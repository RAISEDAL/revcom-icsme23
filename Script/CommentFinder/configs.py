
import logging


logger = logging.getLogger(__name__)


def add_args(parser):
  parser.add_argument("--data_dir", default=None, type=str, required=False,
                      help="The directory name to load data.", )

  parser.add_argument("--train_file", default=None, type=str, required=False,
                      help="The directory name to load train data.", )

  parser.add_argument("--test_file", default=None, type=str, required=False,
                      help="The directory name to load test data.", )

  parser.add_argument("--output_dir", default=None, type=str, required=False,
                      help="The output directory where the output will be written.", )

  parser.add_argument("--repo_name", default=None, type=str, required=False,
                      help="The directory name to load data.", )

  args = parser.parse_args()
  return args
