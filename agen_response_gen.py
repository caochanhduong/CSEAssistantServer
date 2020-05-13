import re
import random
from message_handler import check_match_sublist_and_substring
from constants import list_map_key

GREETING = [
    'Xin chào! Mình là CSE Assistant. Mình có thể giúp gì được bạn?',
    'Hi! CSE Assistant có thể giúp gì được bạn đây?'
]
DONE = [
    'Cảm ơn bạn, hy vọng bạn hài lòng với trải nghiệm vừa rồi! Bye ',
    'Rất vui được tư vấn cho bạn! Chào bạn nhé!',
    'Hy vọng bạn hài lòng với những gì mình tư vấn. Chào bạn!'
]
DONT_UNDERSTAND = [
    'Xin lỗi, mình không hiểu. Bạn nói cách khác dễ hiểu hơn được không?',
    'Mình không hiểu ý bạn lắm'
]

NOT_FOUND = [
    'Mình không tìm thấy hoạt động nào thỏa mãn các thông tin bạn đã cung cấp, vui lòng điều chỉnh lại giúp mình nhé!'
]
EMPTY_SLOT = [
    'Bài đăng về hoạt động thỏa mãn điều kiện của bạn nhưng nó không đề cập đến thông tin *request_slot*'
]
def get_greeting_statement():
    return random.choice(GREETING)

MATCH_FOUND = {
    'found': [
        "Thông tin *found_slot* chung bạn cần: *found_slot_instance*, bên dưới là hoạt động cụ thể chứa thông tin đó và một số hoạt động khác cũng thỏa điều kiện bạn đưa ra"
    ],
    'not_found': [
        "Mình không tìm thấy bài đăng chứa thông tin *found_slot* mà bạn cần, bạn xem lại các thông tin đã cung cấp dưới đây và điều chỉnh lại giúp mình nhé!"
    ],
    'found_activity' :[
        "Dưới đây là các hoạt động bạn cần tìm."
    ]
}
REQUEST = {}
REQUEST['name_activity'] = [
    'Bạn cho mình xin *name_activity* bạn muốn được không',
    'Bạn định hỏi về *name_activity* nào?',
    'Mời bạn cung cấp *name_activity*, mình sẽ tìm cho bạn!'
]
REQUEST['type_activity'] = [
    'Bạn định hỏi về *type_activity* nào? (tình nguyện, hội thảo, ngày hội, ...)',
    '*type_activity* là gì vậy bạn?'
]
REQUEST['holder'] = [
    'Hoạt động này do đơn vị nào tổ chức vậy bạn?',
    'Bạn biết *holder* của hoạt động này là ai không?'
]
REQUEST['time'] = [
    'Bạn nhớ cụ thể *time* diễn ra hoạt động này không?',
    'Cho mình xin thông tin về *time* diễn ra hoạt động này được không?'
]
REQUEST['address'] = [
    'Hoạt động này diễn ra ở *address* nào bạn?',
    'cụ thể *address* là gì bạn nhớ không?'
]
REQUEST['name_place'] = [
    'Tại *name_place* nào bạn?',
    'Cho mình xin cụ thể *name_place* với!'
]
REQUEST['works'] = [
    'Bạn liệt kê một số *works* trong hoạt động được không?',
    'Bạn kể ra một vài *works* trong đó được không?'
]
INFORM = {}
INFORM['name_activity'] = [
    'có phải bạn muốn hỏi về hoạt động *name_activity_instance* không?',
    '*name_activity_instance* có phải là *name_activity* bạn muốn tìm không?'
]
INFORM['type_activity'] = [
    'Bạn có muốn mình tìm với *type_activity* là *type_activity_instance* không?',
    '*type_activity* là *type_activity_instance* đúng không bạn?'
]
INFORM['holder'] = [
    'Hoạt động này do *holder_instance* tổ chức đúng không nhỉ?',
    '*holder* là *holder_instance*, đúng không bạn?'
]
INFORM['time'] = [
    '*time* mình tìm được với thông tin bạn đã cung cấp: *time_instance*',
    '*time* diễn ra là: *time_instance* đúng không bạn?'
]
INFORM['address'] = [
    'Với thông tin bạn đã cung cấp thì mình thấy hoạt động này diễn ra ở *address_instance*',
    'Tại *address* là *address_instance* đúng không bạn?'
]
INFORM['name_place'] = [
    'Tại *name_place_instance* phải không bạn?',
    'hoạt động diễn ra ở *name_place_instance* đúng không?'
]
INFORM['works'] = [
    'Theo thông tin mình tìm được thì *works* trong hoạt động là: *works_instance*',
    'Tham gia hoạt động này thì thường sẽ làm các công việc như *works_instance*'
]
INFORM['reward'] = [
    'Tham gia hoạt động sẽ được *reward_instance*'
]
INFORM['contact'] = [
    'bạn có thể liên hệ *contact_instance* nhé'
]
INFORM['register'] = [
    'Để đăng ký bạn có thể làm như sau: *register_instance*'
]
INFORM['joiner'] = [
    '*joiner* là *joiner_instance* phải không?'
]
INFORM['activity'] = [
    'Đây là hoạt động mình tìm được với yêu cầu hiện tại của bạn: *activity_instance*'
]

AGENT_REQUEST_OBJECT = {
    "name_activity": "tên hoạt động",
    "type_activity": "loại hoạt động",
    "holder": "ban tổ chức",
    "time": "thời gian",
    "address": "địa chỉ",
    "name_place": "tên địa điểm",
    "works": "công việc"
}

AGENT_INFORM_OBJECT = {
    "name_activity": "tên hoạt động",
    "type_activity": "loại hoạt động",
    "holder": "ban tổ chức",
    "time": "thời gian",
    "address": "địa chỉ",
    "name_place": "tên địa điểm",
    "works": "các công việc trong hoạt động",
    "reward": "lợi ích",
    "contact": "liên hệ",
    "register": "đăng ký",
    "joiner": "đối tượng tham gia",
    "activity": "hoạt động"
}


def response_craft(agent_action, state_tracker, confirm_obj, isGreeting=False):
    if isGreeting:
        return random.choice(GREETING)
    agent_intent = agent_action['intent']
    if agent_intent == "inform":
        # TO DO : trường hợp agent inform, bổ sung thêm response thêm các object thỏa điều kiện (chỉ cần lấy ra từ trong agent action)
        inform_slot = list(agent_action['inform_slots'].keys())[0]
        list_obj_map_match = agent_action['list_obj_match']
        if agent_action['inform_slots'][inform_slot] == 'no match available':
            return random.choice(NOT_FOUND)

        sentence_pattern = random.choice(INFORM[inform_slot])
        sentence = sentence_pattern.replace("*{}*".format(inform_slot), AGENT_INFORM_OBJECT[inform_slot])
        if len(agent_action['inform_slots'][inform_slot]) > 1:
            inform_value = ",\n".join(agent_action['inform_slots'][inform_slot])
            sentence = sentence.replace("*{}_instance*".format(inform_slot), "\n\"{}\"".format(inform_value))
        elif len(agent_action['inform_slots'][inform_slot]) == 1:
            inform_value = agent_action['inform_slots'][inform_slot][0]
            sentence = sentence.replace("*{}_instance*".format(inform_slot), "\"{}\"".format(inform_value))
        else:
            sentence_pattern = random.choice(EMPTY_SLOT)
            sentence = sentence_pattern.replace("*request_slot*", inform_slot)
        # print(sentence_pattern)
        if inform_slot in list_map_key:
            if list_obj_map_match not in [None, []]:
                response_obj += "Trong đó các công việc cụ thể sẽ là (kèm theo thời gian, địa điểm, địa chỉ):\n"
                for obj_map_match in list_obj_map_match:
                    response_obj += "************************************************* \n"
                    for key in list_map_key:
                        response_obj += "+ {0} : {1} \n".format(AGENT_INFORM_OBJECT[key], ', '.join(obj_map_match[key]))
    elif agent_intent == "request":
        request_slot = list(agent_action['request_slots'].keys())[0]
        sentence_pattern = random.choice(REQUEST[request_slot])
        sentence = sentence_pattern.replace("*{}*".format(request_slot), AGENT_REQUEST_OBJECT[request_slot])
        # print(sentence_pattern)
    elif agent_intent == "done":
        return random.choice(DONE)
    elif agent_intent == "match_found":
        # TO DO :trường hợp agent matchfound, lúc lấy ra kết quả đầu tiên thỏa thì get lại current_inform từ state tracker để tìm các list match obj 
	# thỏa điều kiện, đồng thời response lại câu cho user luôn (không giống với inform chỉ cần lấy ra và response câu), inform value mà phải trả về 
    # cho user bây giờ phải viết 1 module sử dụng current_inform để tìm ra value cần inform cho user, lúc confirm thì so value này với confirm_obj và kết luận
        assert len(state_tracker.current_request_slots) > 0
        inform_slot = state_tracker.current_request_slots[0]
        if agent_action['inform_slots']['activity'] == "no match available":
            sentence_pattern = random.choice(MATCH_FOUND['not_found'])
            sentence = sentence_pattern.replace("*found_slot*", AGENT_INFORM_OBJECT[inform_slot])
        else:
            key = agent_action['inform_slots']['activity']
            #????????
            first_result_data = agent_action['inform_slots'][key][0]

            # #nếu là câu hỏi intent confirm thì cần response lại mà match hay không
            # print("-------------------------------inform slot :{}".format(inform_slot))
            print("---------------------------------confirm obj: {}".format(confirm_obj))
            response_match = ''
            if confirm_obj != None:
                if inform_slot not in list_map_key:
                    # không cần sửa
                    check_match = check_match_sublist_and_substring(confirm_obj[inform_slot],first_result_data[inform_slot])
                else: #nếu là 4 key map
                    # TO DO: chỉnh lại 	
                    # + problem: tìm cách dựa vào current inform để lấy ra value inform phù hợp trong trường hợp matchfound (không thể dùng first user action),
                    # tuy nhiên lúc cập nhật nhiều object vào current inform thì giờ nó bị lộn xộn (chứa nhiều obj) nên chắc phải dùng first user action
                    # MỚI : lúc lấy value inform chỉ cần dùng first user action để lọc ra từ first_result_data
                    # lúc lấy các obj thỏa điều kiện có thể dùng first_result_data không ????? CHƯA ỔN !!!!!!!!!!!! LỠ ĐÂU GIỮA CHỪNG USER INFORM THÊM THÔNG TIN VÀO OBJ
                    ############### CHƯA ỔN !!!!!!!!!!!! LỠ ĐÂU GIỮA CHỪNG USER INFORM THÊM THÔNG TIN VÀO OBJ

                    ####NEW: nếu count <= 1 thì lấy thông tin chung bình thường , ngược lại tìm cách chọn ra từ curent inform những giá trị để lọc , tuy nhiên khó 
                    # khăn là nó vừa chứa giá trị inform từ agent (lẻ, trong hoặc ngoài) và giá trị inform từ user (cập nhật trong và ngoài)

                    #### lấy ra value inform
                    first_user_action = state_tracker.first_user_action

                    count_special = 0
                    if list(first_user_action['request_slots'].keys())[0] in special_keys:
                        count_special = count_special + 1 
                    for key, value in first_user_action['inform_slots'].items():
                        # nếu là câu đầu tiên 
                        if key in special_keys:
                            count_special = count_special + 1
                    
                    ## nếu ít hơn 1 key đặc biệt (kể cả intent và ner) thì lấy từ thông tin chung
                    if count_special <= 1:
                        check_match = check_match_sublist_and_substring(confirm_obj[inform_slot],first_result_data[inform_slot])
                        inform_value_list = first_result_data[inform_slot]
                    else: ## nếu nhiều hơn thì xét cả thông tin chung và riêng
                        match_all_condition_first_user_action = True
                        ###kiểm tra thông tin chung
                        for key in first_user_action['request_slots'].keys():
                            if key in special_keys and not check_match_sublist_and_substring(first_user_action['inform_slots'][key], first_result_data[key]):
                                match_all_condition_first_user_action = False
                                break
                        if match_all_condition_first_user_action: #
                            check_match = check_match_sublist_and_substring(confirm_obj[inform_slot],first_result_data[inform_slot])
                            inform_value_list = first_result_data[inform_slot]
                        else: # kiểm tra thông tin riêng
                            if "time_works_place_address_mapping" in first_result_data and first_result_data["time_works_place_address_mapping"] not in [None,[]]:
                                list_obj_map = first_result_data["time_works_place_address_mapping"]
                                for obj_map in list_obj_map:
                                    check_match_obj = True
                                    for key in first_user_action['request_slots'].keys():
                                        if key in special_keys and not check_match_sublist_and_substring(first_user_action['inform_slots'][key], obj_map[key]):
                                            check_match_obj = False
                                            break
                                    if check_match_obj == True:
                                        check_match = check_match_sublist_and_substring(confirm_obj[inform_slot],obj_map[inform_slot])
                                        inform_value_list = obj_map[inform_slot]
                                        break

                value_match = ''
                if len(confirm_obj[inform_slot]) > 1:
                    value_match = ',\n'.join(confirm_obj[inform_slot])
                else:
                    value_match = confirm_obj[inform_slot][0]
                if check_match:
                    response_match = "\n \n Đúng rồi! {0} là {1}".format(AGENT_INFORM_OBJECT[inform_slot],value_match)
                else:
                    response_match = "\n \n Sai rồi! {0} không là {1}".format(AGENT_INFORM_OBJECT[inform_slot],value_match)
            if inform_slot != "activity":
                sentence_pattern = random.choice(MATCH_FOUND['found'])
                sentence = sentence_pattern.replace("*found_slot*", AGENT_INFORM_OBJECT[inform_slot])
                if len(inform_value_list) > 1:
                    inform_value = ",\n".join(inform_value_list)
                    sentence = sentence.replace("*found_slot_instance*", "\n\"{}\"".format(inform_value))
                elif len(inform_value_list) == 1:
                    inform_value = inform_value_list[0]
                    sentence = sentence.replace("*found_slot_instance*", "\"{}\"".format(inform_value))
                else: #slot mà user request của kết quả trả về là list rỗng  
                    # inform_value = "không có thông tin này"
                    sentence = EMPTY_SLOT[0].replace("*request_slot*",AGENT_INFORM_OBJECT[inform_slot])
            else:
                sentence = random.choice(MATCH_FOUND['found_activity'])



            ### chỗ này cần chỉnh lại vì lỡ đâu user inform thêm thông tin 
            list_obj_map_match = []
            response_obj = ''
            if "time_works_place_address_mapping" in first_result_data and first_result_data["time_works_place_address_mapping"] not in [None,[]] and inform_slot in list_map_key:
                current_informs = state_tracker.current_informs
                print("--------------------------current informs : {0}".format(current_informs))
                list_obj_map = first_result_data["time_works_place_address_mapping"]
                for obj_map in list_obj_map:
                    check_match = True
                    for map_key in list_map_key:
                        if map_key in current_informs:
                            if current_informs[map_key] != "anything" and not check_match_sublist_and_substring(current_informs[map_key],obj_map[map_key]):
                                check_match = False
                                break
                    if check_match and obj_map not in list_obj_map_match:
                        list_obj_map_match.append(obj_map)

            if list_obj_map_match != []:
                response_obj += "Cụ thể các công việc thỏa điều kiện bạn cung cấp sẽ là (kèm theo thời gian, địa điểm, địa chỉ):\n"
                for obj_map_match in list_obj_map_match:
                    response_obj += "************************************************* \n"
                    for key in list_map_key:
                        response_obj += "+ {0} : {1} \n".format(AGENT_INFORM_OBJECT[key], ', '.join(obj_map_match[key]))


            # print(sentence)
            sentence += "\n" + response_obj + response_match
            print("-----------------------------match sentence")
            print(sentence)
    return sentence

# print(response_craft({'intent': 'inform', 'inform_slots': {'holder': ['đội công tác xã hội']}, 'request_slots': {}, 'round': 1, 'speaker': 'Agent'}))