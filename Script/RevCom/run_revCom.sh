#!/bin/bash

module load python/3.9.6
source ../venv/bin/activate
python -m  RevCom_script  \
  --data_dir  ../dataset/elasticsearch \
  --train_file train_data-without-elasticsearch.jsonl \
  --test_file test_data-elasticsearch.jsonl \
  --output_dir ../dataset/elasticsearch \
  --repo_name elasticsearch 