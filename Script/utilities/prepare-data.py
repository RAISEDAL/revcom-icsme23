import os
from sklearn.model_selection import train_test_split
import pandas as pd

def write_json_line(path,file_name,df):
  with open(os.path.join(path,file_name+".jsonl"), "w",encoding="utf-8") as f1:
    f1.write(df.to_json(orient='records', lines=True, force_ascii=False))
  f1.close()

def create_dataframe_cross_project(list_of_files,cross_project,test_file,model):
  df=pd.DataFrame()
  for file in list_of_files:
    if file.endswith('.csv') and cross_project==True and not file.startswith(test_file):
      df=df.append(pd.read_csv(data_root+file))
    elif file.endswith('.csv') and cross_project==False and file.startswith(test_file):
      df = df.append(pd.read_csv(data_root + file))
      break
    else:
      print("irrelevant file")

  df = df[df['change'].notna()]
  df = df.fillna('')
  patch_list=[]
  c_id=[]
  oldf=[]
  msg=[]
  old_lines=[]
  file_path=[]
  import_tokens=[]
  for index,row in df.iterrows():
    file_type=row['path']
    if file_type.endswith('.py') or file_type.endswith('.java'):
      patch_list.append(row["diff_hunk"])
      c_id.append((row['comment_id']))
      msg.append(row['comment_text'])
      oldf.append(row['change'])
      old_lines.append(row["original_line"])
      file_path.append(row['path'])
      import_tokens.append(row['tokens'])
    # else:
      # print("non python/java file")
  if model=='codereviewer':
    new_df=pd.DataFrame()
    new_df['id'] = c_id
    new_df['msg'] = msg
    new_df['patch']=patch_list
    new_df['oldf']=oldf
    return new_df
  else:
    new_df=pd.DataFrame()
    new_df['id'] = c_id
    new_df['msg'] = msg
    new_df['patch']=patch_list
    new_df['oldf']=oldf
    new_df['path']=file_path
    new_df['import_tokens']=import_tokens
    return new_df

def create_dataframe_non_cross_project(list_of_files,model):
  df=pd.DataFrame()
  for file in list_of_files:
    if file.endswith('.csv') and file.startswith("ansible"):
      temp_df=pd.read_csv(os.path.join(data_root, dir_name, file))
      temp_df['project_name']="ansible"
      df = df.append(temp_df)
    elif file.endswith('.csv') and file.startswith("django"):
      temp_df=pd.read_csv(os.path.join(data_root, dir_name, file))
      temp_df['project_name']="django"
      df = df.append(temp_df)
    elif file.endswith('.csv') and file.startswith("keras"):
      temp_df=pd.read_csv(os.path.join(data_root, dir_name, file))
      temp_df['project_name']="keras"
      df = df.append(temp_df)
    elif file.endswith('.csv') and file.startswith("youtube-dl"):
      temp_df=pd.read_csv(os.path.join(data_root, dir_name, file))
      temp_df['project_name']="youtube-dl"
      df = df.append(temp_df)
    elif file.endswith('.csv') and file.startswith("elasticsearch"):
      temp_df=pd.read_csv(os.path.join(data_root, dir_name, file))
      temp_df['project_name']="elasticsearch"
      df = df.append(temp_df)
    elif file.endswith('.csv') and file.startswith("kafka"):
      temp_df=pd.read_csv(os.path.join(data_root, dir_name, file))
      temp_df['project_name']="kafka"
      df = df.append(temp_df)
    elif file.endswith('.csv') and file.startswith("RxJava"):
      temp_df=pd.read_csv(os.path.join(data_root, dir_name, file))
      temp_df['project_name']="RxJava"
      df = df.append(temp_df)
    elif file.endswith('.csv') and file.startswith("spring-boot"):
      temp_df=pd.read_csv(os.path.join(data_root, dir_name, file))
      temp_df['project_name']="spring-boot"
      df = df.append(temp_df)
    else: print("irrelevant file")

  df = df[df['change'].notna()]
  df=df.fillna('')
  patch_list=[]
  c_id=[]
  oldf=[]
  msg=[]
  old_lines=[]
  file_path=[]
  import_tokens=[]
  projects=[]
  for index,row in df.iterrows():
    file_type=row['path']
    if file_type.endswith('.py') or file_type.endswith('.java'):
      patch_list.append(row["diff_hunk"])
      c_id.append((row['comment_id']))
      msg.append(row['comment_text'])
      oldf.append(row['change'])
      old_lines.append(row["original_line"])
      file_path.append(row['path'])
      import_tokens.append(row['tokens'])
      projects.append(row['project_name'])
    # else:
      # print("non python/java file")
  if model=='codereviewer':
    new_df=pd.DataFrame()
    new_df['id'] = c_id
    new_df['msg'] = msg
    new_df['patch']=patch_list
    new_df['oldf']=oldf
    return new_df
  else:
    new_df=pd.DataFrame()
    new_df['id'] = c_id
    new_df['msg'] = msg
    new_df['patch']=patch_list
    new_df['oldf']=oldf
    new_df['path']=file_path
    new_df['import_tokens']=import_tokens
    new_df['project_name']=projects
    return new_df


def prepare_codereviewer_data(list_of_files,test_file):
  # train,test=train_test_split(new_df,test_size=0.3, shuffle=True, random_state=8)
  # new_train,validation=train_test_split(train,test_size=0.1, shuffle=True, random_state=8)

  new_df=create_dataframe_cross_project(list_of_files,True,test_file,"codereviewer")
  test = create_dataframe_cross_project(list_of_files, False, test_file,"codereviewer")

  main_dataframe=pd.read_csv(data_root+dir_name+"\\original-data\\"+"revcom-dataset.csv")
  assert (56068==(len(new_df)+len(test)))
  #Cross-project evaluation
  # write_json_line(data_root,"main_data",new_df)
  new_train, validation = train_test_split(new_df, test_size=0.1, shuffle=True, random_state=8)
  write_json_line(data_root+dir_name,f"train_data-without-{test_file}",new_df)
  write_json_line(data_root+dir_name,f"test_data-{test_file}",test)
  write_json_line(data_root, f"val_data-{test_file}", validation)
  print("file written successfully")

def prepare_RevCom_data(list_of_files,test_file):
  new_df=create_dataframe_non_cross_project(list_of_files,"revcom")

  split_train_test_write(new_df)

def split_train_test_write(df,repo_name):
  train, test = train_test_split(df, test_size=0.3, shuffle=True,
                                 random_state=8)
  train.to_csv(os.path.join(data_root, dir_name,f"{repo_name}-train_ComFind.csv"),
               index=False)
  test.to_csv(os.path.join(data_root, dir_name,f"{repo_name}-test_ComFind.csv"), index=False)
  print("file written successfully")

def prepare_CommentFinder_data(list_of_files,repo_name):
  df=pd.DataFrame()
  for file in list_of_files:
    if file.endswith('.csv') and file.endswith('methods.csv'):
      df = df.append(pd.read_csv(os.path.join(data_root,dir_name,file)))
  df=df.fillna(' ')
  df_ansible=df[df['project_name']=='ansible']
  df_django = df[df['project_name'] == 'django']
  df_keras = df[df['project_name'] == 'keras']
  df_youtube = df[df['project_name'] == 'youtube-dl']
  df_elastic=df[df['project_name'] == 'elasticsearch']
  df_kafka = df[df['project_name'] == 'kafka']
  df_RxJava = df[df['project_name'] == 'RxJava']
  df_spring = df[df['project_name'] == 'spring-boot']
  assert len(df)==(len(df_ansible)+len(df_django)+len(df_keras)+len(df_youtube)
                   +len(df_elastic)+len(df_kafka)+len(df_RxJava)+len(df_spring))
  split_train_test_write(df_ansible,"ansible")
  split_train_test_write(df_django, "django")
  split_train_test_write(df_keras, "keras")
  split_train_test_write(df_youtube, "youtube")
  split_train_test_write(df_elastic, "elastic")
  split_train_test_write(df_kafka, "kafka")
  split_train_test_write(df_RxJava, "RxJava")

def prepare_CommentFinder_data_cross_project(list_of_files,test_repo_name):
  df=pd.DataFrame()
  for file in list_of_files:
    if file.endswith('.csv') and file.endswith('methods.csv'):
      temp=pd.read_csv(os.path.join(data_root, dir_name, file))
      print(len(temp))
      df = df.append(pd.read_csv(os.path.join(data_root,dir_name,file)))
  df=df.fillna(' ')

  df_train=df[df['project_name']!=test_repo_name]
  df_test=df[df['project_name']==test_repo_name]
  assert (len(df_train)+len(df_test))==len(df)
  df_train.to_csv(os.path.join(data_root, dir_name, f"{test_repo_name}-train_without_ComFind.csv"), index=False)
  df_test.to_csv(os.path.join(data_root, dir_name, f"{test_repo_name}-test_ComFind.csv"),index=False)
  print("file written successfully")

def prepare_CodeReviewer_data_new(list_of_files,repo_name):
  df = pd.DataFrame()
  for file in list_of_files:
    if file.endswith('.csv') and file.startswith(repo_name):
      df = df.append(pd.read_csv(os.path.join(data_root,dir_name,file)))
  df = df[df['change'].notna()]
  df = df.fillna('')
  patch_list=[]
  c_id=[]
  oldf=[]
  msg=[]
  for index,row in df.iterrows():
    file_type=row['path']
    if file_type.endswith('.py') or file_type.endswith('.java'):
      patch_list.append(row["diff_hunk"])
      c_id.append((row['comment_id']))
      msg.append(row['comment_text'])
      oldf.append(row['change'])
  new_df = pd.DataFrame()
  new_df['id'] = c_id
  new_df['msg'] = msg
  new_df['patch'] = patch_list
  new_df['oldf'] = oldf
  train,test=train_test_split(new_df,test_size=0.3, shuffle=True, random_state=8)
  new_train, validation = train_test_split(train, test_size=0.1, shuffle=True,
                                           random_state=8)
  assert (len(new_train)+len(test)+len(validation))==len(new_df)
  write_json_line(data_root + dir_write, f"train_data-{repo_name}",
                  train)
  write_json_line(data_root + dir_write, f"test_data-{repo_name}", test)
  write_json_line(data_root+dir_write, f"val_data-{repo_name}", validation)
  print("file written successfully")

def count_file(list_of_files):
  for file in list_of_files:
    if file.endswith('.csv'):
      temp = pd.read_csv(os.path.join(data_root, dir_name, file))
      print(f'{file}: {len(temp)}')

data_root= "root directory for data"
dir_name="CommentFinderData"
dir_write="CodeReviewerData\\project-wise"

list_of_files=os.listdir(os.path.join(data_root,dir_name))
# prepare_RevCom_data(list_of_files,None)
repo_name="spring-boot"
# test_file="spring-boot"  #cross-project pass the test file name
# prepare_codereviewer_data(list_of_files,"test_file")
# prepare_CodeReviewer_data_new(list_of_files,"RxJava")
# prepare_RevCom_data(list_of_files,"test_file")
prepare_CommentFinder_data(list_of_files,repo_name)
# prepare_CommentFinder_data_cross_project(list_of_files,repo_name)
# count_file(list_of_files)