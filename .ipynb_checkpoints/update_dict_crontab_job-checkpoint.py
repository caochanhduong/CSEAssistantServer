import json
import re
import pymongo
from pymongo import MongoClient
import random
import os
import glob
import os

# list_of_files = glob.glob('/home/lap11305/LVTN/CSEAssistantServer/*.json') # * means all if need specific format then *.csv
# latest_file = max(list_of_files, key=os.path.getctime)
client = MongoClient('mongodb://caochanhduong:bikhungha1@ds261626.mlab.com:61626/activity?retryWrites=false')
db = client.activity
with open('/home/lap11305/LVTN/CSEAssistantServer/real_dict_2000_new_only_delete_question_noti_new_and_space_newest.json','r') as dict_file:
    real_dict = json.load(dict_file)
    update_real_dict = {}
    check_same_dict = True
    for key in list(real_dict.keys()):
        db_key_res = db.dictionary.find({"type":key})
        results = []
        for result in db_key_res:
            if isinstance(result["value"],str):
                results.append(result["value"])
        update_real_dict[key] = list(set(results))
        update_real_dict[key].sort(reverse=True,key=len)
        real_dict[key] = list(set(real_dict[key]))
        real_dict[key].sort(reverse=True,key=len)
    #check length first
    for key in list(real_dict.keys()):
        if len(real_dict[key]) != len(update_real_dict[key]):
            check_same_dict = False
            break
    if check_same_dict == True:
        for key in list(real_dict.keys()):
            check_same_list = True
            for i in range(len(real_dict[key])):
                if real_dict[key][i] != update_real_dict[key][i]:
                    check_same_list = False
                    break
            if check_same_list == False:
                check_same_dict = False
                break
    # có thay đổi mới update
    if check_same_dict == False:
        random_path_num=str(random.randrange(0,10000000))
        os.rename(r'/home/lap11305/LVTN/CSEAssistantServer/real_dict_2000_new_only_delete_question_noti_new_and_space_newest.json',r'/home/lap11305/LVTN/CSEAssistantServer/real_dict_2000_new_only_delete_question_noti_new_and_space_newest'+random_path_num+'.json')
        with open('/home/lap11305/LVTN/CSEAssistantServer/real_dict_2000_new_only_delete_question_noti_new_and_space_newest.json', 'w+') as dict_file_new:
            json.dump(update_real_dict,dict_file_new,ensure_ascii=False)
