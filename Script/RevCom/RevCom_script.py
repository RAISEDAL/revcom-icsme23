import argparse
import os
import string
from difflib import SequenceMatcher
import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from rev_configs import add_args
punctuations = string.punctuation.replace("\"", "")


def processDatasetUpdated(data):
  processed_token_list = []
  token_type = []
  for d in data:
    src = d.translate(
      str.maketrans({key: " {0} ".format(key) for key in punctuations}))
    processed_token_list.append(src)
    token_type.append(None)
  return processed_token_list


def get_file_token(file_list):
  files_token = []
  for item in file_list:
    temp = item.split('/')
    token = ' '.join(temp)
    files_token.append(token)
  return files_token


def get_bm25_similarity(train_df, test_df, column_name):
  src_train_change = train_df[column_name].to_list()
  src_train_change = [item.split(" ") for item in src_train_change]
  src_test_change = test_df[column_name].to_list()
  src_test_change = [item.split(" ") for item in src_test_change]

  bm25 = BM25Okapi(src_train_change)
  all_similarity = np.empty((0, len(src_train_change)))
  for item in src_test_change:
    test_to_train_sim_score = bm25.get_scores(item)
    all_similarity = np.concatenate([all_similarity, [test_to_train_sim_score]],
                                    axis=0)
  return all_similarity


def similar(a, b):
  return SequenceMatcher(None, a, b).ratio()


def prediction(topk, similarity, test_df, train_df, diff_comment_token,args):
  src_test_change_token = test_df[diff_comment_token].to_list()
  src_train_change_token = train_df[diff_comment_token].to_list()

  prediction = []
  for index in range(len(similarity)):
    index_nn = np.argsort(similarity[index])[::-1][:10]
    similar_nn = []
    for idx in index_nn:
      similar_sequence_score = similar(src_test_change_token[index],
                                       src_train_change_token[idx])
      similar_nn.append((idx, similar_sequence_score))
    similar_nn.sort(key=lambda x: x[1], reverse=True)
    similar_topk = similar_nn[:topk]
    current_prediction = []
    for element in similar_topk:
      current_prediction.append(target_train_comment[element[0]])
    prediction.append(current_prediction)

  with open(os.path.join(args.output_dir , 'preds-' + str(topk) + '.txt'), 'w',
            encoding='utf-8') as f:
    for data in prediction:
      for element in data:
        f.write(' '.join(element.split()) + '\n')



if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  args = add_args(parser)

  DATA_DIR=args.data_dir
  train_df = pd.read_json(os.path.join(DATA_DIR, args.train_file),lines=True)
  test_df = pd.read_json(os.path.join(DATA_DIR, args.test_file),lines=True)
  train_df['patch_token'] = processDatasetUpdated(train_df['patch'].to_list())
  test_df['patch_token'] = processDatasetUpdated(test_df['patch'].to_list())

  train_df['path_token'] = get_file_token(train_df['path'].to_list())
  test_df['path_token'] = get_file_token(test_df['path'].to_list())

  target_train_comment = train_df['msg'].to_list()
  target_test_comment = test_df['msg'].to_list()
  with open(os.path.join(args.output_dir,'golds.txt'), 'w', encoding='utf-8') as f:
    for data in target_test_comment:
      f.write(' '.join(data.split()) + '\n')
  print("file written sucessfully")
  # logger.info(args)
  diff_similarity = get_bm25_similarity(train_df, test_df, "patch_token")
  file_similarity = get_bm25_similarity(train_df, test_df, 'path_token')
  import_similarity = get_bm25_similarity(train_df, test_df, "import_tokens")

  alpha = 0.5
  beta = 0.3
  gama = 0.2

  diff_file_similarity = np.add(alpha*diff_similarity, (beta * file_similarity))
  similarity = np.add(diff_file_similarity, (gama * import_similarity))

  prediction(1, similarity, test_df, train_df, "patch_token",args)
  prediction(3, similarity, test_df, train_df, "patch_token",args)
  prediction(5, similarity, test_df, train_df, "patch_token",args)
  prediction(10, similarity, test_df, train_df, "patch_token",args)


