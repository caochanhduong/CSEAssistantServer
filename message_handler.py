#!/usr/bin/env python
# coding: utf-8
# from agent_utils.state_tracker import StateTracker
from sklearn.externals import joblib
import numpy as np
from sklearn import preprocessing
from sklearn.feature_extraction.text import TfidfVectorizer
from fastai.text import *
import torch
import pickle
import numpy as np
from sklearn.externals import joblib
from sklearn import preprocessing
import constants
import json
from collections import OrderedDict
import re
from constants import *

# imp.reload(real_dict)

def sentence_to_index_vector(input_sentence):
  list_token=input_sentence.split(' ')
  return vocab.numericalize(list_token)

def check_match_sublist_and_substring(list_children,list_parent):
        # print("match sublist")
        count_match=0
        list_children = [compound2unicode(x) for x in list_children]
        list_parent = [compound2unicode(x) for x in list_parent]
        for children_value in list_children:
            for parent_value in list_parent:
                if children_value in parent_value:
                    count_match+=1
                    break
        if count_match==len(list_children):
            # print("match sublist")
            return True
        return False

def forward_dropout(input_sentence):
  t = torch.tensor([sentence_to_index_vector(input_sentence)])
  lm.reset()
  raw_output, dropout_output = lm[0](t)
  
  dropout_output_last_lst=dropout_output[2].detach().numpy().tolist()
  dropout_output_last_lst=dropout_output_last_lst[0]
#   #print(dropout_output_last_lst)
  max_pooling_lst=[]
  avg_pooling_lst=[]
#   print(len(dropout_output_last_lst))
  for i in range(emb_sz):
    lst_one_emb=[]
    for j in range(len(dropout_output_last_lst)-1):
        lst_one_emb.append(dropout_output_last_lst[j][i])
    if len(dropout_output_last_lst)==1:
        max_pooling_lst.append(dropout_output_last_lst[0][i])
        avg_pooling_lst.append(dropout_output_last_lst[0][i])
    else:    
        max_pooling_lst.append(max(lst_one_emb))
        avg_pooling_lst.append(sum(lst_one_emb) / len(lst_one_emb) )
  return max_pooling_lst+avg_pooling_lst+dropout_output_last_lst[-1]


#message -> intent want information
def extract_and_get_intent(message):
        # 10 intent pattern matching

    for notification in list_address_notification:
        if message.lower().find(notification)!=-1:
            return 'address',1.0,message

    for notification in list_name_place_notification:
        if message.lower().find(notification)!=-1 and "liên lạc" not in message.lower() and "liên hệ" not in message.lower() and "đăng kí" not in message.lower() and "đăng ký" not in message.lower():
            return 'name_place',1.0,message


    for notification in list_type_activity_notification:
        if message.lower().find(notification)!=-1:
            return 'type_activity',1.0,message

    for notification in list_name_activity_notification:
        if message.lower().find(notification)!=-1:
            return 'name_activity',1.0,message

    

    for notification in list_time_notification:
        if message.lower().find(notification)!=-1 and "đăng ký" not in message.lower() and "đăng kí" not in message.lower() and "có khi nào" not in message.lower():
            return 'time',1.0,message

    for notification in list_holder_notification:
        if message.lower().find(notification)!=-1 and "liên lạc" not in message.lower() and "liên hệ" not in message.lower() and "đăng kí" not in message.lower() and "đăng ký" not in message.lower() and "sdt" not in message.lower() and "số điện thoại" not in message.lower() and "email" not in message.lower() and "sđt" not in message.lower() and "facebook" not in message.lower() and "fb" not in message.lower():
            return 'holder',1.0,message

    for notification in list_reward_notification:
        if message.lower().find(notification)!=-1:
            return 'reward',1.0,message

    if message.lower().find("được") < message.lower().find("ngày ctxh") or message.lower().find("được") < message.lower().find("ngày công tác xã hội") or message.lower().find("được") < message.lower().find("điểm rèn luyện") or message.lower().find("được") < message.lower().find("đrl") or message.lower().find("được") < message.lower().find("drl"):
        return 'reward',1.0,message
        
    
    # 5 intent machine learning 
    

    max_proba=np.amax(clf.predict_proba([forward_dropout(message)])[0])

    #print(clf.predict_proba([forward_dropout(message)])[0])
    #print(max_proba)
    if max_proba>CONST_THRESHOLD:
        if le.inverse_transform(clf.predict([forward_dropout(message.lower())]))[0] == "work":
            return "works",max_proba,message
        return le.inverse_transform(clf.predict([forward_dropout(message.lower())]))[0],max_proba,message


    return 'other',1.0,message


#message -> check intent want information 
def check_intent(message):
#     ... subject muốn hỏi/biết/xin… *
# ... subject muốn được hỏi/tư vấn .... *
# ... cho subject hỏi/biết/xin *
# ... subject cần hỏi/biết/xin... *
# .... subject cần ... thông tin … *
# .... gửi subject ... *
# ... cho hỏi/xin/biết… *
# ... có/được (...)? không (...) *
    #bắt WH question 
    for signal in list_question_signal:
        if signal in message.lower():
            # #print(signal)
            return True

    for verb in list_verb_have:
        if (message.lower().find(verb)!=-1 and message.lower().find("không")!=-1 and message.lower().find(verb)<message.lower().find("không")):
            #print("1")
            return True

    #....sao (liên hệ/đăng ký sao)
    if "sao"==message.split(' ')[len(message.split(' '))-1]:
        return True


    #.... sao bạn
    for object in list_object:
        if message.lower().find("sao")!=-1 and message.lower().find(object)!=-1 and message.lower().find("sao")<message.lower().find(object):
            return True

    if (message.lower().find("còn")!=-1 and message.lower().find("không")!=-1 and message.lower().find("còn")<message.lower().find("không")):
        #print("1")
        return True
    
    if message.lower().find("xin")!=-1 and (message.lower().find("chào")< message.lower().find("xin")):
        #print("1")
        return True

    #cách liên hệ/đăng ký
    if message.lower().find("cách")==0:
        #print("1")
        return True

    #ai .... (ai được tham gia)
    if message.lower().find("ai")==0:
        #print("1")
        return True


    # #thông tin về xxx/thông tin xxx
    # if message.lower().find("thông tin")!=-1:
    #     #print("1")
    #     return True

    for subject in list_subject:
        for verb in list_verb_want:
            if (message.lower().find(subject+" muốn "+verb)!=-1 or message.lower().find("cho "+subject+" "+verb)!=-1 or message.lower().find(subject+" cần "+verb)!=-1):
                #print("2")
                return True

    for subject in list_subject:
        #chứ bạn
        if message.lower().find("chứ "+subject)!=-1:
            #print("3")
            return True
        if (message.lower().find(subject+" muốn được hỏi")!=-1 or message.lower().find(subject+" muốn được tư vấn")!=-1):
            #print("3")
            return True
        if (message.lower().find(subject+" cần")!=-1 and message.lower().find("thông tin")!=-1 and message.lower().find(subject+" cần")<message.lower().find("thông tin")):
            #print("4")
            return True
        if (message.lower().find(subject+" muốn")!=-1 and message.lower().find("thông tin")!=-1 and message.lower().find(subject+" muốn")<message.lower().find("thông tin")):
            #print("4")
            return True
        if (message.lower().find("gửi "+subject)!=-1):
            #print("5")
            return True
        if (message.lower().find("chỉ "+subject)!=-1):
            #print("5")
            return True
        if (message.lower().find("chỉ giúp "+subject)!=-1):
            #print("5")
            return True

    #cho xin
    for verb in list_verb_want:
        if (message.lower().find("cho "+verb)!=-1):
            #print("6")
            return True

    # nào ... nhỉ
    for signal in list_question_signal_last:
        if (message.lower().find("nào")!=-1) and (message.lower().find(signal)!=-1) and (message.lower().find("nào")<message.lower().find(signal)):
            #print("6")
            return True

    #...... hả
    if message.lower().split(' ')[len(message.lower().split(' '))-1]=="hả":
        return True
    

    
    #gửi cho mình/cho mình/gửi mình/mình cần/mình muốn
    for subject in list_subject:
        if (message.lower().find("cho "+subject)!=-1) or (message.lower().find("gửi "+subject)!=-1) or (message.lower().find(subject+" cần")!=-1) or (message.lower().find(subject+" muốn")!=-1):
            return True


    #mình (có việc) muốn/cần
    #mình định....
    for subject in list_subject:
        if ((message.lower().find(subject)!=-1) and (message.lower().find("định")!=-1) and (message.lower().find(subject)<message.lower().find("định"))) or ((message.lower().find(subject)!=-1) and (message.lower().find("cần")!=-1) and (message.lower().find(subject)<message.lower().find("cần"))) or ((message.lower().find(subject)!=-1) and (message.lower().find("muốn")!=-1) and (message.lower().find(subject)<message.lower().find("muốn"))):
            return True

    #bắt YES-NO/WH question mà signal cuối câu 
    if len(message.split(" "))>3 and (message.split(" ")[-1].lower()=="chưa" or message.split(" ")[-1].lower()=="không" or message.split(" ")[-1].lower()=="ta" or message.split(" ")[-1].lower()=="sao" or message.split(" ")[-1].lower()=="nhỉ" or message.split(" ")[-1].lower()=="nào"):
        #print("7")
        return True

    #bắt YES-NO question cuối câu có chủ ngữ

    for subject in list_object:
        for question_signal_last in list_question_signal_last:
            if message.split(" ")[-1].lower()==subject and message.split(" ")[-2].lower()==question_signal_last:
                #print("8")
                return True 
    

    return False

def preprocess_message(message):
    message = message.lower()
    message = message.replace(',', ' , ')
    message = message.replace('.', ' . ')
    message = message.replace('!', ' ! ')
    message = message.replace('&', ' & ')
    message = message.replace('?', ' ? ')
    message = message.replace('-', ' - ')
    message = message.replace('(', ' ( ')
    message = message.replace(')', ' ) ')
    message = compound2unicode(message)
    list_token = message.split(' ')
    while '' in list_token:
        list_token.remove('')
    message = ' '.join(list_token)
    return message
#message -> final output 
def catch_intent(message):
    message = re.sub('[\:\_=\+\#\@\$\%\$\\(\)\~\@\;\'\|\<\>\]\[\"\–“”…*]',' ',message)
    message_preprocessed = preprocess_message(message)
    #note : vì notification của anything dễ bị nhầm với check intent (do chứa "cái gì","sao")
    # nên check trước
    if len(message_preprocessed.lower().split(" ")) == 1 and (message_preprocessed.lower()==compound2unicode("không") or message_preprocessed.lower() == "no"):
        return 'anything',1.0,message_preprocessed 
    for notification in list_anything_notification:   
        if message_preprocessed.lower().find(notification)!=-1:
            return 'anything',1.0,message_preprocessed

    if check_intent(message_preprocessed):
            #remove ? with blank in the last
        message_preprocessed=re.sub('[?]','',message_preprocessed.lower())
        list_token=message_preprocessed.split(' ')
        while '' in list_token:
            list_token.remove('')
        message_preprocessed=' '.join(list_token)
        return extract_and_get_intent(message_preprocessed)

    message_preprocessed=re.sub('[?]','',message_preprocessed.lower())
    list_token=message_preprocessed.split(' ')
    while '' in list_token:
        list_token.remove('')
    message_preprocessed=' '.join(list_token)
    print("---------------------------message preprocessed")
    print(message_preprocessed)
    for notification in list_done_notification:   
        if message_preprocessed.lower().find(notification)!=-1:
            return 'done',1.0,message_preprocessed

    for notification in list_hello_notification:   
        if message_preprocessed.lower().find(notification)!=-1:
            return 'hello',1.0,message_preprocessed
    
    for notification in list_thanks_notification:   
        if message_preprocessed.lower().find(notification)!=-1:
            return 'thanks',1.0,message_preprocessed



    for object in list_object:
        if message_preprocessed.lower().find("hi " +object)!=-1 and len(message_preprocessed.split(' '))<=5:
            return 'hello',1.0,message_preprocessed
    if message_preprocessed.lower() == "hi":
        return "hello",1.0,message_preprocessed

    return 'not intent',1.0,message_preprocessed

def compound2unicode(text):
  #https://gist.github.com/redphx/9320735`
  text = text.replace("\u0065\u0309", "\u1EBB")    # ẻ
  text = text.replace("\u0065\u0301", "\u00E9")    # é
  text = text.replace("\u0065\u0300", "\u00E8")    # è
  text = text.replace("\u0065\u0323", "\u1EB9")    # ẹ
  text = text.replace("\u0065\u0303", "\u1EBD")    # ẽ
  text = text.replace("\u00EA\u0309", "\u1EC3")    # ể
  text = text.replace("\u00EA\u0301", "\u1EBF")    # ế
  text = text.replace("\u00EA\u0300", "\u1EC1")    # ề
  text = text.replace("\u00EA\u0323", "\u1EC7")    # ệ
  text = text.replace("\u00EA\u0303", "\u1EC5")    # ễ
  text = text.replace("\u0079\u0309", "\u1EF7")    # ỷ
  text = text.replace("\u0079\u0301", "\u00FD")    # ý
  text = text.replace("\u0079\u0300", "\u1EF3")    # ỳ
  text = text.replace("\u0079\u0323", "\u1EF5")    # ỵ
  text = text.replace("\u0079\u0303", "\u1EF9")    # ỹ
  text = text.replace("\u0075\u0309", "\u1EE7")    # ủ
  text = text.replace("\u0075\u0301", "\u00FA")    # ú
  text = text.replace("\u0075\u0300", "\u00F9")    # ù
  text = text.replace("\u0075\u0323", "\u1EE5")    # ụ
  text = text.replace("\u0075\u0303", "\u0169")    # ũ
  text = text.replace("\u01B0\u0309", "\u1EED")    # ử
  text = text.replace("\u01B0\u0301", "\u1EE9")    # ứ
  text = text.replace("\u01B0\u0300", "\u1EEB")    # ừ
  text = text.replace("\u01B0\u0323", "\u1EF1")    # ự
  text = text.replace("\u01B0\u0303", "\u1EEF")    # ữ
  text = text.replace("\u0069\u0309", "\u1EC9")    # ỉ
  text = text.replace("\u0069\u0301", "\u00ED")    # í
  text = text.replace("\u0069\u0300", "\u00EC")    # ì
  text = text.replace("\u0069\u0323", "\u1ECB")    # ị
  text = text.replace("\u0069\u0303", "\u0129")    # ĩ
  text = text.replace("\u006F\u0309", "\u1ECF")    # ỏ
  text = text.replace("\u006F\u0301", "\u00F3")    # ó
  text = text.replace("\u006F\u0300", "\u00F2")    # ò
  text = text.replace("\u006F\u0323", "\u1ECD")    # ọ
  text = text.replace("\u006F\u0303", "\u00F5")    # õ
  text = text.replace("\u01A1\u0309", "\u1EDF")    # ở
  text = text.replace("\u01A1\u0301", "\u1EDB")    # ớ
  text = text.replace("\u01A1\u0300", "\u1EDD")    # ờ
  text = text.replace("\u01A1\u0323", "\u1EE3")    # ợ
  text = text.replace("\u01A1\u0303", "\u1EE1")    # ỡ
  text = text.replace("\u00F4\u0309", "\u1ED5")    # ổ
  text = text.replace("\u00F4\u0301", "\u1ED1")    # ố
  text = text.replace("\u00F4\u0300", "\u1ED3")    # ồ
  text = text.replace("\u00F4\u0323", "\u1ED9")    # ộ
  text = text.replace("\u00F4\u0303", "\u1ED7")    # ỗ
  text = text.replace("\u0061\u0309", "\u1EA3")    # ả
  text = text.replace("\u0061\u0301", "\u00E1")    # á
  text = text.replace("\u0061\u0300", "\u00E0")    # à
  text = text.replace("\u0061\u0323", "\u1EA1")    # ạ
  text = text.replace("\u0061\u0303", "\u00E3")    # ã
  text = text.replace("\u0103\u0309", "\u1EB3")    # ẳ
  text = text.replace("\u0103\u0301", "\u1EAF")    # ắ
  text = text.replace("\u0103\u0300", "\u1EB1")    # ằ
  text = text.replace("\u0103\u0323", "\u1EB7")    # ặ
  text = text.replace("\u0103\u0303", "\u1EB5")    # ẵ
  text = text.replace("\u00E2\u0309", "\u1EA9")    # ẩ
  text = text.replace("\u00E2\u0301", "\u1EA5")    # ấ
  text = text.replace("\u00E2\u0300", "\u1EA7")    # ầ
  text = text.replace("\u00E2\u0323", "\u1EAD")    # ậ
  text = text.replace("\u00E2\u0303", "\u1EAB")    # ẫ
  text = text.replace("\u0045\u0309", "\u1EBA")    # Ẻ
  text = text.replace("\u0045\u0301", "\u00C9")    # É
  text = text.replace("\u0045\u0300", "\u00C8")    # È
  text = text.replace("\u0045\u0323", "\u1EB8")    # Ẹ
  text = text.replace("\u0045\u0303", "\u1EBC")    # Ẽ
  text = text.replace("\u00CA\u0309", "\u1EC2")    # Ể
  text = text.replace("\u00CA\u0301", "\u1EBE")    # Ế
  text = text.replace("\u00CA\u0300", "\u1EC0")    # Ề
  text = text.replace("\u00CA\u0323", "\u1EC6")    # Ệ
  text = text.replace("\u00CA\u0303", "\u1EC4")    # Ễ
  text = text.replace("\u0059\u0309", "\u1EF6")    # Ỷ
  text = text.replace("\u0059\u0301", "\u00DD")    # Ý
  text = text.replace("\u0059\u0300", "\u1EF2")    # Ỳ
  text = text.replace("\u0059\u0323", "\u1EF4")    # Ỵ
  text = text.replace("\u0059\u0303", "\u1EF8")    # Ỹ
  text = text.replace("\u0055\u0309", "\u1EE6")    # Ủ
  text = text.replace("\u0055\u0301", "\u00DA")    # Ú
  text = text.replace("\u0055\u0300", "\u00D9")    # Ù
  text = text.replace("\u0055\u0323", "\u1EE4")    # Ụ
  text = text.replace("\u0055\u0303", "\u0168")    # Ũ
  text = text.replace("\u01AF\u0309", "\u1EEC")    # Ử
  text = text.replace("\u01AF\u0301", "\u1EE8")    # Ứ
  text = text.replace("\u01AF\u0300", "\u1EEA")    # Ừ
  text = text.replace("\u01AF\u0323", "\u1EF0")    # Ự
  text = text.replace("\u01AF\u0303", "\u1EEE")    # Ữ
  text = text.replace("\u0049\u0309", "\u1EC8")    # Ỉ
  text = text.replace("\u0049\u0301", "\u00CD")    # Í
  text = text.replace("\u0049\u0300", "\u00CC")    # Ì
  text = text.replace("\u0049\u0323", "\u1ECA")    # Ị
  text = text.replace("\u0049\u0303", "\u0128")    # Ĩ
  text = text.replace("\u004F\u0309", "\u1ECE")    # Ỏ
  text = text.replace("\u004F\u0301", "\u00D3")    # Ó
  text = text.replace("\u004F\u0300", "\u00D2")    # Ò
  text = text.replace("\u004F\u0323", "\u1ECC")    # Ọ
  text = text.replace("\u004F\u0303", "\u00D5")    # Õ
  text = text.replace("\u01A0\u0309", "\u1EDE")    # Ở
  text = text.replace("\u01A0\u0301", "\u1EDA")    # Ớ
  text = text.replace("\u01A0\u0300", "\u1EDC")    # Ờ
  text = text.replace("\u01A0\u0323", "\u1EE2")    # Ợ
  text = text.replace("\u01A0\u0303", "\u1EE0")    # Ỡ
  text = text.replace("\u00D4\u0309", "\u1ED4")    # Ổ
  text = text.replace("\u00D4\u0301", "\u1ED0")    # Ố
  text = text.replace("\u00D4\u0300", "\u1ED2")    # Ồ
  text = text.replace("\u00D4\u0323", "\u1ED8")    # Ộ
  text = text.replace("\u00D4\u0303", "\u1ED6")    # Ỗ
  text = text.replace("\u0041\u0309", "\u1EA2")    # Ả
  text = text.replace("\u0041\u0301", "\u00C1")    # Á
  text = text.replace("\u0041\u0300", "\u00C0")    # À
  text = text.replace("\u0041\u0323", "\u1EA0")    # Ạ
  text = text.replace("\u0041\u0303", "\u00C3")    # Ã
  text = text.replace("\u0102\u0309", "\u1EB2")    # Ẳ
  text = text.replace("\u0102\u0301", "\u1EAE")    # Ắ
  text = text.replace("\u0102\u0300", "\u1EB0")    # Ằ
  text = text.replace("\u0102\u0323", "\u1EB6")    # Ặ
  text = text.replace("\u0102\u0303", "\u1EB4")    # Ẵ
  text = text.replace("\u00C2\u0309", "\u1EA8")    # Ẩ
  text = text.replace("\u00C2\u0301", "\u1EA4")    # Ấ
  text = text.replace("\u00C2\u0300", "\u1EA6")    # Ầ
  text = text.replace("\u00C2\u0323", "\u1EAC")    # Ậ
  text = text.replace("\u00C2\u0303", "\u1EAA")    # Ẫ
  return text


def longest_common_sublist(a, b):
    table = {}
    l = 0
    i_max = None
    j_max = None
    for i, ca in enumerate(a, 1):
        for j, cb in enumerate(b, 1):
            if ca == cb:
                table[i, j] = table.get((i - 1, j - 1), 0) + 1
                if table[i, j] > l:
                    l = table[i, j]
                    i_max=i
                    j_max=j
    if i_max != None:
        return l,i_max - 1
    return l,i_max

def lcs_length_ta(x, y):
    m = len(x)
    n = len(y)
    c = [[0 for x in range(n+1)] for y in range(m+1)] 
    b = [['' for x in range(n+1)] for y in range(m+1)] 
    
    for i in range(1,m+1):
        for j in range(1,n+1):
            if x[i-1] == y[j-1]:
                c[i][j] = c[i-1][j-1] + 1
                b[i][j] = '↖️'
            elif c[i - 1][j] >= c[i][j-1]:
                c[i][j] = c[i - 1][j] 
                b[i][j] = '⬆️'
            else:
                c[i][j] = c[i][j-1] 
                b[i][j] = '⬅️'
    max_common_length = c[-1][-1]
    i = m
    j = n
    pointer = c[i][j]
    result_index = []
    i_max = 0
    max_length_in_sentence = 0
    while pointer != 0:
        if pointer == max_common_length and b[i][j]=='⬆️':
            i = i-1
            pointer = c[i][j]
        if pointer == max_common_length and b[i][j]=='⬅️':
            j = j-1
            pointer = c[i][j]
        if pointer == max_common_length and b[i][j]=='↖️':
            result_index.append(i)
            i = i-1
            j = j-1
            pointer = c[i][j]
        if pointer != max_common_length and b[i][j]=='⬆️':
            result_index.append(i)
            i = i-1
            pointer = c[i][j]
        if pointer != max_common_length and b[i][j]=='⬅️':
            result_index.append(i)
            j = j-1
            pointer = c[i][j]
        if pointer != max_common_length and b[i][j]=='↖️':
            result_index.append(i)
            j = j-1
            i = i-1
            pointer = c[i][j]
#     print(result_index)
#     print(max_common_length)
    if result_index != [] :
        i_max = result_index[0]-1
        max_length_in_sentence = result_index[0] -result_index[-1] +1
    
    return max_common_length,max_length_in_sentence,i_max
    
def find_entity_longest_common(sentence,list_entity,entity_name):
    normalized_sentence=compound2unicode(sentence)
    list_token_sentence = normalized_sentence.split(' ')
    list_result_entity = []
    dict_max_len = {}
    list_normalized_entity = [compound2unicode(entity) for entity in list_entity]
    result = []
    longest_common_length = None
    end_common_index = None
    for index, entity in enumerate(list_normalized_entity):
#         print(entity)
        list_token_entity = entity.split(' ')
        if entity_name in ['register','reward','works']:
            longest_common_length, max_length_in_sentence, end_common_index = lcs_length_ta(list_token_sentence,list_token_entity)
        else:
            longest_common_length, end_common_index = longest_common_sublist(list_token_sentence,list_token_entity)
#         print(longest_common_length)
        if longest_common_length!=0:
            if entity_name in ['register','reward','works']:
                longest_common_length_entity, max_length_in_sentence_entity, end_common_index_entity = lcs_length_ta(list_token_entity,list_token_sentence)
                if float(longest_common_length)/max_length_in_sentence > 0.6 and float(longest_common_length_entity)/max_length_in_sentence_entity>0.6:
                    dict_max_len[str(index)] = {'max_length_in_sentence':max_length_in_sentence,'longest_common_length':longest_common_length,'end_common_index':end_common_index}
            else:
                dict_max_len[str(index)] = {'longest_common_length':longest_common_length,'end_common_index':end_common_index}
#         list_token_sentence = list_token_sentence[: end_common_index - longest_common_length] + list_token_sentence[end_common_index:]
    max_longest_common_length=0
#     print(dict_max_len)
    for k,v in dict_max_len.items():
        if v['longest_common_length']>max_longest_common_length:
            max_longest_common_length=v['longest_common_length']
    
    for k,v in dict_max_len.items():
        if v['longest_common_length']==max_longest_common_length:
            if entity_name in ['register','reward','works']:
                result.append({"longest_common_entity_index":int(k),"longest_common_length":v['max_length_in_sentence'],"end_common_index":v['end_common_index']})
            else:
                result.append({"longest_common_entity_index":int(k),"longest_common_length":v['longest_common_length'],"end_common_index":v['end_common_index']})
    return result

def delete_extra_word(sentence,list_extra_word):
    for word in list_extra_word:
        if word == " hả ":
            sentence = sentence.replace(word," ✪ ")
        elif word == " ai ":
            sentence = sentence.replace(word," ✪ ")
        elif word == " ai":
            sentence = sentence.replace(word," ✪")
        elif word in list_question_signal_last and word == sentence.split(' ')[len(sentence.split(' '))-1]:
            sentence = sentence.replace(word,"✪")
        else:# replace la sao -> ✪ ✪
            sentence = sentence.replace(word,' '.join(['✪']*(word.count(' ')+1)))
    return sentence

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def replace_digit_in_string(inputString):
    return ''.join(['\d' if char.isdigit() else char for char in inputString])

def delete_last_space_list(list_input_string):
    result = []
    for input_string in list_input_string:
        if input_string[len(input_string)-1]==' ':
            result.append(input_string[:len(input_string)-1])
            continue
        result.append(input_string)
    return result

def check_sublist(a,b):
    if len(a) > len(b):
        return False
    if a == b:
        return True
    check = True
    for item_a in a:
        if item_a not in b:
            check = False
            break
    return check

def find_all_entity(intent,input_sentence):
    #dictionary
    with open('real_dict_2000_new_only_delete_question_noti_new_and_space_newest.json','r') as real_dict_file:
        real_dict = json.load(real_dict_file)
    # print("duongcc")
    normalized_input_sentence = compound2unicode(input_sentence)
    normalized_input_sentence = delete_extra_word(normalized_input_sentence,list_extra_word)
    
    result_entity_dict={}
    list_order_entity_name = map_intent_to_list_order_entity_name[intent]
    print(normalized_input_sentence)
    if 'time' in list_order_entity_name:
        for pattern_time in list_pattern_time:
            if re.findall(pattern_time,normalized_input_sentence)!=[]:
                # print("pattern_time :{0}".format(pattern_time))
                if 'time' not in result_entity_dict:
                    result_entity_dict['time'] = delete_last_space_list(re.findall(pattern_time,normalized_input_sentence))
                else:
                    result_entity_dict['time'].extend(delete_last_space_list(re.findall(pattern_time,normalized_input_sentence)))
                
                normalized_input_sentence = re.sub(pattern_time,' '.join(['✪']*(pattern_time.count(' ')+1)),normalized_input_sentence)
        # if 'time' in result_entity_dict:
        #     print(result_entity_dict['time'])
    if 'reward' in list_order_entity_name:
        print("hellllllllllllllllllo")
        for pattern_reward in list_pattern_reward:
            if re.findall(pattern_reward,normalized_input_sentence)!=[]:
                # print("pattern_reward :{0}".format(pattern_reward))
                if 'reward' not in result_entity_dict:
                    result_entity_dict['reward'] = delete_last_space_list(re.findall(pattern_reward,normalized_input_sentence))
                else:
                    result_entity_dict['reward'].extend(delete_last_space_list(re.findall(pattern_reward,normalized_input_sentence)))
                
                normalized_input_sentence = re.sub(pattern_reward,' '.join(['✪']*(pattern_reward.count(' ')+1)),normalized_input_sentence)
        # if 'reward' in result_entity_dict:
        #     print(result_entity_dict['reward'])
    matching_threshold = 0.0
    longest_common_length, end_common_index = None, None
    
    map_entity_name_to_threshold={}
    for entity_name in list_order_entity_name:
        if entity_name in ['time','address']:
            map_entity_name_to_threshold[entity_name]=1
        elif entity_name in ['name_activity','contact','joiner','holder','type_activity','name_place']:
            map_entity_name_to_threshold[entity_name]=2
        elif entity_name in ['works','reward']:
            map_entity_name_to_threshold[entity_name]=2
        elif entity_name in ['register']:
            map_entity_name_to_threshold[entity_name]=3


    ordered_real_dict = OrderedDict()
    for entity_name in map_intent_to_list_order_entity_name[intent]:
        ordered_real_dict[entity_name] = real_dict[entity_name]
    for entity_name, list_entity in ordered_real_dict.items():
        print(entity_name)
        list_entity = [preprocess_message(entity) for entity in list_entity]
        print("input sentence: {0}".format(normalized_input_sentence))
        if entity_name in ["works","register","reward"]:
            matching_threshold = 0.5
        elif entity_name == "joiner":
            matching_threshold = 0.5
        else:
            matching_threshold = 0.8
        # print("000. sentence:{0}".format(normalized_input_sentence))
        catch_entity_threshold_loop = 0
        while True:
            if catch_entity_threshold_loop > 5:
                break
            list_dict_longest_common_entity = find_entity_longest_common(normalized_input_sentence,list_entity,entity_name)
            # print(list_dict_longest_common_entity)
                #     [{'longest_common_entity_index': 0,
                #   'longest_common_length': 3,
                #   'end_common_index': 9}]
            

            ##find the most match longest common match (calculate by length of token match in sentence 
                                                                #/ length of entity )
                            ##{'greatest_match_entity_index':0,'longest_common_length':3,'end_common_index':9}
            if list_dict_longest_common_entity == []:
                break
            if list_dict_longest_common_entity[0]['longest_common_length'] < map_entity_name_to_threshold[entity_name] :
                break
            
            list_sentence_token = normalized_input_sentence.split(' ')
#             print("list_sentence_token :{0}".format(list_sentence_token))
            greatest_entity_index=None
            greatest_common_length = None
            greatest_end_common_index = None
            max_match_entity = 0.0
            # print("common entity :{0}".format(list_dict_longest_common_entity))
            for dict_longest_common_entity in list_dict_longest_common_entity:
#                 print("0. dict_longest_common_entity: {0}".format(dict_longest_common_entity))

#                     print("duong")
#                 print("0.1 entity: {0}".format(list_entity[dict_longest_common_entity['longest_common_entity_index']]))
                longest_common_entity_index = dict_longest_common_entity['longest_common_entity_index']
                longest_common_length = dict_longest_common_entity['longest_common_length']
                end_common_index = dict_longest_common_entity['end_common_index']
                
                list_sentence_token_match = list_sentence_token[end_common_index - longest_common_length+1:end_common_index+1]
                # if entity_name == "type_activity":
                #     if "ban chỉ huy" in normalized_input_sentence or "ban tổ chức" in normalized_input_sentence or "bch" in normalized_input_sentence or "btc" in normalized_input_sentence:
                #         continue
                    # #nếu chỉ là các câu inform 1 entity mà câu đó không phải là câu inform tên 1 hoạt động thì không cần xét
                    # if "inform" not in intent or "name_activity" in intent:
                    #     list_name_activity = ordered_real_dict['name_activity']
                    #     check_in_name = False
                    #     for name_activity in list_name_activity:
                    #         #nếu loại hoạt động nằm trọn trong bất kì 1 tên hoạt động 
                    #         # thì không lấy
                    #         if  name_activity.find(' '.join(list_sentence_token_match)) > 0:
                    #             check_in_name = True
                    #             break
                    #     if check_in_name == True:
                    #         continue
                
            #     if entity_name == "holder":
            #         # nếu holder mà trước đó có từ chỉ nơi chốn : ở, tại => không là holder mà là  
            #         # name_place
            #         if end_common_index - longest_common_length >= 0:
            #             if list_sentence_token[end_common_index - longest_common_length] in ["ở","tại","trước","sau","trong"]:
            #                 if 'name_place' in result_entity_dict:
            # #                     result_entity_dict[entity_name].append(list_entity[greatest_entity_index])
            #                     result_entity_dict['name_place'].append(' '.join(list_sentence_token_match))
            #                 else:
            # #                     result_entity_dict[entity_name] = [list_entity[greatest_entity_index]]
            #                     result_entity_dict['name_place'] = [' '.join(list_sentence_token_match)]
            #                 list_sentence_token[end_common_index - longest_common_length +1 :end_common_index +1] = ["✪"]*longest_common_length
            #                 normalized_input_sentence = ' '.join(list_sentence_token)
            #                 continue

                # if entity_name == "name_place":
                #     # nếu name_place mà trước đó có từ chỉ nơi chốn : ở, tại hoặc sau đó có "là địa điểm","là nơi","là chỗ"=>  
                #     # name_place
                #     if end_common_index - longest_common_length >= 0:
                #         if list_sentence_token[end_common_index - longest_common_length] not in ["ở","tại","trước","sau","trong"]:
                #             if end_common_index + 2 <= len(list_sentence_token):
                #                 if not (list_sentence_token[end_common_index+1] == "là" and list_sentence_token[end_common_index+2] in ["địa","nơi","chỗ"]):
                #                     if 'holder' in result_entity_dict:
                #     #                     result_entity_dict[entity_name].append(list_entity[greatest_entity_index])
                #                         result_entity_dict['holder'].append(' '.join(list_sentence_token_match))
                #                     else:
                #     #                     result_entity_dict[entity_name] = [list_entity[greatest_entity_index]]
                #                         result_entity_dict['holder'] = [' '.join(list_sentence_token_match)]
                #                     list_sentence_token[end_common_index - longest_common_length +1 :end_common_index +1] = ["✪"]*longest_common_length
                #                     normalized_input_sentence = ' '.join(list_sentence_token)
                #                     continue
                            

#                 print("2. list_sentence_token_match : {0}".format(list_sentence_token_match))
                list_temp_longest_entity_token = list_entity[longest_common_entity_index].split(' ')
#                 print("3. list_temp_longest_entity_token : {0}".format(list_temp_longest_entity_token))
                if entity_name in ["works","register","reward"]:
#                     print("list_temp_longest_entity_token :{0}".format(list_temp_longest_entity_token))
#                     print("list_sentence_token_match :{0}".format(list_sentence_token_match))
                    _,longest_common_length_entity,end_common_index_entity = lcs_length_ta(list_temp_longest_entity_token,list_sentence_token_match)
                    list_entity_token_match = list_temp_longest_entity_token[end_common_index_entity - longest_common_length_entity +1 :end_common_index_entity +1]
                    score = len(list_entity_token_match)/float(len(list_temp_longest_entity_token))
#                     print("list_entity_token_match: {0}".format(list_entity_token_match))
#                     print("list_temp_longest_entity_token:{0}".format(list_temp_longest_entity_token))
#                     print("score :{0}".format(score))
                    
                else:
                    score = len(list_sentence_token_match)/float(len(list_temp_longest_entity_token))
                if score > max_match_entity:
#                     max_match_entity = len(list_sentence_token_match)/float(len(list_temp_longest_entity_token))
                    max_match_entity = score
                    greatest_entity_index = longest_common_entity_index
                    greatest_common_length = longest_common_length
                    greatest_end_common_index = end_common_index
#             print(list_sentence_token)
#             print(greatest_common_length)
#             print(greatest_end_common_index)
#             print("longest_common_length: {0}".format(longest_common_length))
#             print("end_common_index: {0}".format(end_common_index))
#             print("1. greatest_common_length : {0}".format(greatest_common_length))
            # print(max_match_entity)
            if greatest_entity_index != None:
                print("2. greatest entity : {0}".format(list_entity[greatest_entity_index]))
#             print("2.1 greatest_end_common_index: {0}".format(greatest_end_common_index))
#             print("3. sentence match: {0}".format(list_sentence_token[greatest_end_common_index - greatest_common_length +1 :greatest_end_common_index +1]))
            
            if greatest_common_length != None:
                if greatest_common_length >= map_entity_name_to_threshold[entity_name] and max_match_entity > matching_threshold:
                    # if entity_name in ['name_activity','type_activity']:
                    #     result = list_entity[greatest_entity_index]
                    # else:
                    #     result = ' '.join(list_sentence_token[greatest_end_common_index - greatest_common_length +1 :greatest_end_common_index +1])
                    list_sentence_token_match = list_sentence_token[greatest_end_common_index - greatest_common_length +1 :greatest_end_common_index +1]
                    


                    ##########################LỌC CONFLICT ENTITY
                    #LỌC NAMEPLACE VÀ HOLDER
                    if entity_name == "name_place":
                        # nếu name_place mà trước đó có từ chỉ nơi chốn : ở, tại hoặc sau đó có "là địa điểm","là nơi","là chỗ"=>  
                        # name_place, không thì là holder
                        if "ở" in list_sentence_token_match or "tại" in list_sentence_token_match or "trước" in list_sentence_token_match or "sau" in list_sentence_token_match or "trong" in list_sentence_token_match:
                            if 'name_place' in result_entity_dict:
            #                     result_entity_dict[entity_name].append(list_entity[greatest_entity_index])
                                result_entity_dict['name_place'].append(' '.join(list_sentence_token_match))
                            else:
            #                     result_entity_dict[entity_name] = [list_entity[greatest_entity_index]]
                                result_entity_dict['name_place'] = [' '.join(list_sentence_token_match)]
                            list_sentence_token[greatest_end_common_index - greatest_common_length +1 :greatest_end_common_index +1] = ["✪"]*greatest_common_length
                            normalized_input_sentence = ' '.join(list_sentence_token)
                            continue


                        if greatest_end_common_index - greatest_common_length >= 0:
                            if list_sentence_token[greatest_end_common_index - greatest_common_length] not in ["ở","tại","trước","sau","trong"]:
                                if greatest_end_common_index + 2 < len(list_sentence_token):
                                    if not (list_sentence_token[greatest_end_common_index+1] == "là" and list_sentence_token[greatest_end_common_index+2] in ["địa","nơi","chỗ"]):
                                        if 'holder' in result_entity_dict:
                        #                     result_entity_dict[entity_name].append(list_entity[greatest_entity_index])
                                            result_entity_dict['holder'].append(' '.join(list_sentence_token_match))
                                        else:
                        #                     result_entity_dict[entity_name] = [list_entity[greatest_entity_index]]
                                            result_entity_dict['holder'] = [' '.join(list_sentence_token_match)]
                                        list_sentence_token[greatest_end_common_index - greatest_common_length +1 :greatest_end_common_index +1] = ["✪"]*greatest_common_length
                                        normalized_input_sentence = ' '.join(list_sentence_token)
                                        continue
                    
                    #LỌC NAME ACTIVITY VÀ JOINER (sinh viên và các hoạt động có chữ sinh viên)
                    if entity_name == "name_activity":
                        list_noti_joiner = []
                        if greatest_end_common_index + 4 < len(list_sentence_token):
                            list_noti_joiner = list_sentence_token[greatest_end_common_index+1 : greatest_end_common_index+5]
                        elif greatest_end_common_index + 3 < len(list_sentence_token):
                            list_noti_joiner = list_sentence_token[greatest_end_common_index+1 : greatest_end_common_index+4]
                        elif greatest_end_common_index + 2 < len(list_sentence_token):
                            list_noti_joiner = list_sentence_token[greatest_end_common_index+1 : greatest_end_common_index+3]
                        # nếu sau tên hoạt động là các cụm từ: (có) được tham gia, (có )được đi,(có) được tham dự,...
                        # thì là joiner chứ không phải name
                        if check_sublist(["được","đi"],list_noti_joiner) or  check_sublist(["được","tham"],list_noti_joiner):
                            if 'joiner' in result_entity_dict:
            #                     result_entity_dict[entity_name].append(list_entity[greatest_entity_index])
                                result_entity_dict['joiner'].append(' '.join(list_sentence_token_match))
                            else:
            #                     result_entity_dict[entity_name] = [list_entity[greatest_entity_index]]
                                result_entity_dict['joiner'] = [' '.join(list_sentence_token_match)]
                            list_sentence_token[greatest_end_common_index - greatest_common_length +1 :greatest_end_common_index +1] = ["✪"]*greatest_common_length
                            normalized_input_sentence = ' '.join(list_sentence_token)
                            continue
                    result = ' '.join(list_sentence_token[greatest_end_common_index - greatest_common_length +1 :greatest_end_common_index +1])
                    if entity_name in result_entity_dict:
    #                     result_entity_dict[entity_name].append(list_entity[greatest_entity_index])
                        result_entity_dict[entity_name].append(result)
                    else:
    #                     result_entity_dict[entity_name] = [list_entity[greatest_entity_index]]
                        result_entity_dict[entity_name] = [result]
    #                 list_sentence_token = list_sentence_token[:greatest_end_common_index - greatest_common_length + 1] + list_sentence_token[greatest_end_common_index +1 :]
                    list_sentence_token[greatest_end_common_index - greatest_common_length +1 :greatest_end_common_index +1] = ["✪"]*greatest_common_length
                    normalized_input_sentence = ' '.join(list_sentence_token)
            catch_entity_threshold_loop = catch_entity_threshold_loop + 1
            print("output sentence: {0}".format(normalized_input_sentence))
        # print("result entity dict : {0}".format(result_entity_dict))
        
        #sau khi bắt xong hết các name_activity thì xóa hết indicator của joiner: được tham gia,được đi,vv
        if entity_name == "name_activity":
            for indicator in list_joiner_indicator:
                normalized_input_sentence = normalized_input_sentence.replace(indicator,' '.join(['✪']*(indicator.count(' ')+1)))
    confirm_obj = None
    # print(result_entity_dict)
    # print(intent)
    if intent in result_entity_dict:
        # print("duongcc")
        value = result_entity_dict.pop(intent)
        # print(result_entity_dict)
        confirm_obj = {intent:value}
        # print("----------------------confirm obj")
        # print(confirm_obj)
    return result_entity_dict, confirm_obj

def process_message_to_user_request(message,state_tracker):
    print("----------------------------------message")
    print(message)
    confirm_obj = None
    if isinstance(message,str):
        intent , proba , processed_message = catch_intent(message)
        user_action = {}
        if intent not in ['hello','done','not intent','thanks','anything',"other"]:
            result_entity_dict, confirm_obj = find_all_entity(intent,processed_message)
            # print(result_entity_dict)
            # print(intent)
            user_action['intent'] = 'request'
            user_action['inform_slots'] = result_entity_dict
            user_action['request_slots'] = {intent:'UNK'}
        elif intent == 'not intent':
            #get agent request key for user to inform (not intent)
            # tránh những câu inform ngay từ ban đầu mà không biết intent
            if state_tracker.history != []:
                last_agent_action = state_tracker.history[-1]
                #nếu agent request 1 key thì user trả lời key đó
                if len(list(last_agent_action['request_slots'].keys())) > 0:
                    user_inform_key = list(last_agent_action['request_slots'].keys())[0]
                #nếu agent inform 1 key thì user cũng inform lại key đó
                elif len(list(last_agent_action['inform_slots'].keys())) > 0:
                    user_inform_key = list(last_agent_action['inform_slots'].keys())[0]
                    
                if len(list(last_agent_action['request_slots'].keys())) > 0 or len(list(last_agent_action['inform_slots'].keys())) > 0:
                    final_intent = user_inform_key + '_inform'
                else:
                    final_intent = 'not intent'
                result_entity_dict, confirm_obj = find_all_entity(final_intent,processed_message)
                user_action['intent'] = 'inform'
                user_action['inform_slots'] = result_entity_dict
                user_action['request_slots'] = {}
            else:
                user_action['intent'] = 'dont_know'
                user_action['inform_slots'] = {}
                user_action['request_slots'] = {}
        elif intent == 'anything':
            anything_key = None
            # lấy anything key từ noti 
            for entity_name, list_noti_anything in map_entity_name_to_list_noti_anything.items():
                check_match_anything_key = False
                for noti in list_noti_anything:
                    if noti in message:
                        anything_key = entity_name
                        check_match_anything_key = True
                        break
                if check_match_anything_key == False:
                    continue
                else:
                    break
            
            #nếu không phải là câu anything dạng có entity thì lấy từ agent request/inform key
            if anything_key == None: 
                last_agent_action = state_tracker.history[-1]
                if len(list(last_agent_action['request_slots'].keys())) > 0:
                    anything_key = list(last_agent_action['request_slots'].keys())[0]
                elif len(list(last_agent_action['inform_slots'].keys())) > 0:
                    anything_key = list(last_agent_action['inform_slots'].keys())[0]

            #nếu vẫn là None thì mặc định là lấy name_activity (để tránh crash server)
            if anything_key == None:
                anything_key = "name_activity"

            user_action['intent'] = 'inform'
            user_action['inform_slots'] = {anything_key:'anything'}
            user_action['request_slots'] = {}
        else:
            user_action['intent'] = intent
            user_action['inform_slots'] = {}
            user_action['request_slots'] = {}
    else:
        user_action = message
        ######chuẩn hóa
        if user_action["inform_slots"] != {}:
            for key in user_action["inform_slots"].keys():
                if isinstance(user_action["inform_slots"][key],list):
                    for i in range(len(user_action["inform_slots"][key])):
                        user_action["inform_slots"][key][i] = preprocess_message(user_action["inform_slots"][key][i])
    
    # print("-----------------------------user action")
    # print(user_action)
    if "time" in user_action.keys():
        if user_action["time"] != []:
            user_action["time"] = parse
    return user_action, confirm_obj

#TEST
if __name__ == '__main__':
    # #TESTCASE FILE
    # testcase_file= open("data/testcase_intent_recognizer.txt","r",encoding='utf-8')
    # output_test_file=open("data/output_intent_recognizer_1043_dictionary_replace_all_placeholder.txt","w+",encoding='utf-8')
    # testcases=testcase_file.readlines()
    # num_success_testcases=0
    # num_testcases=len(testcases)
    # i=0
    # for testcase in testcases:
    #     # #print(testcase)
    #     i+=1
    #     print(i)
    #     success=False
    #     testcase_without_enter=testcase.replace('\n', '').split('|')
    #     message=testcase_without_enter[0]
    #     intent_label=testcase_without_enter[1]
    #     intent_predict,proba=process_message(message)
    #     if intent_label==intent_predict:
    #         success=True
    #         num_success_testcases+=1
    #     output_test_file.write("Message: {0} \t Intent_label: {1} \t Intent_predict: {2} \t Probability: {3} \t Success: {4} \n".format(message,intent_label,intent_predict,proba,success))
    # output_test_file.write("Success rate: {0} %".format(100*float(num_success_testcases)/num_testcases))
    # output_test_file.close()
    # testcase_file.close()
    # print(catch_intent("cái gì cũng được"))
    # print(process_message_to_user_request("cho mình xin thông tin đăng kí mùa hè xanh khoa máy tính"))
    # print(find_all_entity("joiner","mình thích âm nhạc thì đi mùa hè xanh khoa máy tính được không",list_extra_word))
    # print(list_extra_word)
    # print(vocab.stoi["sẻ"])
    # state_tracker = StateTracker(database, constants)
    # process_message_to_user_request("cho mình hỏi đối tượng tham gia của hoạt động an toàn thực phẩm và an ninh lương thực",state_tracker)
    pass