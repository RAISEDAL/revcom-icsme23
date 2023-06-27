#!/bin/bash

module load python/3.9.6
source ./venv/bin/activate
python -m  compute_score_script  \
  --output_dir ./RevCom/kafka/cross-project \
  --repo_name ./kafka