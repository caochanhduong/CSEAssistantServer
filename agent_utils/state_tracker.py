from .db_query import DBQuery
import numpy as np
from .utils import convert_list_to_dict
from .dialogue_config import all_intents, all_slots, usersim_default_key,agent_inform_slots,agent_request_slots, special_keys
import copy
import time


class StateTracker:
    """Tracks the state of the episode/conversation and prepares the state representation for the agent."""

    def __init__(self, database, constants):
        """
        The constructor of StateTracker.
        The constructor of StateTracker which creates a DB query object, creates necessary state rep. dicts, etc. and
        calls reset.
        Parameters:
            database (dict): The database with format dict(long: dict)
            constants (dict): Loaded constants in dict
        """

        self.db_helper = DBQuery(database)
        self.match_key = usersim_default_key
        self.intents_dict = convert_list_to_dict(all_intents)
        self.num_intents = len(all_intents)
        self.slots_dict = convert_list_to_dict(all_slots)
        self.num_slots = len(all_slots)
        self.max_round_num = constants['run']['max_round_num']
        self.none_state = np.zeros(self.get_state_size())
        self.reset()
        self.current_request_slots = []
        self.first_user_action = None
        self.agent_inform_stack = []

    def get_state_size(self):
        """Returns the state size of the state representation used by the agent."""

        return 2 * self.num_intents + 7 * self.num_slots + 3 + 13 + self.max_round_num

    def reset(self):
        """Resets current_informs, history and round_num."""

        self.current_informs = {}
        # A list of the dialogues (dicts) by the agent and user so far in the conversation
        self.history = []
        self.round_num = 0
        self.current_request_slots = []

    def print_history(self):
        """Helper function if you want to see the current history action by action."""

        for action in self.history:
            print(action)

    def get_state(self, done=False):
        """
        Returns the state representation as a numpy array which is fed into the agent's neural network.
        The state representation contains useful information for the agent about the current state of the conversation.
        Processes by the agent to be fed into the neural network. Ripe for experimentation and optimization.
        Parameters:
            done (bool): Indicates whether this is the last dialogue in the episode/conversation. Default: False
        Returns:
            numpy.array: A numpy array of shape (state size,)
        """

        # If done then fill state with zeros
        if done:
            return self.none_state

        user_action = self.history[-1]
        db_results_dict = self.db_helper.get_db_results_for_slots(self.current_informs)
        last_agent_action = self.history[-2] if len(self.history) > 1 else None
        # print("--------------------------user action")
        # print(user_action)       
        # print("--------------------------last agent action")
        # print(last_agent_action)        

        # Create one-hot of intents to represent the current user action
        user_act_rep = np.zeros((self.num_intents,))
        user_act_rep[self.intents_dict[user_action['intent']]] = 1.0

        # Create bag of inform slots representation to represent the current user action
        # TO DO :agent action là inform (inform key chung/riêng và các object thỏa điều kiện) thì trong ma trận agent_inform_slots_rep trong state  
        # tính luôn các key của các object thỏa điều kiện 
        user_inform_slots_rep = np.zeros((self.num_slots,))
        for key in user_action['inform_slots'].keys():
            list_match_obj = user_action['list_match_obj']
            user_inform_slots_rep[self.slots_dict[key]] = 1.0
            if list_match_obj not in [None,[]]:
                for special_key in special_keys:
                    user_inform_slots_rep[self.slots_dict[special_key]] = 1.0

        # Create bag of request slots representation to represent the current user action
        # EDIT: user request slots should maintain through out the episode
        user_request_slots_rep = np.zeros((self.num_slots,))
        # for key in user_action['request_slots'].keys():
        #     user_request_slots_rep[self.slots_dict[key]] = 1.0
        for key in self.current_request_slots:
            user_request_slots_rep[self.slots_dict[key]] = 1.0

        # Create bag of filled_in slots based on the current_slots
        current_slots_rep = np.zeros((self.num_slots,))
        # print("current inform: {}".format(self.current_informs))

        # TO DO : chỉ cập nhật các key trong current inform mà giá trị của nó khác rỗng (tức là không chỉ toàn chứa '', nếu là list rỗng thì vẫn tính là có giá trị)
        for key in self.current_informs:
            if key in special_keys:
                if self.current_informs[key][0] != '' or self.current_informs[key][1][0] != '':
                    current_slots_rep[self.slots_dict[key]] = 1.0     
            else:
                current_slots_rep[self.slots_dict[key]] = 1.0

        # Encode last agent intent
        agent_act_rep = np.zeros((self.num_intents,))
        if last_agent_action:
            agent_act_rep[self.intents_dict[last_agent_action['intent']]] = 1.0

        # Encode last agent inform slots
        agent_inform_slots_rep = np.zeros((self.num_slots,))
        # print(last_agent_action)

        # TO DO :agent action là inform (inform key chung/riêng và các object thỏa điều kiện) thì trong ma trận agent_inform_slots_rep trong state  
        # tính luôn các key của các object thỏa điều kiện 
        
        if last_agent_action:
            list_match_obj = last_agent_action['list_match_obj']
            for key in last_agent_action['inform_slots'].keys():
                if key in agent_inform_slots:
                    agent_inform_slots_rep[self.slots_dict[key]] = 1.0
            if list_match_obj not in [None,[]]:
                for special_key in special_keys:
                    agent_inform_slots_rep[self.slots_dict[special_key]] = 1.0
        # Encode last agent request slots
        agent_request_slots_rep = np.zeros((self.num_slots,))
        if last_agent_action:
            for key in last_agent_action['request_slots'].keys():
                if key in agent_request_slots:
                    agent_request_slots_rep[self.slots_dict[key]] = 1.0
        # print("------------------------agent_request_slots_rep")
        # print(agent_request_slots_rep)
        # Value representation of the round num
        turn_rep = np.zeros((1,)) + self.round_num / 5.

        # One-hot representation of the round num
        turn_onehot_rep = np.zeros((self.max_round_num,))
        turn_onehot_rep[self.round_num - 1] = 1.0

        # Representation of DB query results (scaled counts)
        kb_count_rep = np.zeros((self.num_slots + 1,)) + db_results_dict['matching_all_constraints'] / 100.
        for key in db_results_dict.keys():
            if key in self.slots_dict:
                kb_count_rep[self.slots_dict[key]] = db_results_dict[key] / 100.

        # Representation of DB query results (binary)
        kb_binary_rep = np.zeros((self.num_slots + 1,)) + np.sum(db_results_dict['matching_all_constraints'] > 0.)
        for key in db_results_dict.keys():
            if key in self.slots_dict:
                kb_binary_rep[self.slots_dict[key]] = np.sum(db_results_dict[key] > 0.)
        # print(kb_binary_rep)

        # represent current slot has value in db result
        db_binary_slot_rep = np.zeros((self.num_slots + 1,))
        db_results = self.db_helper.get_db_results(self.current_informs)
        if db_results:
            # Arbitrarily pick the first value of the dict
            key, data = list(db_results.items())[0]
            # print("size state: {} ".format(self.num_slots + 1))
            # print("first value:   {}".format(data))
            for slot, value in data.items():
                if slot in self.slots_dict and isinstance(value, list) and len(value) > 0:
                    # if slot not in self.current_request_slots:
                    db_binary_slot_rep[self.slots_dict[slot]] = 1.0
        
        # print("-------------------begin element")
        # print(user_act_rep)
        # print(user_inform_slots_rep)
        # print(user_request_slots_rep)
        # print(agent_act_rep)
        # print(agent_inform_slots_rep)
        # print(agent_request_slots_rep)
        # print("-------------------end element")
        # print("---------------------begin hstack")
        list_state = np.hstack(
            [user_act_rep, user_inform_slots_rep, user_request_slots_rep, agent_act_rep, agent_inform_slots_rep,
             agent_request_slots_rep]).flatten()
        # print(list_state[:6])
        # print(list_state[12:18])
        # print(list_state[18:30])
        # print(list_state[30:36])
        # print(list_state[36:48])
        # print(list_state[48:60])
        # print("---------------------end hstack")

        # print(np.hstack(
        #     [user_act_rep, user_inform_slots_rep, user_request_slots_rep, agent_act_rep, agent_inform_slots_rep,
        #      agent_request_slots_rep]))


        state_representation = np.hstack(
            [user_act_rep, user_inform_slots_rep, user_request_slots_rep, agent_act_rep, agent_inform_slots_rep,
             agent_request_slots_rep, current_slots_rep, turn_rep, turn_onehot_rep, kb_binary_rep,
             kb_count_rep,db_binary_slot_rep]).flatten()
        # print("---------------------------------------state")
        # print(state_representation)
        # time.sleep(0.5)
        return state_representation

    def update_state_agent(self, agent_action):
        """
        Updates the dialogue history with the agent's action and augments the agent's action.
        Takes an agent action and updates the history. Also augments the agent_action param with query information and
        any other necessary information.
        Parameters:
            agent_action (dict): The agent action of format dict('intent': string, 'inform_slots': dict,
                                 'request_slots': dict) and changed to dict('intent': '', 'inform_slots': {},
                                 'request_slots': {}, 'round': int, 'speaker': 'Agent')
        """

        if agent_action['intent'] == 'inform':
            assert agent_action['inform_slots']
            # print("intent: inform, current inform_slots: {}".format(self.current_informs))
            # print("current request slot: {}".format(self.current_request_slots))
            # TO DO : bổ sung thêm 1 key 'list_match_obj' vào agent action
            inform_slots, list_match_obj = self.db_helper.fill_inform_slot(agent_action['inform_slots'], self.current_informs)
            agent_action['inform_slots'] = inform_slots
            agent_action['list_match_obj'] = list_match_obj
            self.agent_inform_stack.append({'inform_slots': inform_slots, 'list_match_obj': list_match_obj})
            assert agent_action['inform_slots']
            key, value = list(agent_action['inform_slots'].items())[0]  # Only one
            assert key != 'match_found'
            assert value != 'PLACEHOLDER', 'KEY: {}'.format(key)
            #TO DO :nhận thông tin inform chung hoặc riêng vào dkien và object vào dkien
            # problem: update_state_agent đã append vào điều kiện rồi nhưng update_state_user lại append thêm phát nữa, tìm cách check đã tồn tại value trong điều kiện 
	# rồi để khỏi append
            ##### OLD 
            # if isinstance(value, tuple):
            #   self.current_informs[key] = list(value)
            # else:
            #   self.current_informs[key] = value

            #### NEW 
            for key, value in agent_action['inform_slots'].items():
                if key not in special_keys:
                    self.current_informs[key] = value
                else:
                    if 'list_obj_match' in list(agent_action.keys()): #là câu confirm inform  
                        list_obj_match = agent_action['list_obj_match']
                        is_general = agent_action['is_general'] #key để phân biệt value inform hiện tại là chung hay riêng
                        if is_general == True: #là value inform chung thì mới cần cập nhật, còn không thì không cần
                            if key not in self.current_informs.keys(): #chưa có thì khởi tạo
                                self.current_informs[key] = [value,[]]
                            else: #nếu có rồi thì gán thẳng
                                self.current_informs[key][0] = value
                        if list_obj_match != None:
                            for obj_match in list_obj_match:
                                for key_obj in obj_match.keys():
                                    if key_obj not in self.current_informs:
                                        self.current_informs[key] = ['',[obj_match[key_obj]]]
                                    else:
                                        self.current_informs[key][1].append(obj_match[key_obj])

        # If intent is match_found then fill the action informs with the matches informs (if there is a match)
        elif agent_action['intent'] == 'match_found':
            assert not agent_action['inform_slots'], 'Cannot inform and have intent of match found!'
            # print("intent: match found, current informs: {}".format(self.current_informs))

            db_results = self.db_helper.get_db_results(self.current_informs)
            if db_results:
                # Arbitrarily pick the first value of the dict


                # list_results = list(db_results.items())
                # index = 0
                # key, data = list_results[index]
                # while index < len(list_results) and isinstance(data[index][self.current_request_slots[0]],list) and len(data[index][self.current_request_slots[0]]) == 0:
                #     key, data = list(db_results.items())[index]
                #     index += 1
                db_results_no_empty = {}
                if self.current_request_slots[0] != usersim_default_key:
                    for key, data in db_results.items():
                        if isinstance(data[self.current_request_slots[0]], list) and len(data[self.current_request_slots[0]]) > 0:
                            db_results_no_empty[key] = copy.deepcopy(data)
                if db_results_no_empty:
                    # lấy key là kết quả đầu tiên của danh sách các hoạt động thỏa điều kiện, value là list các hoạt động thỏa dkien
                    key, data = list(db_results_no_empty.items())[0]
                    data = list(db_results_no_empty.values())
                    # print("MATCH FOUND: filtered only not empty data ")
                else:
                    # lấy key là kết quả đầu tiên của danh sách các hoạt động thỏa điều kiện, value là list các hoạt động thỏa dkien
                    key, data = list(db_results.items())[0]
                    data = list(db_results.values())
                # key, data = list(db_results.items())[0]
                agent_action['inform_slots'] = {key:copy.deepcopy(data)}
                agent_action['inform_slots'][self.match_key] = str(key)
            else:
                agent_action['inform_slots'][self.match_key] = 'no match available'
            self.current_informs[self.match_key] = agent_action['inform_slots'][self.match_key]
        agent_action.update({'round': self.round_num, 'speaker': 'Agent'})
        
        self.history.append(agent_action)
        print("------------------------------------history in update state agent")
        print(self.history)

    #fill giá trị value vào object trống tương ứng với key
    def fill_current_informs_object(self, key, value):
        is_enough_special_key = 0
        for key_inform, value_inform in self.current_informs.items():
            if key_inform in special_keys:
                is_enough_special_key += 1
        if is_enough_special_key < 4: #chưa đủ key đặc biệt, tức là lần đầu cập nhật
            for special_key in special_keys:
                if special_key != key: #các key khác thì khởi tạo
                    self.current_informs[special_key] = ['',['']]     
                else: #key đang xét thì cập nhật vào thông tin object riêng
                    self.current_informs[special_key][1].append(value)
        else: #đã đủ, duyệt tìm object trống vào fill vào
            for i in range(len(self.current_informs[key][1])):
                if self.current_informs[key][1][i] == '': #phát hiện object trống
                    self.current_informs[key][1][i] = value

    def checkExistValue(self, key, value):
        if key in self.current_informs.keys():
            if key in special_keys:
                if value == self.current_informs[key][0] or value in self.current_informs[key][1]:
                    return True
            else:
                if value == self.current_informs[key]:
                    return True
        return False
    
    def deleteInform(self, inform_obj): #-> replace with ''
        if self.checkExistInform(inform_obj):
            inform_slots =  inform_obj['inform_slots']
            list_match_obj = inform_obj['list_match_obj']
            for key in inform_slots.keys(): #delete current_informs từ value
                self.current_informs[key][0] = ''
            if list_match_obj not in [None,[]]:
                # danh sách các list key riêng mới (của 4 key works, name_place, address, time)
                list_new_works_obj = []
                list_new_address_obj = []
                list_new_name_place_obj = []
                list_new_time_obj = []

                #delete current_informs từ object bằng cách tạo mới xong gán lại
                for i in range(len(self.current_informs['works'][1])): 
                    has_match_obj = False
                    for match_obj in list_match_obj:
                        count_match = 0
                        for key in special_keys:
                            if match_obj[key] == self.current_informs[key][1][i]:
                                count_match += 1
                        if count_match == 4:
                            has_match_obj = True
                            break
                    if not has_match_obj:
                        list_new_works_obj.append(self.current_informs['works'][1][i])
                        list_new_address_obj.append(self.current_informs['address'][1][i])
                        list_new_name_place_obj.append(self.current_informs['name_place'][1][i])
                        list_new_time_obj.append(self.current_informs['time'][1][i])
                self.current_informs['works'][1] = list_new_works_obj
                self.current_informs['address'][1] = list_new_address_obj
                self.current_informs['name_place'][1] = list_new_name_place_obj
                self.current_informs['time'][1] = list_new_time_obj
                
                        

    def checkExistInform(self, inform_obj):
        inform_slots =  inform_obj['inform_slots']
        list_match_obj = inform_obj['list_match_obj']
        match_all = True
        # kiểm tra trong inform_slots
        for key in inform_slots.keys():
            if inform_slots[key] != '':
                if not self.checkExistValue(key, inform_slots[key]):
                    match_all = False
                    break
        # kiểm tra trong list_match_obj
        if match_all == True:
            if list_match_obj not in [None, []] :
                for key in special_keys: #nếu current inform không đủ key đặc biệt (nhưng lại có list_match_obj)
                    if key not in self.current_informs.keys():
                        match_all = False
                        break
                if match_all == True: #nếu đủ key đặc biệt thì loop qua kiểm tra các object trong list_match_obj có nằm trong current_infomrs không
                    for match_obj in list_match_obj:
                        match_all_key_in_obj = False
                        #số object hiện có trong current_informs
                        for i in range(len(self.current_informs['works'][1])): 
                            count_match = 0
                            for key in special_keys:
                                if match_obj[key] == self.current_informs[key][1][i]:
                                    count_match += 1
                            if count_match == 4:
                                match_all_key_in_obj = True
                                break
                        if match_all_key_in_obj == True:
                            continue
                        else:
                            match_all = False
                            break
        return match_all



    def update_state_user(self, user_action, first_user_action):
        """
        Updates the dialogue history with the user's action and augments the user's action.
        Takes a user action and updates the history. Also augments the user_action param with necessary information.
        Parameters:
            user_action (dict): The user action of format dict('intent': string, 'inform_slots': dict,
                                 'request_slots': dict) and changed to dict('intent': '', 'inform_slots': {},
                                 'request_slots': {}, 'round': int, 'speaker': 'User')
        """
        ##TO DO: CẬP NHẬT THEO RULE SAU :
        #########NẾU LÀ CÂU ĐẦU TIÊN NHẬP VÀO
        # + ner bắt được và intent đều không là key đặc biệt => như bình thường, tức là chỉ cập nhật 1 key với 1 value
		# + ner bắt được có 2 key đặc biệt trở lên, không quan tâm intent, đem bộ key đó đi query chung với nhau (thông tin chung hoặc trong object map)
		# + ner bắt được có 1 key đặc biệt, intent không là key đặc biệt => xem key đặc biệt đó là thông tin chung => như bình thường
		# + ner bắt được có 1 key đặc biệt, intent là 1 key đặc biệt khác, đem key đó đi query ở cả thông tin chung hoặc thông tin trong object map.
        #lấy đúng 1 cặp object 1 là chung 2 là riêng (không tính lẻ hoặc 2 cặp trở lên) (nếu chỉ tồn tại 1 key đặc biệt thì tính là thông tin chung, 
        # làm đường vẫn tính là works chung, khi nào là xây mét đường đầu tiên mới là works riêng)


        ######### NẾU LÀ CÂU user response lại inform:
		# +Key bình thường:
		# 	+ Làm như bth, tức là chỉ cập nhật 1 key với 1 value
		# +Key đặc biệt:
		# 	+ đồng ý: nhận thông tin inform chung hoặc riêng vào dkien và object vào dkien 
		# 	+ anything: tìm object còn trống và bỏ vào (là object có chứa ''), đồng thời bỏ vào thông tin chung 
        # nếu câu đầu tiên nhập vào ner có ít nhất 2 key đặc biệt hoặc 1 key đặc biệt nhưng intent cũng là key đặc biệt khác, 
        # còn không thì chỉ bỏ vào thông tin chung
		# 	+ từ chối hoặc chỉ nhận 1 thông tin inform (câu nhập): tìm object còn trống và bỏ vào, đồng thời bỏ vào 
        # thông tin chung nếu câu đầu tiên nhập vào ner có ít nhất 2 key đặc biệt hoặc 1 key đặc biệt nhưng intent cũng là 
        # key đặc biệt khác, còn không thì chỉ bỏ vào thông tin chung

        ######### NẾU LÀ CÂU user response lại request:
		# + Key bình thường:
		# 	+ Làm như bth, tức là chỉ cập nhật 1 key với 1 value
		# + Key đặc biệt:
		# 	+ anything: tìm object còn trống và bỏ vào, đồng thời bỏ vào thông tin chung nếu câu đầu tiên nhập vào ner 
        # có ít nhất 2 key đặc biệt hoặc 1 key đặc biệt nhưng intent cũng là key đặc biệt khác, còn không thì chỉ bỏ vào thông 
        # tin chung
		# 	+ nhận 1 thông tin inform (câu nhập): tìm object còn trống và bỏ vào, đồng thời bỏ vào thông tin chung nếu 
        # câu đầu tiên nhập vào ner có ít nhất 2 key đặc biệt hoặc 1 key đặc biệt nhưng intent cũng là key đặc biệt khác, 
        # còn không thì chỉ bỏ vào thông tin chung

        if user_action['intent'] == 'request': #câu đầu tiên (trước đó không có agent inform nên không cần xóa chỉ thêm)
            # Đếm key đặc biệt trong câu đầu tiên (gồm intent và ner bắt được)
            count_special = 0
            self.first_user_action = user_action
            if list(user_action['request_slots'].keys())[0] in special_keys:
                count_special = count_special + 1 
            for key, value in user_action['inform_slots'].items():
                # nếu là câu đầu tiên 
                if key in special_keys:
                    count_special = count_special + 1
            if count_special <= 1:
                for key, value in user_action['inform_slots'].items():
                    self.current_informs[key] = value
            else:
                for key, value in user_action['inform_slots'].items():
                    if key not in special_keys:
                        self.current_informs[key] = value
                    else:
                        self.current_informs[key] = [value,[]]
                        self.current_informs[1].append(value)
                for special_key in special_keys:
                    if special_key not in self.current_informs.keys():
                        self.current_informs[special_key] = ['',['']]
        else: #các câu inform sau
            last_agent_inform = self.agent_inform_stack.pop()
            user_inform_obj = {"inform_slots": user_action['inform_slots'],"list_obj_match": user_action["list_obj_match"]}
            if user_inform_obj != last_agent_inform: #nếu user_inform khác với agent_inform thì xóa agent inform cũ rồi thêm user inform mới vào
                if self.checkExistInform(last_agent_inform):
                    self.deleteInform(last_agent_inform)
                    ### thêm user inform vào
                    for key, value in user_action['inform_slots'].items():
                        if key not in special_keys:
                            self.current_informs[key] = value
                        else:
                            if 'list_obj_match' in list(user_action.keys()): #là câu confirm inform  
                                list_obj_match = user_action['list_obj_match']
                                is_general = user_action['is_general'] #key để phân biệt value inform hiện tại là chung hay riêng
                                if is_general == True: #là value inform chung thì mới cần cập nhật, còn không thì không cần
                                    if key not in self.current_informs.keys(): #chưa có thì khởi tạo
                                        self.current_informs[key] = [value,[]]
                                    else: #nếu có rồi thì gán thẳng
                                        self.current_informs[key][0] = value
                                if list_obj_match != None:
                                    for obj_match in list_obj_match:
                                        for key_obj in obj_match.keys():
                                            if key_obj not in self.current_informs:
                                                self.current_informs[key] = ['',[obj_match[key_obj]]]
                                            else:
                                                self.current_informs[key][1].append(obj_match[key_obj])
                            else: #là câu inform riêng lẻ
                                #đếm số key đặc biệt của câu đầu tiên để quyết định cập nhật ntn
                                count_special = 0
                                if list(self.first_user_action['request_slots'].keys())[0] in special_keys:
                                    count_special = count_special + 1 
                                for key_first, value_first in self.first_user_action['inform_slots'].items():
                                    # nếu là câu đầu tiên 
                                    if key_first in special_keys:
                                        count_special = count_special + 1
                                
                                if key not in self.current_informs:
                                    self.current_informs[key] = [value, []]
                                else:
                                    self.current_informs[key][0] = value 
                                                    
                                    #nếu chỉ có 1 key đặc biệt thì chỉ cập nhật thông tin chung
                                if count_special >= 2: #nếu có 2 key đặc biệt trở lên thì làm thêm module tìm object còn trống và bỏ vào
                                    self.fill_current_informs_object(key,value)
                                



        #current_request_slots giữ nguyên do request lúc nào cũng chỉ 1 thông tin .
        for key, value in user_action['request_slots'].items():
            if key not in self.current_request_slots:
                self.current_request_slots.append(key)
        user_action.update({'round': self.round_num, 'speaker': 'User'})
        self.history.append(user_action)
        self.round_num += 1
        print("---------------------------------------------history in update state user")
        print(self.history)