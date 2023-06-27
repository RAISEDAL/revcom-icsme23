#!/bin/bash

#SBATCH --account=def-mrdal22
#SBATCH --time=02:00:00
#SBATCH --mem=128G
#SBATCH --output=../ComFind/ComFind-logs/slurm-%x-%j.out
#SBATCH --mail-user=oh599627@dal.ca
#SBATCH --mail-type=ALL

module load python/3.9.6
source ../venv/bin/activate
python -m  ComFind_script  \
  --data_dir  ../dataset/ComFindData/cross-project \
  --train_file youtube-dl-train_without_ComFind.csv \
  --test_file youtube-dl-test_ComFind.csv \
  --output_dir ./youtube/cross-project/ \
  --repo_name youtube-dl