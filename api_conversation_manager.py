#!/usr/bin/env python
# coding: utf-8

# In[13]:


# chạy mining nhớ exclude intent
from data_utils.check_question import check_question
from information_extractor import extract_information
from intent_regconizer_activity import extract_and_get_intent
import time
import random
import numpy as np
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from temp_agent_action_gen import *
from constants import *
import message_handler 
from agen_response_gen import *
from dqn_agent import DQNAgent
from agent_utils.state_tracker import StateTracker
from keras import backend as K
from pymongo import MongoClient
import importlib

importlib.reload(message_handler)
from message_handler import *


app = Flask(__name__)
CORS(app)

################## {state_tracker_id:(state_tracker,confirm_obj),}
StateTracker_Container = dict()

app.config["MONGO_URI"] = "mongodb://caochanhduong:bikhungha1@ds261626.mlab.com:61626/activity?retryWrites=false"
mongo = PyMongo(app)


CONSTANT_FILE_PATH = 'constants.json'
with open(CONSTANT_FILE_PATH) as f:
    constants = json.load(f)


# ##############DATABASE FILE
# file_path_dict = constants['db_file_paths']
# DATABASE_FILE_PATH = file_path_dict['database']

# database= json.load(open(DATABASE_FILE_PATH,encoding='utf-8'))

####################DATABASE REMOTE
# client = MongoClient()
client = MongoClient('mongodb://caochanhduong:bikhungha1@ds261626.mlab.com:61626/activity?retryWrites=false')
database = client.activity


# state_tracker = StateTracker(database, constants)
# dqn_agent = DQNAgent(state_tracker.get_state_size(), constants)    
def msg(code, mess=None):
    if code == 200 and mess is None:
        return jsonify({"code": 200, "value": True})
    else:
        return jsonify({"code": code, "message": mess}), code

def get_new_id():
    while (True):
        _id = str(random.randint(100000, 999999))
        if _id not in StateTracker_Container.keys():
            return _id

def process_conversation_POST(state_tracker_id, message):
    state_tracker = None
    
    if state_tracker_id in StateTracker_Container.keys():
        state_tracker = StateTracker_Container[state_tracker_id][0]
        confirm_obj = StateTracker_Container[state_tracker_id][1]
    else:
        # print("---------------------------------in model")
        state_tracker = StateTracker(database, constants)
        confirm_obj = None
        StateTracker_Container[state_tracker_id] = (state_tracker, confirm_obj)
        
        
    user_action, new_confirm_obj = process_message_to_user_request(message,state_tracker)
    print("-----------------------------------user action")
    print(user_action)
    #nếu là câu request mới của user thì reset state tracker và cho confirm về lại None
    if user_action['request_slots'] != {}:
        state_tracker.reset()
        confirm_obj = None
    #nếu có câu confirm request mới thì ghi đè
    if new_confirm_obj != None:
        confirm_obj = new_confirm_obj
    if user_action['intent'] not in ["hello","other","done","dont_know"] :
        dqn_agent = DQNAgent(state_tracker.get_state_size(), constants)    
        agent_act = get_agent_response(state_tracker, dqn_agent, user_action)
        StateTracker_Container[state_tracker_id] = (state_tracker,confirm_obj)
        agent_message = response_craft(agent_act, state_tracker,confirm_obj)
    else:
        # to prevent key error
        agent_act = {'intent':user_action['intent'],'request_slots':[],'inform_slots':[]}
        agent_message = random.choice(response_to_user_free_style[user_action['intent']])
        #nếu là done thì reset và cho confirm về None
        if user_action['intent'] == "done":
            state_tracker.reset()
            StateTracker_Container[state_tracker_id] = (state_tracker,None)
    return agent_message,agent_act
# In[14]:
@app.route('/')
def index():
    return """<h1>rLeT BOT</h1>"""


@app.errorhandler(404)
def url_error(e):
    print("---------------------")
    return msg(404, "cao chánh dương")


@app.errorhandler(500)
def server_error(e):
    return msg(500, "SERVER ERROR")


@app.route('/api/LT-conversation-manager', methods=['POST'])
def post_api():
    input_data = request.get_json(force=True)
    print(input_data)
    if "message" not in input_data.keys():
        return msg(400, "Message cannot be None")
    else:
        message = input_data["message"]
        result, probability = extract_and_get_intent(message)
        probability = probability.tolist()
    return jsonify({"code": 200, "message": result, "probability": probability})

@app.route('/api/cse-assistant-conversation-manager', methods=['POST'])
def post_api_cse_assistant():
    input_data = request.json
    
    if "message" not in input_data.keys(): 
        return msg(400, "Message cannot be None")
    else:
        message = input_data["message"]
    print("-------------------------message")
    print(message)
    if "state_tracker_id" not in input_data.keys(): 
        state_tracker_id = get_new_id()
    else:
        state_tracker_id = input_data["state_tracker_id"]
    # print(StateTracker_Container)
    K.clear_session()
    current_informs = 'null'
    agent_message , agent_action = process_conversation_POST(state_tracker_id, message)
    if agent_action['intent'] in ["match_found","inform"]:
        current_informs = StateTracker_Container[state_tracker_id][0].current_informs
    
    # ###########begin modify
    if agent_action['intent'] == "match_found":
        if agent_action['inform_slots']['activity'] != "no match available":
            activity_key = agent_action['inform_slots']['activity']
            first_result_data = agent_action['inform_slots'][activity_key][0]
            if first_result_data["time"] != []:
                first_result_data["time"] = [convert_from_unix_to_iso_format(x) for x in first_result_data["time"]]
            if "time_works_place_address_mapping" in first_result_data and first_result_data["time_works_place_address_mapping"] not in [None,[]]:
                list_obj_map = first_result_data["time_works_place_address_mapping"]
                list_result_obj_map = []
                for obj_map in list_obj_map:
                    if obj_map["time"] not in [None,[]]:
                        obj_map["time"] = [convert_from_unix_to_iso_format(x) for x in obj_map["time"]]
                    list_result_obj_map.append(obj_map)
            first_result_data["time_works_place_address_mapping"] = list_obj_map
            agent_action['inform_slots'][activity_key][0] = first_result_data

    ################end modify
    K.clear_session()
    return jsonify({"code": 200, "message": agent_message,"state_tracker_id":state_tracker_id,"agent_action":agent_action,"current_informs":current_informs})

@app.route('/api/cse-assistant-conversation-manager/reset-state-tracker', methods=['POST'])
def post_api_cse_assistant_reset_state_tracker():
    input_data = request.json
    
    if "state_tracker_id" not in input_data.keys(): 
        return msg(400, "Message cannot be None")
    else:
        state_tracker_id = input_data["state_tracker_id"]
    # print("-------------------------state_tracker_id")
    # print(state_tracker_id)
    # # if "state_tracker_id" not in input_data.keys(): 
    # #     state_tracker_id = get_new_id()
    # # else:
    # #     state_tracker_id = input_data["state_tracker_id"]
    # print(StateTracker_Container)
    K.clear_session()

    if state_tracker_id in StateTracker_Container:
        state_tracker = StateTracker_Container[state_tracker_id][0]
        state_tracker.reset()
        StateTracker_Container[state_tracker_id] = (state_tracker,None)
        message = "success"
        code = 200
    else:
        message = "fail"
        code = 404
    K.clear_session()
    return jsonify({"code": code, "message": message,"state_tracker_id":state_tracker_id})


@app.route('/api/LT-conversation-manager/extract-information', methods=['POST'])
def post_api_extract_information():
    input_data = request.json
    print(input_data)
    if "message" not in input_data.keys():
        return msg(400, "Message cannot be None")
    else:
        message = input_data["message"]
        print(message)
        emails, phones, names = extract_information(message)
        print(emails)
        print(phones)
    return jsonify({"code": 200, "emails": emails, "phones": phones, "names": names})


@app.route("/api/LT-conversation-manager/messages", methods=['POST'])
def user_profile():
    input_data = request.json
    print(input_data)
    if "message" not in input_data.keys():
        return msg(400, "Message cannot be None")
    if "intent" not in input_data.keys():
        return msg(400, "Intent cannot be None")
    user_id = input_data["user_id"]
    message = input_data["message"]
    intent = input_data["intent"]
    is_correct = input_data["is_correct"]

    mongo.db.messages.insert_one(
        {"user_id": user_id, "message": message, "intent": intent, "is_correct": is_correct})
        
    return jsonify({"code": 200, "message": "insert successed!"})

@app.route('/api/LT-conversation-manager/classify-message', methods=['POST'])
def post_api_classify_message():
    input_data = request.get_json(force=True)
    print(input_data)
    if "message" not in input_data.keys():
        return msg(400, "Message cannot be None")
    else:
        message = input_data["message"]
        # if check_question(message):
        #     result, probability = extract_and_get_intent(message)
        # else:
        #     result=""
        result, probability = extract_and_get_intent(message)
    return jsonify({"is_question": check_question(message), "intent": result})


if __name__ == '__main__':
    app.run()


# In[ ]:
