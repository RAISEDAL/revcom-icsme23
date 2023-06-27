
import os
import statistics
import string
from datetime import timedelta
from timeit import default_timer as timer
import pandas as pd
from nltk.translate import bleu_score
from rank_bm25 import BM25Okapi
import numpy as np
punctuations = string.punctuation.replace("\"", "")

def get_bm25_similarity(train_df,test_df,column_name):
  src_train_change = train_df[column_name].to_list()
  src_train_change= [item.split(" ") for item in src_train_change]
  src_test_change = test_df[column_name].to_list()
  src_test_change = [item.split(" ") for item in src_test_change]

  bm25 = BM25Okapi(src_train_change)
  all_similarity = np.empty((0, len(src_train_change)))
  for item in src_test_change:
    test_to_train_sim_score=bm25.get_scores(item)
    all_similarity = np.concatenate([all_similarity, [test_to_train_sim_score]], axis=0)
  return all_similarity

from difflib import SequenceMatcher

def similar(a, b):
  return SequenceMatcher(None, a, b).ratio()

def prediction(topk,similarity,test_df,train_df,diff_comment_token,diff_token_type,diff_file_name,diff_token_import,alpha,beta,gama,delta,info_type):

  src_test_change_token=test_df[diff_comment_token].to_list()
  src_train_change_token=train_df[diff_comment_token].to_list()

  prediction=[]
  for index in range(len(similarity)):
    index_nn = np.argsort(similarity[index])[::-1][:10]
    similar_nn = []
    for idx in index_nn:
      similar_sequence_score=similar(src_test_change_token[index],src_train_change_token[idx])
      similar_nn.append((idx, similar_sequence_score))
    similar_nn.sort(key=lambda x: x[1], reverse=True)
    similar_topk = similar_nn[:topk]
    current_prediction = []
    for element in similar_topk:
      current_prediction.append(target_train_comment[element[0]])
    prediction.append(current_prediction)

  with open(OUTPUT_DIR +repo_name+'-'+info_type+'-our_predictions_'+ str(topk) + '.txt', 'w',encoding='utf-8') as f:
    for data in prediction:
      for element in data:
        f.write(' '.join(element.split()) + '\n')


def proposed_approach_evaluation(OUTPUT_DIR,repo_name,info_type):
  chencherry = bleu_score.SmoothingFunction()
  for k in [1,3,5,10]:
    print('k candidates: ', k)
    path_targets = OUTPUT_DIR +repo_name+'-'+info_type+'-target.txt'
    path_predictions = OUTPUT_DIR +repo_name+'-'+info_type+'-our_predictions_' + str(k) + '.txt'

    tgt = [line.strip() for line in open(path_targets,encoding='utf-8')]
    pred = [line.strip() for line in open(path_predictions,encoding='utf-8')]

    count_perfect = 0
    BLEUscore = []
    for i in tqdm(range(len(tgt))):
      best_BLEU = 0
      target = tgt[i]
      for prediction in pred[i * k:i * k + k]:
        if " ".join(prediction.split()) == " ".join(target.split()):
          count_perfect += 1
          best_BLEU = bleu_score.sentence_bleu([target], prediction,
                                               smoothing_function=chencherry.method1)
          break
        current_BLEU = bleu_score.sentence_bleu([target], prediction,
                                                smoothing_function=chencherry.method1)
        if current_BLEU > best_BLEU:
          best_BLEU = current_BLEU
      BLEUscore.append(best_BLEU)

    print(f'{repo_name}\n PP    : %d/%d (%s%.2f)' % ( count_perfect, len(tgt), '%', (count_perfect * 100) / len(tgt)))
    print(f'{repo_name} BLEU mean              : ', statistics.mean(BLEUscore))
  return statistics.mean(BLEUscore)

def processDatasetUpdated(data,datatype):
  processed_token_list=[]
  token_type=[]
  for d in data:
    src=d.translate(str.maketrans({key: " {0} ".format(key) for key in punctuations}))
    processed_token_list.append(src)
    token_type.append(None)
  return processed_token_list,token_type

def get_file_token(file_list):
  files_token = []
  for item in file_list:
    temp = item.split('/')
    token = ' '.join(temp)
    files_token.append(token)
  return files_token

if __name__=='__main__':
  DATA_DIR = "Data Directory path"
  OUTPUT_DIR="Output Directory Path"
  repo_names = ["spring-boot","elasticsearch","RxJava","kafka"]
  start = timer()
  for repo_name in repo_names:

    train_df = pd.read_csv(os.path.join(DATA_DIR,"scrap-github",repo_name+"-train-data.csv"))
    test_df = pd.read_csv(os.path.join(DATA_DIR,"scrap-github",repo_name+"-test-non-duplicates.csv"))

    train_df['diff_comment_token'], train_df['diff_token_type'] = processDatasetUpdated(train_df['diff_hunk'].to_list(), "diff") # For methods as input
    test_df['diff_comment_token'], test_df['diff_token_type'] = processDatasetUpdated(test_df['diff_hunk'].to_list(), "diff")

    train_df = train_df[train_df['tokens'].notna()]
    test_df = test_df[test_df['tokens'].notna()]

    train_df['path_token']=get_file_token(train_df['path'].to_list())
    test_df['path_token'] = get_file_token(test_df['path'].to_list())

    diff_comment_token = 'diff_comment_token'
    diff_file_name = "path_token"
    diff_token_import = 'tokens'

    #Initial Parameter values
    alpha=0.5
    beta=0.2
    gama=0.2
    delta=1
    step=0.2
    minimum=0.5
    maximum=6
    info_type='revcom-non-duplicates'

    # Target Comment List
    target_train_comment = train_df['comment_text'].to_list()
    target_test_comment = test_df['comment_text'].to_list()

    with open(OUTPUT_DIR + repo_name + '-' + info_type + '-target.txt',
              'w', encoding='utf-8') as f:
      for data in target_test_comment:
        f.write(' '.join(data.split()) + '\n')

    #Diff similarity calculation
    diff_similarity = get_bm25_similarity(train_df, test_df, diff_comment_token)
    file_similarity = get_bm25_similarity(train_df, test_df, diff_file_name)
    import_similarity = get_bm25_similarity(train_df, test_df,diff_token_import)

    diff_file_similarity=np.add(diff_similarity,(beta*file_similarity))
    similarity=np.add(diff_file_similarity,(alpha*import_similarity))


    #Initial fitness value calculation
    end = timer()
    print(timedelta(seconds=end-start))
    prediction(1,diff_similarity,test_df,train_df,diff_comment_token,diff_file_name,diff_token_import,alpha,beta,gama,delta,info_type)
    prediction(3,diff_similarity,test_df,train_df,diff_comment_token,diff_file_name,diff_token_import,alpha,beta,gama,delta,info_type)
    prediction(5,diff_similarity,test_df,train_df,diff_comment_token,diff_file_name,diff_token_import,alpha,beta,gama,delta,info_type)
    prediction(10,diff_similarity,test_df,train_df,diff_comment_token,diff_file_name,diff_token_import,alpha,beta,gama,delta,info_type)

    fitness_value_best=proposed_approach_evaluation(OUTPUT_DIR,repo_name,info_type)

    while True:
      fit_value_iter = []
      up_diff_file_similarity = np.add(((alpha+step) if (alpha+step)<maximum else maximum * diff_similarity),((beta+step) if (beta+step)<maximum else maximum * file_similarity))
      up_similarity = np.add(diff_file_similarity, ((gama+step) if (gama+step)<maximum else maximum * import_similarity))

      down_diff_type_similarity = np.add(((alpha-step) if (alpha-step)<minimum else minimum * diff_similarity),((beta-step) if (beta-step)<minimum else minimum * file_similarity))
      down_similarity = np.add(diff_file_similarity, ((gama-step) if (gama-step)<minimum else minimum * import_similarity))

      prediction(1, up_similarity, test_df, train_df, diff_comment_token, diff_file_name, diff_token_import,(alpha+step) if (alpha+step)<maximum else maximum, beta,gama,delta)
      fit_value_iter.append(proposed_approach_evaluation(repo_name, diff_comment_token))
      prediction(1, down_similarity, test_df, train_df, diff_comment_token, diff_file_name, diff_token_import,(alpha-step) if (alpha-step)<minimum else minimum, beta,gama,delta)
      fit_value_iter.append(proposed_approach_evaluation(repo_name, diff_comment_token))

      prediction(1, up_similarity, test_df, train_df, diff_comment_token, diff_file_name, diff_token_import,alpha,(beta+step) if (beta+step)<maximum else maximum,gama,delta)
      fit_value_iter.append(proposed_approach_evaluation(repo_name, diff_comment_token))
      prediction(1, down_similarity, test_df, train_df, diff_comment_token, diff_file_name, diff_token_import,alpha,(beta-step) if (beta-step)<minimum else minimum,gama,delta)
      fit_value_iter.append(proposed_approach_evaluation(repo_name, diff_comment_token))

      prediction(1, up_similarity, test_df, train_df, diff_comment_token, diff_file_name, diff_token_import,alpha,beta,(gama+step) if (gama+step)<maximum else maximum,delta)
      fit_value_iter.append(proposed_approach_evaluation(repo_name, diff_comment_token))
      prediction(1, down_similarity, test_df, train_df, diff_comment_token, diff_file_name, diff_token_import,alpha,beta,(gama-step) if (gama-step)<minimum else minimum,delta)
      fit_value_iter.append(proposed_approach_evaluation(repo_name, diff_comment_token))

      prediction(1, up_similarity, test_df, train_df, diff_comment_token, diff_file_name, diff_token_import,alpha,beta,gama,(delta+step) if (delta+step)<maximum else maximum)
      fit_value_iter.append(proposed_approach_evaluation(repo_name, diff_comment_token))
      prediction(1, down_similarity, test_df, train_df, diff_comment_token, diff_file_name, diff_token_import,alpha,beta,gama,(delta-step) if (delta-step)<minimum else minimum)
      fit_value_iter.append(proposed_approach_evaluation(repo_name, diff_comment_token))

      best_fitness_iter=max(fit_value_iter)
      best_fitness_index=fit_value_iter.index(best_fitness_iter)
      if best_fitness_iter>=fitness_value_best:
        print(f"previous fitness: {fitness_value_best}  Best fitness: {best_fitness_iter} ")
        fitness_value_best=best_fitness_iter
        if best_fitness_index==0:
          alpha=alpha+step
          beta=beta
          gama=gama
          print(f"alpha: {alpha}   Beta: {beta}  Gama: {gama}")
        elif best_fitness_index==1:
          alpha=alpha-step
          beta=beta
          gama=gama
          print(f"alpha: {alpha}   Beta: {beta}  Gama: {gama} ")
        elif best_fitness_index==2:
          alpha=alpha
          beta=beta+step
          gama=gama
          print(f"alpha: {alpha}   Beta: {beta}  Gama: {gama} ")
        elif best_fitness_index==3:
          alpha=alpha
          beta=beta-step
          gama=gama
          print(f"alpha: {alpha}   Beta: {beta}  Gama: {gama} ")
        elif best_fitness_index==4:
          alpha=alpha
          beta=beta
          gama=gama+step
          print(f"alpha: {alpha}   Beta: {beta}  Gama: {gama} ")
        elif best_fitness_index==5:
          alpha=alpha
          beta=beta
          gama=gama-step
          print(f"alpha: {alpha}   Beta: {beta}  Gama: {gama} ")


        with open(OUTPUT_DIR + repo_name + '-' +'parameter-tuning.txt', 'a',encoding='utf-8') as f1:
            f1.write(f"previous fitness: {fitness_value_best}  Best fitness: {best_fitness_iter} \nalpha: {alpha}   Beta: {beta}  Gama: {gama} "+'\n')
        f1.close()
      else:
        print(f"current fitness: {fitness_value_best}  Best fitness: {best_fitness_iter} ")
        print(f"alpha: {alpha}   Beta: {beta}  Gama: {gama}")
        with open(OUTPUT_DIR + repo_name + '-' +'parameter-tuning.txt', 'a',encoding='utf-8') as f1:
            f1.write(f"previous fitness: {fitness_value_best}  Best fitness: {best_fitness_iter} \nalpha: {alpha}   Beta: {beta}  Gama: {gama}  End of iteration"+'\n')
        f1.close()
        break





