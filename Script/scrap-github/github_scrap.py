import os
import re
import base64
import time

import pandas as pd
from oauthlib.oauth2 import ServerError
from requests.adapters import Retry
import configparser
import requests
from typing import Dict, List, Optional, Tuple, Union

NUM_REPOS=10
ROOT = 'https://api.github.com'

def get_rate_limited_response(path: str, token):
  token_list = _get_token_list()
  for i in range(len(token_list)):
    token = token_list[i]
    _headers = {
      'Authorization': f'Bearer {token}'
    }
    try:
      response_obj = requests.get(path, headers=_headers)
    except:
      print("Check Response error:" + path)
      flag=0
      last_page=0
      response=[]
      return response,last_page,flag
    if response_obj.status_code==502 or response_obj.status_code==500:
      time.sleep(5)
      return [], 0, 0

    limit_remaining = int(response_obj.headers['x-ratelimit-remaining'])
    if limit_remaining >= 1:
      break
    else:
      continue
  response = response_obj.json()
  print('token limit: ' + str(limit_remaining))
  try:
    last_page=int(response_obj.links['last']['url'].split("&")[1].split("=")[1])
  except:
    last_page=0
  flag=1
  return response,last_page,flag

def _get_token_list():
  config = configparser.RawConfigParser()
  path = os.getcwd()
  config.read(path + '\\github-token.cfg')
  details_dict = dict(config.items('DEFAULT'))
  tokens = list(details_dict.values())
  return tokens

def get_most_starred_repositories():
  star_conditions = ['>10100']
  for i in range(10000, 0, -100):
    star_conditions.append(f'{i}..{i + 99}')

  path_template = '/search/repositories?' \
                  'q=language:java+stars:{}+archived:false' \
                  '&sort=stars&order=desc&per_page=100'
  yield_count = 0
  repo_df=pd.DataFrame()
  for star_condition in star_conditions:
    if yield_count >= NUM_REPOS:
      break
    path_template_with_stars = path_template.format(star_condition)
    for page_n in range(10):
      path = f'{path_template_with_stars}&page={page_n + 1}'
      response,last_page,flag = get_rate_limited_response(f'{ROOT}{path}','')
      for item in response["items"]:
        repo_df=repo_df.append({"id":item["id"],"node_id":item["node_id"],"name":item["name"], "full_name":item["full_name"],"private":item["private"],

                             "html_url":item["html_url"],"description":item["description"],"fork":item["fork"],"url":item["url"],"forks_url":item["forks_url"],
                        "size":item["size"],"stargazers_count":item["stargazers_count"],
                        "watchers_count":item["watchers_count"],"language":item["language"],"archived":item["archived"],"forks":item["forks"],
                        "watchers":item["watchers"]},ignore_index=True)
  repo_df.to_csv("C:\\Users\wahid\PycharmProjects\RevCom\dataset\scrap-github\\top_100_repos_java-non-archived.csv")

      # assert isinstance(response, dict)
      # assert type(response['items']) is list, type(response['items'])



def get_review_comments():
  repo_df=pd.read_csv(os.path.join(DATA_DIR,"python-repo-name-last-one.csv"))
  for index,row in repo_df.iterrows():
    existing_data=os.listdir(DATA_DIR+"\\repo-data\\")
    if row["name"] =="kafka" or row["name"]=="elasticsearch":
       continue;
    if row["name"] in existing_data:
      existing_page=os.listdir(DATA_DIR+"\\repo-data\\"+row['name']+"\\")
      q=f"/repos/{row['full_name']}/pulls/comments?per_page=100"
      response, last_page, flag = get_rate_limited_response(f'{ROOT}{q}','')
      if last_page-len(existing_page)<10:
        print(f"{row['name']} existed")
        continue
    query=f"/search/issues?q=repo:{row['full_name']}%20is:pr"
    response,last_page,flag=get_rate_limited_response(f'{ROOT}{query}','')
    total_pr=response['total_count']
    from itertools import count

    if total_pr>1500:
      query=f"/repos/{row['full_name']}/pulls/comments?per_page=100"
      #query = f"/repos/keras-team/keras/pulls/comments?per_page=100"
      if not os.path.exists(
        os.path.join(DATA_DIR + "\\repo-data\\", row['name'])):
        os.mkdir(os.path.join(DATA_DIR + "\\repo-data\\", row['name']))

      file_list = os.listdir(DATA_DIR+"\\repo-data\\"+row['name']+"\\")
      page_number=1
      for page_n in count(1):
        if f"{row['name']}page-{page_number}.csv" in file_list:
          page_number = page_number + 1
          continue
        query=query+f'&page={page_number}'
        response,last_page,flag=get_rate_limited_response(f'{ROOT}{query}','')
        if flag==0:

          print(f"Server Error for page- {page_number}")
          query = f"/repos/{row['full_name']}/pulls/comments?per_page=100"
          continue
        comments_df = pd.DataFrame()
        for item in response:
          comments_df=comments_df.append({'comment_url':item["url"],'comment_id':item['id'],'diff_hunk':item["diff_hunk"],"path":item["path"],
                                        "commit_id":item["commit_id"],"original_commit_id":item["original_commit_id"],"user":item["user"],
                                        "comment_text":item["body"],"comment_time":item["created_at"],"pull_request_url":item["pull_request_url"],
                                        "line":item["line"],"original_line":item["original_line"]},ignore_index=True)
        comments_df.to_csv(os.path.join(DATA_DIR+"\\repo-data\\",row['name'], row['name'] + f"page-{page_number}.csv"),
                           index=False)
        print(f'{row["full_name"]}+ f" page-{page_number}.csv written succesfully')
        time.sleep(5)
        page_number=page_number+1
        if page_number==last_page-1:
          break
def get_review_commits(org_name,repo_name):
  comment_df=pd.read_csv(os.path.join(DATA_DIR,"repo-data", repo_name, repo_name,
                                   repo_name + "-review-comment-final.csv"))
  commit_list=comment_df['original_commit_id'].to_list()
  unique_commits=list(set(commit_list))
  #print(unique_commits)
  for commit in unique_commits:
    query=f"/repos/{org_name}/{repo_name}/commits/{commit}?per_page=100"
    response, last_page, flag = get_rate_limited_response(f'{ROOT}{query}', '')
    commit_df=pd.DataFrame()
    try:
      for file in response['files']:
        commit_df=commit_df.append({'commit_sha':response['sha'],'file_path':file['filename'],'contents_url':file['contents_url'],'raw_url':file['raw_url'],
                                    "additions":file['additions'],"deletions":file["deletions"],"status":file["status"],
                                    "commit_message":response["commit"]['message'],"commit_author":response["commit"]["author"]["name"]},ignore_index=True)
    except:
      continue
    if not os.path.exists(os.path.join(DATA_DIR,"repo-data", repo_name, repo_name,"commit")):
      os.mkdir(os.path.join(DATA_DIR,"repo-data", repo_name, repo_name,"commit"))
    commit_df.to_csv(os.path.join(DATA_DIR,"repo-data", repo_name, repo_name,"commit",commit+".csv"),index=False)
    print(f'{commit} written successfully')
def get_file_content_updated(org_name,repo_name):
  comment_df=pd.read_csv(os.path.join(DATA_DIR,"repo-data",repo_name,repo_name,repo_name+"-review-comment-final.csv"))
  new_df = pd.DataFrame()
  comment_id = []
  comment_diff = []
  comment_text = []
  comment_source_file = []
  cfile_path = []
  for index,row in comment_df.iterrows():
    path=row['path']
    if path.endswith('.py'):
      query = f"/repos/{org_name}/{repo_name}/contents/{path}?ref={row['original_commit_id']}~1"
      response, last_page, flag = get_rate_limited_response(f'{ROOT}{query}','')
      if len(response) > 2:
        try:
          content = base64.b64decode(response['content']).decode(encoding='utf-8')
        except:
          print("Can not decode the file byte error")
          continue
      else:
        continue
      comment_id.append(row['comment_id'])
      comment_diff.append(row['diff_hunk'])
      comment_text.append(row['comment_text'])
      comment_source_file.append(content)
      cfile_path.append(row['path'])
    else:
      print(f"path: {path}")
  new_df['comment_id'] = comment_id
  new_df['diff_hunk'] = comment_diff
  new_df['comment_text'] = comment_text
  new_df['change'] = comment_source_file
  new_df['path'] = cfile_path
  print(len(new_df))
  new_df.to_csv(os.path.join(DATA_DIR,"repo-data",repo_name,repo_name,repo_name+"-review-comment-finalv2.csv"),index=False)
  print(f"{repo_name} written successfully")


def get_file_content(repo_name):
  listCommit=os.listdir(os.path.join(DATA_DIR,"repo-data",repo_name,repo_name,"commit"))
  comment_df=pd.read_csv(os.path.join(DATA_DIR,"repo-data",repo_name,repo_name,repo_name+"-review-comment-final.csv"))
  comment_files=comment_df['path'].to_list()
  for commit in listCommit:
    try:
      df=pd.read_csv(os.path.join(DATA_DIR,"repo-data",repo_name,repo_name,"commit",commit))
    except:
      print(f"{commit} Empty Commit file")
      continue
    if not os.path.exists(os.path.join(DATA_DIR,"repo-data",repo_name,repo_name,"change-file")):
      os.mkdir(os.path.join(DATA_DIR,"repo-data",repo_name,repo_name,"change-file"))
    for index,row in df.iterrows():
      existing_file=os.listdir(os.path.join(DATA_DIR,"repo-data",repo_name,repo_name,"change-file"))
      path_name = row['file_path'].split('.')[0]
      path_name = path_name.replace("/", "-")
      if row['file_path'] in comment_files and not commit.split(".")[0]+"-"+path_name+".csv" in existing_file:
        file_df=pd.DataFrame(columns=['file_path','contents'])
        response, last_page, flag = get_rate_limited_response(f'{row["contents_url"]}',"")
        if len(response)==2:
          response, last_page, flag = get_rate_limited_response(
            f'{row["contents_url"]}', "")
        if len(response)>2:
          try:
            content= base64.b64decode(response['content']).decode(encoding='utf-8')
          except:
            print("Can not decode the file byte error")
            continue
          if len(content)>=2:
            file_df=file_df.append({"file_path":row['file_path'],"contents":content},ignore_index=True)
            try:
              file_df.to_csv(os.path.join(DATA_DIR,"repo-data",repo_name,repo_name,"change-file",commit.split(".")[0]+"-"+path_name+".csv"),index=False)
            except:
              print(f"{path_name} was not written")
              continue
            print(f"{path_name} written successfully")
          else:
            print("Empty Contents")
      else:
        print("File existed")
      #print("DOne")

if __name__=="__main__":
  DATA_DIR="Data directory"
  repo_name_list=["keras"]
  repo_org_list=["keras-team"]
  #get_review_comments()
  # #get_most_starred_repositories()
  for i in range(len(repo_name_list)):
    #get_review_commits(repo_list[i],repo_name_list[i])
    get_file_content_updated(repo_org_list[i],repo_name_list[i])
