
import torch
from sentence_transformers import SentenceTransformer
from nltk.translate import bleu_score
import os
import statistics
from torch.nn.functional import cosine_similarity
import argparse
import multiprocessing
from score_configs import add_args

model = SentenceTransformer('stsb-roberta-large', device='cuda')

# logging.basicConfig(
#     format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
#     datefmt="%m/%d/%Y %H:%M:%S",
#     level=logging.INFO,
# )
# logger = logging.getLogger(__name__)

def proposed_approach_evaluation(OUTPUT_DIR,repo_name):
  chencherry = bleu_score.SmoothingFunction()
  print("calculation started")
  for k in [1,3,5,10]:
    print('k candidates: ', k)
    path_targets = os.path.join(OUTPUT_DIR,'golds.txt')
    path_predictions = os.path.join(OUTPUT_DIR,f'preds-{str(k)}.txt')

    tgt = [line.strip() for line in open(path_targets,encoding='utf-8')]
    pred = [line.strip() for line in open(path_predictions,encoding='utf-8')]

    count_perfect = 0
    BLEUscore = []
    cosine_score_list=[]
    for i in (range(len(tgt))):
      best_BLEU = 0
      best_ss=0
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

        gold_embed=torch.tensor(model.encode(target))
        target_embed=torch.tensor(model.encode(prediction))
        current_ss=cosine_similarity(gold_embed,target_embed,dim=0)
        if current_ss>best_ss:
          best_ss=current_ss
      BLEUscore.append(best_BLEU)
      cosine_score_list.append(best_ss)

    print(f'{repo_name}\n PP    : %d/%d (%s%.2f)' % ( count_perfect, len(tgt), '%', (count_perfect * 100) / len(tgt)))
    print(f'{repo_name} BLEU mean              : ', statistics.mean(BLEUscore))
    print(f'{repo_name} Semantic Similarity              : ', sum(cosine_score_list)/len(tgt))

def main(args):
  OUTPUT_DIR=args.output_dir
  repo_name=args.repo_name
  proposed_approach_evaluation(OUTPUT_DIR,repo_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = add_args(parser)
    args.cpu_count = multiprocessing.cpu_count()
    #logger.info(args)
    main(args)
    print("Calculation finished.")