from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import os
from difflib import SequenceMatcher
import numpy as np
import string
from configs import add_args
import argparse
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

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def prediction(similarity, test_df, train_df, methods,args):
  src_test_change_token = test_df[methods].to_list()
  src_train_change_token = train_df[methods].to_list()
  topk = 1
  while topk <= 10:
    if topk == 7:
      topk = topk + 3
      continue
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

    with open(args.output_dir + 'preds-' + str(topk) + '.txt', 'w',
              encoding='utf-8') as f:
      for data in prediction:
        for element in data:
          f.write(' '.join(element.split()) + '\n')
    if topk == 10:
      print(f"predicted sequence :{topk}")
      print("Prediction Complete")
      break
    topk = topk + 2

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  args = add_args(parser)

  DATA_DIR=args.data_dir

  train_df = pd.read_csv(os.path.join(DATA_DIR, args.train_file))
  test_df = pd.read_csv(os.path.join(DATA_DIR, args.test_file))

  train_df['methods'] = processDatasetUpdated(train_df['methods'].to_list())
  test_df['methods'] = processDatasetUpdated(test_df['methods'].to_list())

  data_count_vect = CountVectorizer()
  train_data_vect = data_count_vect.fit_transform(train_df['methods'])
  test_data_vect = data_count_vect.transform( test_df['methods'])

  target_train_comment = train_df['msg'].to_list()
  target_test_comment = test_df['msg'].to_list()

  with open(args.output_dir + 'golds.txt', 'w', encoding='utf-8') as f:
    for data in target_test_comment:
      f.write(' '.join(data.split()) + '\n')
   # logger.info(args)

  similarity = cosine_similarity(test_data_vect, train_data_vect)
  prediction(similarity, test_df, train_df, "methods",args)