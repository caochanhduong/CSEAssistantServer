from .db_query import DBQuery
import numpy as np
from .utils import convert_list_to_dict
from .dialogue_config import all_intents, all_slots, usersim_default_key,agent_inform_slots,agent_request_slots
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
        self.current_results = []
        self.list_agent_request = []

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
        self.list_agent_request = []

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
        print("-------------------in getstate in state_tracker")
        # If done then fill state with zeros
        if done:
            return self.none_state

        user_action = self.history[-1]
        print("-------------------------current informs in getstate")
        print(self.current_informs)
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
        # TO DO :agent action là inform (inform key chung và các object thỏa điều kiện) thì trong ma trận agent_inform_slots_rep trong state  
        # tính luôn các key của các object thỏa điều kiện 
        user_inform_slots_rep = np.zeros((self.num_slots,))
        for key in user_action['inform_slots'].keys():
            user_inform_slots_rep[self.slots_dict[key]] = 1.0

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
            current_slots_rep[self.slots_dict[key]] = 1.0

        # Encode last agent intent
        agent_act_rep = np.zeros((self.num_intents,))
        if last_agent_action:
            agent_act_rep[self.intents_dict[last_agent_action['intent']]] = 1.0

        # Encode last agent inform slots
        agent_inform_slots_rep = np.zeros((self.num_slots,))
        # print(last_agent_action)

        # TO DO :agent action là inform (inform key chung và các object thỏa điều kiện) thì trong ma trận agent_inform_slots_rep trong state  
        # tính luôn các key của các object thỏa điều kiện 
        if last_agent_action:
            for key in last_agent_action['inform_slots'].keys():
                if key in agent_inform_slots:
                    agent_inform_slots_rep[self.slots_dict[key]] = 1.0

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
        print("-------------------in update_state_agent")

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
            print("-------------------in update_state_agent, agent inform")

            assert agent_action['inform_slots']
            # print("intent: inform, current inform_slots: {}".format(self.current_informs))
            # print("current request slot: {}".format(self.current_request_slots))

            inform_slots, self.current_results = self.db_helper.fill_inform_slot(agent_action['inform_slots'], self.current_informs)
            agent_action['inform_slots'] = inform_slots
            assert agent_action['inform_slots']
            key, value = list(agent_action['inform_slots'].items())[0]  # Only one
            assert key != 'match_found'
            assert value != 'PLACEHOLDER', 'KEY: {}'.format(key)
            if isinstance(value, tuple):
              self.current_informs[key] = list(value)
            else:
              self.current_informs[key] = value
        # If intent is match_found then fill the action informs with the matches informs (if there is a match)
        elif agent_action['intent'] == 'match_found':
            print("-------------------in update_state_agent, agent matchfound")

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
                    key, data = list(db_results_no_empty.items())[0]
                    data = list(db_results_no_empty.values())
                    # print("MATCH FOUND: filtered only not empty data ")
                else:
                    key, data = list(db_results.items())[0]
                                        #######??????????
                    data = list(db_results.values())
                # key, data = list(db_results.items())[0]
                agent_action['inform_slots'] = {key:copy.deepcopy(data)}
                agent_action['inform_slots'][self.match_key] = str(key)
            else:
                agent_action['inform_slots'][self.match_key] = 'no match available'
                ################?????????
            self.current_informs[self.match_key] = agent_action['inform_slots'][self.match_key]
        ## dùng để detect request lặp lại
        elif agent_action['intent'] == 'request':
            self.list_agent_request.append(agent_action)
        agent_action.update({'round': self.round_num, 'speaker': 'Agent'})
        
        self.history.append(agent_action)
        # print("------------------------------------history in update state agent")
        # print(self.history)

    def update_state_user(self, user_action):
        print("-------------------in update_state_user")

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
		# 	+ đồng ý: nhận thông tin inform chung vào dkien và object vào dkien 
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
        for key, value in user_action['inform_slots'].items():
            self.current_informs[key] = value
        print("current informs in update_state_user")
        print(self.current_informs)
        #current_request_slots giữ nguyên do request lúc nào cũng chỉ 1 thông tin .
        for key, value in user_action['request_slots'].items():
            if key not in self.current_request_slots:
                self.current_request_slots.append(key)
        user_action.update({'round': self.round_num, 'speaker': 'User'})
        self.history.append(user_action)
        self.round_num += 1
        # print("---------------------------------------------history in update state user")
        # print(self.history)