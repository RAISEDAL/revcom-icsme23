import configparser
import os
import re
import subprocess
import time
from collections import namedtuple

import pandas as pd
import requests

Import = namedtuple("Import", ["module", "name", "alias"])

def get_rate_limited_response(path: str, token=None):
  token_list = _get_token_list()
  for i in range(len(token_list)):
    token = token_list[i]
    _headers = {'Authorization': f'Bearer {token}'}
    try:
      response_obj = requests.get(path, headers=_headers)
    except:
      print("Check Response error:" + path)
      response = []
      return response
    if response_obj.status_code == 502 or response_obj.status_code == 500:
      time.sleep(120)
      return []
    limit_remaining = int(response_obj.headers['x-ratelimit-remaining'])
    if limit_remaining >= 1:
      break
    else:
      continue
  response = response_obj.json()
  print('token limit: ' + str(limit_remaining))
  return response

def _get_token_list():
  config = configparser.RawConfigParser()
  path = "C:\\Users\wahid\PycharmProjects\RevCom\scrap_github\\"
  config.read(path + '\\github-token.cfg')
  details_dict = dict(config.items('DEFAULT'))
  tokens = list(details_dict.values())
  return tokens


def merge_dataset(repo_name):
  if not os.path.exists(os.path.join(DATA_DIR,repo_name,repo_name)):
    os.mkdir(os.path.join(DATA_DIR,repo_name,repo_name))

  file_list=os.listdir(os.path.join(DATA_DIR,repo_name))
  df=pd.DataFrame()
  for i in range(1,len(file_list)):
    temp_df=pd.read_csv(os.path.join(DATA_DIR,repo_name,file_list[i]))
    if len(temp_df)<100:
      print(file_list[i])
    df=df.append(temp_df)
  #print(df.duplicated().sum())
  df=df.drop_duplicates()
  #print(df.duplicated().sum())
  print("Data Merged Successfully")
  df.to_csv(os.path.join(DATA_DIR,repo_name,repo_name,repo_name+".csv"),index=False)
  print(f"{repo_name}.csv written successfully and size is {len(df)}")

'''
This function is for discarding the review comments which are written by the pr author
in response to the reviewer
'''
def remove_author_comments(repo_name):
  df_pr=pd.read_csv(os.path.join(DATA_DIR,repo_name,repo_name,repo_name+"-with-pr-info.csv"))
  df_author = pd.read_csv(os.path.join(DATA_DIR, repo_name, repo_name,
                                   repo_name + "_author_list.csv"))
  prs=df_author['pr_number'].to_list()
  authors=df_author['author_name'].to_list()
  pr_author_map=dict(zip(prs,authors))
  df_review_comments=df_pr.copy()
  for index,row in df_pr.iterrows():
    #print(row['comment_author'])
    #print(pr_author_map[row["pr_number"]])
    if isinstance(row['comment_author'],float):
      df_review_comments = df_review_comments.drop(index)
    elif row['comment_author'].strip()==pr_author_map[row["pr_number"]]:
      df_review_comments=df_review_comments.drop(index)
      # print(f"Author Comment: {row['author_name']} and Pr: {row['pr_number']}")
  df_review_comments.to_csv(os.path.join(DATA_DIR,repo_name,repo_name,repo_name+"-review-comment.csv"),index=False)
  print(f"{repo_name}-review-comment.csv has written successfully")

'''
this function is for getting the pr-author list
'''
def get_pr_author(repo,repo_name):
  df=pd.read_csv(DATA_DIR+repo_name+"\\"+repo_name+"\\"+repo_name+".csv")
  pr_numbers=[]
  comment_authors=[]
  for index,row in df.iterrows():
    pr_url=row['pull_request_url'].split("/")
    pr_number=pr_url[len(pr_url)-1]
    pr_numbers.append(int(pr_number))
    try:
      comment_author=row['user'].split(',')[0].split(":")[1].replace("\'","")
    except:
      #print("NAN Value")
      comment_author=None
    comment_authors.append(comment_author)
  df['comment_author']=comment_authors
  df['pr_number']=pr_numbers
  df=df.sort_values(by=['pr_number'])
  df.to_csv(os.path.join(DATA_DIR,repo_name,repo_name,repo_name+"-with-pr-info.csv"),index=False)
  unique_prs=list(set(pr_numbers))
  author_list=[]
  prs=[]
  from itertools import count
  pr_index=0
  existing_author_df=pd.DataFrame(columns=["pr_number","author_name"])
  existing_author_df.to_csv(DATA_DIR+repo_name+"\\"+repo_name+"_author_list.csv",index=False)
  existing_author_df=pd.read_csv(DATA_DIR+repo_name+"\\"+repo_name+"_author_list.csv")
  prs=existing_author_df['pr_number'].to_list()
  author_list=existing_author_df['author_name'].to_list()
  for i in count(1):
    if unique_prs[pr_index] in prs:
      pr_index=pr_index+1
      continue
    query="https://api.github.com/repos/"+repo+"/"+repo_name+"/pulls/"+str(unique_prs[pr_index])
    response=get_rate_limited_response(query,'')
    if len(response)<=2:
     continue
    author_list.append(response['user']['login'])
    prs.append(response['number'])
    pr_index = pr_index + 1
    if pr_index==len(unique_prs):
      break

  pr_author_map=pd.DataFrame()
  pr_author_map['pr_number']=prs
  pr_author_map['author_name']=author_list
  pr_author_map.to_csv(DATA_DIR+repo_name+"\\"+repo_name+"\\"+repo_name+"_author_list.csv",index=False)
  print("File Written Successfully")

'''
These function is for discarding the irrelevent comments
'''


stop_words = ["a", "an", "the", "this", "that", "is", "it", "to", "and"]
def removeStopwords(text):
  text=text.lower()
  text = ''.join(
    w + ' ' for w in text.split() if w.upper() not in stop_words).strip()

  if text.endswith(("?", "!", ".")):
    text = text[:-1]

  if text.startswith(('-', '.', ':', '>')):
    text = text[1:].strip()

  return text

def is_comment_relevant(comment):
  comment = comment.lower()
  size = len(comment.split())

  if size == 0:
    return False

  if len(removeStopwords(comment)) == 0:
    return False

  if comment == ":+1:" or comment == "+1" or comment == "\+" or comment == ":100:" or comment == "..." or comment == "!!!" or comment == "==>" or comment == "++" or comment == "??" or comment == "-;" or comment == "... :)" or comment == "+" or comment == ";)" or comment == ":0" or comment == ":-)" or comment == ":0" or comment == ";-)" or comment == ":(" or comment == ":-(" or comment == "?!" or comment == "^^" or comment == "^^^" or comment == "???" or comment == ":/" or comment == "+:100:" or comment == "????" or comment == "..?" or comment == ":-|" or comment == "...?" or comment == "??????" or comment == ":)" or comment == "^":
    return False

  # Useless comments, one word, no action required or unclear action
  if size == 1:
    return False
    # if "update" in comment or "done" in comment or "indeed" in comment or "idem" in comment or "doc" in comment or"lgtm" in comment or "docs" in comment or "ok" in comment or "nice" in comment or "pleas" in comment or "ditto" in comment or "thank" in comment or "lol" in comment or "fine" in comment or "agre" in comment or "dito" in comment or "yeh" in comment or "cool" in comment or "same" in comment or "ack" in comment or "hahaha" in comment:
    #   return False

  if size == 2:
    return False
    # if "remove" in comment or"ack" in comment or "same change" in comment or "this too" in comment or "java doc" in comment or "good catch" in comment or "and this" in comment:
    #   return False
  # as above, see above, ditto above, same above,
  # same here, and here, also here, here too, ditto here, here..., likewise here.
  if size <= 3:
    if "as before" in comment or "done" in comment or "Ok added this".lower() in comment or "nice" in comment or "here" in comment or "above" in comment:
      return False;

  # Request to change formatting, no impact on code
  if "indent" in comment and size < 5:
    return False

  # Likely a thankyou message
  if (
    "works for me" in comment or "sounds good" in comment or "makes sense" in comment or "smile" in comment or "approve" in comment or "Oh yes I understand actually" in comment or "To be confirmed with".lower() in comment or "That's very clean".lower() in comment or "yeah i kind of agree" in comment) and size <= 5:
    return False
  if '?' in comment.split()[-1]:
    return False
  if "love" in comment or "satisfying" in comment or "reasonable" in comment or "agree" in comment or "nice addition" in comment and len(comment)<=5:
    return False
  # Request to add test code, no impact on the reviewed code
  if ("test" in comment and size < 5) or (
    "add" in comment and "test" in comment):
    return False

  # Request for clarification
  if ((
        "please explain" in comment or "what" in comment or "wat" in comment or "explain" in comment) and size < 5) or (
    "not sure" in comment and ("understand" in comment or "meant" in comment)):
    return False

  # Refers to previous comment or external resource with unclear action point
  if (
    "same as" in comment or "same remark" in comment or "said above" in comment or "do the same" in comment) and size < 5:
    return False

  if ("like" in comment or "see" in comment) and (
    "http" in comment or "https" in comment or "<link_" in comment):
    return False

  # Request to add comment
  if "document" in comment or "javadoc" in comment or "comment" in comment:
    return False
  if "should remove this line" in comment and len(comment)==4:
    return False

  # Feedback about reorganizing the PR
  if "pr" in comment and size < 5:
    return False

  # Comment contains a +1 to support previous comment.
  # It may be accompanied by another word, like agree or a smile.
  # This is the reason for < 3
  if "+1" in comment and size < 3:
    return False

  # The code is ok for now
  if "for now" in comment and size < 5:
    return False

  # Answers
  if (
    "fixed" in comment or "thank" in comment or "youre right" in comment) and size < 3:
    return False

  return True


def remove_irrelevent_comments(repo_name):
  df = pd.read_csv(os.path.join(DATA_DIR, repo_name, repo_name,
                                   repo_name + "-review-comment.csv"),encoding='latin-1')
  updated_df=df.copy()
  for index,row in df.iterrows():
    if is_comment_relevant(row['comment_text']):
      continue
    else:
      updated_df=updated_df.drop(index)
  updated_df.to_csv(os.path.join(DATA_DIR, repo_name, repo_name,
                                   repo_name + "-review-comment-final.csv"),index=False)
  print(f"File {repo_name} writtten successfully")

def build_comment_file_map_updated(repo_name,repo_directory):
  comment_df = pd.read_csv(os.path.join(DATA_DIR, repo_name, repo_name,repo_name + "-review-comment-final.csv"))
  new_df = pd.DataFrame()
  comment_id = []
  comment_diff = []
  comment_text = []
  comment_source_file = []
  cfile_path = []
  comment_author=[]
  for index,row in comment_df.iterrows():
    path=row['path']
    if path.endswith('.py'):
      command=f"git show {row['original_commit_id']}:{path}"
      run = subprocess.run(command,cwd=repo_directory,capture_output=True,encoding='utf-8')
      if len(run.stdout)<2:
        continue
      comment_id.append(str(int(row['comment_id']))+"-"+str(row['pr_number']))
      comment_diff.append(row['diff_hunk'])
      comment_text.append(row['comment_text'])
      # comment_source_file.append(run.stdout)
      cfile_path.append(row['path'])
      comment_author.append(row['comment_author'])
  new_df['comment_id'] = comment_id
  new_df['diff_hunk'] = comment_diff
  new_df['comment_text'] = comment_text
  #new_df['change'] = comment_source_file
  new_df['path'] = cfile_path
  new_df['comment_author']=comment_author
  print(len(new_df))
  # temp=new_df.sample(373,random_state=42)
  new_df.to_csv(os.path.join(DATA_DIR, repo_name, repo_name,repo_name + "-review-comment-final-sample-for-EMSE.csv"),index=False)
  print(f"{repo_name} written successfully")


def build_comment_file_map(repo_name):
  file_list=os.listdir(os.path.join(DATA_DIR,repo_name,repo_name,"change-file-old"))
  comment_df=pd.read_csv(os.path.join(DATA_DIR,repo_name,repo_name,repo_name+"-review-comment-final.csv"))
  change_file_list=[]
  for index,row in comment_df.iterrows():
    path=row['path'].split(".")[0].replace('/','-')
    #if row['commit_id']+"-"+path+".csv" in file_list:
    if path+".csv" in file_list:
     # path_df=pd.read_csv(os.path.join(DATA_DIR,repo_name,repo_name,"change-file-old",row['commit_id']+"-"+path+".csv"))
      path_df=pd.read_csv(os.path.join(DATA_DIR,repo_name,repo_name,"change-file-old",path+".csv"))
      change_file_list.append(path_df['contents'].item())
    else:
      change_file_list.append(None)
  comment_df["change"]=change_file_list
  comment_df.to_csv(os.path.join(DATA_DIR,repo_name,repo_name,repo_name+"-review-comment-final.csv"),index=False)
  print(f'{repo_name} written successfully')


def comment_file_import_map(repo_name,filType):
  # pattern = "'*|\[*|\]*"
  comment_df = pd.read_csv(os.path.join(DATA_DIR, repo_name, repo_name,
                                        repo_name + "-review-comment-final.csv"))
  file_tokens=[]
  for index,row in comment_df.iterrows():
    if filType == "python":
      if row['path'].endswith("py"):
        contents=row["change"]
        try:
          lines=contents.split("\n")
        except:
          print("No file contents")
          file_tokens.append(None)
          continue
        code = ""
        for line in lines:
          line = line.strip()
          if line.startswith("import"):
            line=line.replace("import","")
            code += line + "\n"
          elif line.startswith("from") :
            line = line.replace("import", "")
            line = line.replace("from", "")
            code += line + "\n"
        file_tokens.append(code)
      else:
        file_tokens.append(None)

    if filType == "java":
      if row['path'].endswith("java"):
        contents=row["change"]
        try:
          contents=contents.split("\n")
        except:
          file_tokens.append(None)
          continue
        tokens=''
        for line in contents:
          if line.startswith("import"):
            line=line.replace("import","")
            tokens=tokens+' '+line

        # tree = javalang.parse.parse(contents)
        # tokens = ""
        # package_statement = tree.children[0]
        # tokens += package_statement.name
        # import_statements = tree.children[1]
        # for item in import_statements:
        #   tokens += " " + item.path
        print(tokens)
        file_tokens.append(tokens)
      else:
        file_tokens.append(None)

  comment_df['tokens']=file_tokens
  comment_df.to_csv(os.path.join(DATA_DIR, repo_name, repo_name,
                                 repo_name + "-review-comment-final.csv"),
                    index=False)
  print("File_updated successfully with tokens")

def format_diff(repo_name):
  DIFF_PREFIX = 'diff --git a/a.java b/a.java\nindex 51c00f47b54..3659a0811cd 100644\n--- a/a.java\n+++ b/a.java\n'
  substitute_deleted_number_re=r",\d*\s\+"
  substitute_added_number_re = r",\d*\s\@"
  comment_df = pd.read_csv(os.path.join(DATA_DIR, repo_name, repo_name,repo_name + "-review-comment-finalv2.csv"))
  format_diff_list=[]
  for index,row in comment_df.iterrows():
    patch=row['diff_hunk']
    patch_lines=patch.split('\n')
    added_line_count=0
    deleted_line_count=0
    contex_line_count=0
    first_line=patch_lines.pop(0)
    for i in range(0,len(patch_lines)):
      if patch_lines[i].startswith('+'):
        added_line_count+=1
      elif patch_lines[i].startswith('-'):
        deleted_line_count+=1
      else:
        contex_line_count+=1
    substitute_deleted_number_subst = f',{deleted_line_count+contex_line_count} +'
    substitute_added_number_subst = f',{added_line_count + contex_line_count} @'

    temp1 = re.sub(substitute_deleted_number_re, substitute_deleted_number_subst, first_line, 0, re.MULTILINE | re.DOTALL)
    result = re.sub(substitute_added_number_re, substitute_added_number_subst, temp1, 0, re.MULTILINE | re.DOTALL)
    result=DIFF_PREFIX+result
    patch_lines.insert(0,result)
    formatted_diff='\n'.join(patch_lines)
    format_diff_list.append(formatted_diff)
  comment_df['formatted_diff_hunk']=format_diff_list
  comment_df.to_csv(os.path.join(DATA_DIR, repo_name, repo_name,repo_name + "-review-comment-finalv2.csv"))
  print(f"Updated formatted diff in {repo_name} data frame")

if __name__=='__main__':
  DATA_DIR="Data directory"
  repo_name_list=["youtube-dl"]
  repo_list=["pandas-dev"]
  repo_directory="repo directory"

  for i in range(len(repo_name_list)):
    # #merge_dataset(repo_name_list[i])
    # get_pr_author(repo_list[i],repo_name_list[i])
    # remove_author_comments(repo_name_list[i])
    # remove_irrelevent_comments(repo_name_list[i])
    build_comment_file_map_updated(repo_name_list[i],repo_directory+repo_name_list[i]+"\\")
    # format_diff(repo_name_list[i])
    #comment_file_import_map(repo_name_list[i],"python")
