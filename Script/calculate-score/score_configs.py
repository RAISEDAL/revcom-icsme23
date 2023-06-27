import random
import torch
import logging
import multiprocessing
import numpy as np

logger = logging.getLogger(__name__)


def add_args(parser):
  parser.add_argument("--output_dir", default=None, type=str, required=False,
                      help="The output directory where the output will be written.", )

  parser.add_argument("--repo_name", default=None, type=str, required=False,
                      help="The directory name to load data.", )

  args = parser.parse_args()
  return args
