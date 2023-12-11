import argparse
import os
import string
from difflib import SequenceMatcher
import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from rev_configs import add_args

"""
This script calculates similarity between query and corpus data for RevCom.
RevCom uses three structured items : patch from the diff commit, 
file name, and library from each source file. It recommends review comments 
based on similarity between these structured items.
"""


def tokenizer(token_data: list) -> list:
    return [item.split(" ") for item in token_data]


def get_bm25_similarity(corpus_data, query_data):
    # Tokenize corpus and query data
    corpus_tokens = tokenizer(corpus_data)
    query_tokens = tokenizer(query_data)

    bm25_model = BM25Okapi(corpus_tokens)
    bm25_similarity_table = np.empty((0, len(corpus_tokens)))
    for token in query_tokens:
        query_to_corpus_sim_score = bm25_model.get_scores(token)
        bm25_similarity_table = np.concatenate([bm25_similarity_table, [query_to_corpus_sim_score]],
                                               axis=0)
    return bm25_similarity_table


def sequence_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


class CodeReviewPredictor:

    def __init__(self, args):
        self.args = args
        self.punctuations = string.punctuation.replace("\"", "")
        self.DATA_DIR = args.data_dir

    def data_loader(self):
        corpus_df = pd.read_json(os.path.join(self.DATA_DIR, self.args.train_file), lines=True)
        query_df = pd.read_json(os.path.join(self.DATA_DIR, self.args.test_file), lines=True)
        return corpus_df, query_df

    def get_patch_token(self, patch_list: list) -> list:
        patch_token_list = []
        for patch in patch_list:
            # Translates punctuations by adding spaces around them
            patch_token = patch.translate(
                str.maketrans({key: " {0} ".format(key) for key in self.punctuations}))
            patch_token_list.append(patch_token)
        return patch_token_list

    def get_file_token(self: list) -> list:
        file_token_list = []
        for file_name in self:
            file_name = file_name.split('/')
            file_token = ' '.join(file_name)
            file_token_list.append(file_token)
        return file_token_list

    def write_predictions(self, topk, predictions):
        file_path = os.path.join(self.args.output_dir, f'predictions-{topk}.txt')
        with open(file_path, 'w', encoding='utf-8') as file:
            for comment_list in predictions:
                prediction_string = '\n'.join(' '.join(comment.split()) for comment in comment_list)
                file.write(prediction_string + '\n')

    def get_prediction(self, topk, similarity, corpus_patch_tokens, query_patch_tokens, corpus_review_comments):
        """
        Retrieves predictions based on the top-k similar items for each query.

        Args:
            topk (int): Number of top similar items to consider.
            similarity (np.ndarray): 2D array containing similarity scores between query and corpus data.
            corpus_patch_tokens (list): List of tokenized data in the corpus.
            query_patch_tokens (list): List of tokenized data in the query.
            corpus_review_comments: List of actual review comments in the corpus.

        Returns:
            list: List of predicted comments for each query.
        """
        predicted_comments = []
        for query_index in range(len(similarity)):
            # Get the indices of the top-10 similar corpus for the current query
            top_corpus_index = np.argsort(similarity[query_index])[::-1][:10]

            # Calculate sequence similarity scores between the top-k corpus and current query
            sequence_similarity_table = [
                (corpus_index,
                 sequence_similarity(query_patch_tokens[query_index], corpus_patch_tokens[corpus_index]))
                for corpus_index in top_corpus_index
            ]

            sequence_similarity_table.sort(key=lambda x: x[1], reverse=True)
            top_indices_of_corpus = sequence_similarity_table[:topk]

            # Retrieve review comments corresponding to the top-k corpus items
            review_comments = [corpus_review_comments[index[0]] for index in top_indices_of_corpus]
            predicted_comments.append(review_comments)

        return predicted_comments

    def run_prediction(self):
        corpus_df, query_df = self.data_loader()

        # Extracting the list of patch tokens for query and corpus
        corpus_patch_tokens = self.get_patch_token(corpus_df['patch'].to_list())
        query_patch_tokens = self.get_patch_token(query_df['patch'].to_list())

        # Extracting the list of file tokens for query and corpus
        corpus_file_tokens = self.get_file_token(corpus_df['path'].to_list())
        query_file_tokens = self.get_file_token(query_df['path'].to_list())

        # Extracting the list of library tokens for query and corpus
        corpus_library_tokens = corpus_df['import_tokens'].to_list()
        query_library_tokens = query_df['import_tokens'].to_list()

        # Extracting the list of actual review comments from corpus
        corpus_review_comments = corpus_df['msg']

        patch_similarity = get_bm25_similarity(corpus_patch_tokens, query_patch_tokens)
        file_similarity = get_bm25_similarity(corpus_file_tokens, query_file_tokens)
        library_similarity = get_bm25_similarity(corpus_library_tokens, query_library_tokens)

        patch_file_similarity = np.add(self.args.alpha * patch_similarity, (self.args.beta * file_similarity))
        combined_similarity_table = np.add(patch_file_similarity, (self.args.gamma * library_similarity))

        for topk in self.args.topk_values:
            predicted_comments = self.get_prediction(topk, combined_similarity_table, corpus_patch_tokens,
                                                     query_patch_tokens,
                                                     corpus_review_comments)
            self.write_predictions(topk, predicted_comments)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--alpha', type=float, default=0.5, help='Weight for diff_similarity')
    parser.add_argument('--beta', type=float, default=0.3, help='Weight for file_similarity')
    parser.add_argument('--gamma', type=float, default=0.2, help='Weight for import_similarity')

    args = add_args(parser)

    predictor = CodeReviewPredictor(args)
    predictor.run_prediction()
