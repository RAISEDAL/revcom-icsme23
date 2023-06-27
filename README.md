# Replication Package of RevCom

## Recommending Code Reviews Leveraging Code Changes with Structured Information Retrieval
#### Accepted Paper at ICSME 2023

## Abstract
Review comments are one of the main building blocks of modern code reviews.  Manually writing code review comments 
could be time-consuming and technically challenging. Recently, an information retrieval (IR) based approach has been 
proposed to automatically recommend relevant code review comments for method-level code changes. However, this technique overlooks the structured items
(e.g., class name, library information) from the source code and is applicable only for method-level changes.
In this paper, we propose a novel technique for relevant review comments recommendation -- RevCom -- that leverages various code-level changes using structured information retrieval.
RevCom uses different structured items from source code and can recommend relevant reviews for all types of changes (e.g., method-level and non-method-level). 
Our evaluation using three performance metrics show that RevCom outperforms both IR-based and DL-based baselines by up to 49.45% and 23.57% margins in BLEU score in recommending review comments.
We find that RevCom can recommend review comments with an average BLEU score of 26.63%.
According to Google's AutoML Translation documentation, such a BLEU score indicates that the review comments can capture the original intent of the reviewers.
All these findings suggest that RevCom can recommend relevant code reviews and has the potential to reduce the cognitive effort of human code reviewers.
## Download Dataset, Model Checkpoints and Generated Predictions

To replicate our experiment, please download the necessary materials following the below steps.
* `Baselines.zip` contains our fine-tuned model for the baseline techniques and generated prediction. Please download `Baselines.zip` from [here](https://drive.google.com/file/d/1Gs2mmihe9WH1t43PU6Oj3quTidWL4HX9/view?usp=sharing). Extract the downloaded directory and replace the `Baselines` directory of this repository with the extracted directory.
* `Dataset.zip` contains our dataset for this experiment. Please download `Dataset.zip` from [here](https://drive.google.com/file/d/15kq7LqvfY-oP1M1UDdK_lLmUfq71daVR/view?usp=sharing). Extract the downloaded directory and replace the `Dataset` directory of this repository with the extracted directory.

## File Structure

* `Baselines` : contains two subdirectories `CodeReviewer` and `CommentFinder`
    * subdirectory `CodeReviewer` has  sub-subdirectory `project-wise` and `cross-project` which containes the finetuned models and generated prediction by this technique. 
    * subdirectory `CommentFinder` has  sub-subdirectory `project-wise` and `cross-project` which containes the generated prediction by this technique.
* `Dataset` : contains the data files
* `Results` : contains the generated prediction for RevCom. It has subdirectory `project-wise` and `cross-project`. 
            These two subdirectories contains the generated output for both within project and cross-project for RevCom
* `Script` : contains four subdirectories -- `calculate-score`, `CommentFinder`, `RevCom`, `scrap-github`, and `utilities`
    * subdirectory `calculate-score` contains python script to calculate the score for each techniques using the gold review comments and recommended review comment
    * subdirectory `CommentFinder` contains python script for the baseline technique CommentFinder. The details of this approach can be find in the original study- [CommentFinder](https://github.com/CommentFinder/CommentFinder) 
    * subdirectory `RevCom` contains python script of our Proposed technique RevCom
    * subdirectory `scrap-github` contains python script to scrap the data from GitHub
    * subdirectory `utilities` contains python script for data preparation and weight tuning
   
## Replicate

In the following sections, we describe how to replicate the result for RevCom and baseline techniques

## Prerequisites
---
We recommend using a virtual environment to install the packages and run the application.
    
In order to calculate the semantic similarity scores, a CUDA supported GPU with at least 16 GB memory is recommended.
In plain words, any NVIDIA GPU is CUDA supported. It also requires to install torch in your system.

**Installation**

Make sure you have python 3.9, CUDA 11.3 and the latest pip installed on your machine. Then, to install pytorch, run

    pip install torch==1.10.0+cu113 torchvision==0.11.0+cu113 torchaudio==0.10.0+cu113 torchtext==0.11.0 -f https://download.pytorch.org/whl/cu113/torch_stable.html
    
Once pytorch is installed, install the remaining packages by running

    pip install -r requirements.txt
    
  **Calculate the score**
  
  To replicate the first experiment of RQ1 (i.e., Performance of RevCom) follow the below instruction
  
  * Navigate to the `Script/calculate-score` directory and run `compute_score.sh` file
  * `compute_score.sh` script takes two parameters one is `--output_dir` and another is `--repo_name` 
  * pass the value for `--output directory` in the following format-- `./Results/project-wise/<repo-name>`
  * pass the value for `--repo_name` in the following format `./<repo-name>`
  
 This will produce the reported result for our RQ1.
 
To replicate the score for the baseline techniques follow the same instruction above. However, only change the value for `output directory` in `compute_score.sh` file.
* pass the value for `--output directory` in the following format-- `./Baselines/<technique name>/cross-project/<repo-name>`
This will produce the reported result for the baseline techniques in RQ4.
    
**Run RevCom for generating prediction from scratch**
* Navigate to the `Script/utilities` directory and run `prepare-data.py` python file to format data for our technique
* Then navigate to the `Script/RevCom` directory and run `run_revCom.sh` bash file
* `run_revCom.sh` script takes the following parameters
* `--data_dir` < directory of the dataset > that you prepared for RevCom
* `--train_file` < file name of your train or corpus dataset >
* `--test_file` < file name of your test or query dataset >
* `--output_dir` < directory where you want ot save the output >
* `--repo_name` < repository name for which you want to run RevCom >
This will generate the prediction by using our technique for the Given data.

**Run baseline for generating prediction from scratch**
* Navigate to the `Script/utilities` directory and run `prepare-data.py` python file to format data for our CodeReviewer
* The finetuned model of CodeReviewer can be found in the following directory-- `./Baselines/CodeReviewer/cross-project/<repo-name>/checkpoints-last`
* To generate prediction, Use our finetuned model and follow the instruction from original replication package of [CodeReviewer](https://github.com/microsoft/CodeBERT/tree/master/CodeReviewer)
* Navigate to the `Script/utilities` directory and run `prepare-data.py` python file to format data for our CommentFinder
* To generate the prediction for CommentFinder, you can use the script given in the following directory `Script/CommentFinder` or follow the instruction from the original replication package of [CommentFinder](https://github.com/CommentFinder/CommentFinder) 
---
# Licensing Information
[![License](https://i.creativecommons.org/l/by-nc-sa/1.0/88x31.png)](https://creativecommons.org/publicdomain/zero/1.0/)
<br/>
This work is licensed under a [Creative Commons CC0 1.0 Universal (CC0 1.0)
Public Domain Dedication License](https://creativecommons.org/publicdomain/zero/1.0/).

---

> Something not working as expected? Create an issue [here](https://github.com/RAISEDAL/revcom-icsme23/issues).



