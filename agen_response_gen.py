import re
import random
from message_handler import check_match_sublist_and_substring, check_match_time, convert_from_unix_to_iso_format
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
    'Mình không hiểu ý bạn lắm. Bạn nhập câu khác giúp mình nhen.',
    'Chà! Bạn nói gì mình không hiểu lắm. Bạn nhập lại câu khác nhen.'
]

NOT_FOUND = [
    'Mình không tìm thấy hoạt động nào thỏa mãn các thông tin bạn đã cung cấp, vui lòng điều chỉnh lại giúp mình nhé!',
    'Không có hoạt động nào thỏa mãn thông tin bạn đưa ra, bạn điều chỉnh lại giúp mình nhé!'
]
EMPTY_SLOT = [
    'Bài đăng về hoạt động thỏa mãn điều kiện của bạn nhưng nó không đề cập đến thông tin *request_slot*',
    'Mình tìm được một số hoạt động thỏa yêu cầu của bạn nhưng lại không đề cập đến thông tin *request_slot*'
]
def get_greeting_statement():
    return random.choice(GREETING)

MATCH_FOUND = {
    'found': [
        "Thông tin *found_slot* bạn cần: *found_slot_instance*, bên dưới là hoạt động cụ thể chứa thông tin đó và một số hoạt động khác cũng thỏa điều kiện bạn đưa ra",
        "Đây là thông tin *found_slot* bạn đang tìm: *found_slot_instance*, hoạt động cụ thể chứa thông tin đó và một số hoạt động khác cũng thỏa điều kiện bạn đưa ra được hiển thị ở bên dưới",
        "Mình tìm được rồi đây!Thông tin *found_slot* bạn đang tìm nè: *found_slot_instance*, hoạt động cụ thể chứa thông tin đó và một số hoạt động khác cũng thỏa điều kiện bạn đưa ra được hiển thị ở bên dưới"
    ],
    'not_found': [
        "Xin lỗi bạn! Mình không tìm thấy hoạt động nào chứa thông tin *found_slot* mà bạn cần, bạn xem lại các thông tin đã cung cấp dưới đây và điều chỉnh lại giúp mình nhé!",
        "Xin lỗi nhé! Không có hoạt động nào chứa thông tin *found_slot* mà bạn cung cấp, bạn điều chỉnh lại giúp mình các thông tin đã cung cấp nhé!",
        "Xin lỗi! Thông tin *found_slot* mà bạn cung cấp không nằm trong hoạt động nào, bạn điều chỉnh lại giúp mình các thông tin nhé!"
    ],
    'found_activity' :[
        "Dưới đây là các hoạt động bạn cần tìm.",
        "Đây là các hoạt động bạn đang tìm kiếm.",
        "Mình đã tìm được các hoạt động bạn cần"
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
    'Tại *name_place* nào vậy bạn?',
    'Cho mình xin cụ thể tên *name_place* với!'
]

REQUEST['works'] = [
    'Bạn liệt kê một số *works* trong hoạt động được không?',
    'Bạn kể ra một vài *works* trong đó được không?'
]

REQUEST_REPEAT = [
    'Thông tin *request_key* bạn nhập vào chưa rõ ràng, bạn cung cấp lại giúp mình thông tin này nhé! ',
    'Rất tiếc, thông tin *request_key* bạn nhập vào mình vẫn chưa rõ, bạn vui lòng cung cấp lại thông tin này giúp mình nhé!',
    'Bạn cung cấp lại thông tin *request_key* giúp mình với nhé!'
]
INFORM = {}
INFORM['name_activity'] = [
    'có phải bạn muốn hỏi về hoạt động "*name_activity_instance*" không?',
    '"*name_activity_instance*" có phải là *name_activity* bạn muốn tìm không?'
]
INFORM['type_activity'] = [
    'Bạn có muốn mình tìm với *type_activity* là "*type_activity_instance*" không?',
    '*type_activity* là "*type_activity_instance*" đúng không bạn?'
]
INFORM['holder'] = [
    'Hoạt động này do *holder_instance* tổ chức đúng không nhỉ?',
    '*holder* là *holder_instance*, đúng không bạn?'
]
INFORM['time_single'] = [
    '*time* mình tìm được với thông tin bạn đã cung cấp: *time_instance*',
    '*time* diễn ra là: *time_instance* đúng không bạn?'
]
INFORM['time_double'] = [
    '*time* mình tìm được với thông tin bạn đã cung cấp: bắt đầu vào lúc *time_start_instance* và kết thúc vào lúc *time_end_instance*',
    '*time* diễn ra là: bắt đầu vào lúc *time_start_instance* và kết thúc vào lúc *time_end_instance* đúng không bạn?'
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
    'Tham gia hoạt động sẽ được *reward_instance* ?',
    'Lợi ích khi bạn tham gia hoạt động sẽ là: *reward_instance*'
]
INFORM['contact'] = [
    'bạn có thể liên hệ *contact_instance* nhé',
    'thông tin liên hệ có thể là *contact_instance*'
]
INFORM['register'] = [
    'Để đăng ký bạn có thể làm như sau: *register_instance*',
    'Thông tin để bạn đăng ký có thể là: *register_instance*'

]
INFORM['joiner'] = [
    '*joiner* là *joiner_instance* phải không?',
    '*joiner* có phải là *joiner_instance* không?'
]
INFORM['activity'] = [
    'Đây là hoạt động mình tìm được với yêu cầu hiện tại của bạn: *activity_instance*',
    'Hiện tại mình tìm được một số hoạt động thỏa yêu cầu: *activity_instance*'
]

AGENT_REQUEST_OBJECT = {
    "name_activity": "tên hoạt động",
    "type_activity": "loại hoạt động",
    "holder": "ban tổ chức",
    "time": "thời gian",
    "address": "địa chỉ",
    "name_place": "địa điểm",
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


def response_craft(agent_action, state_tracker, confirm_obj,isGreeting=False):
    sentence_pattern = None 
    if isGreeting:
        return random.choice(GREETING)
    agent_intent = agent_action['intent']
    if agent_intent == "inform":
        # TO DO : trường hợp agent inform, bổ sung thêm response thêm các object thỏa điều kiện (chỉ cần lấy ra từ trong agent action)
        inform_slot = list(agent_action['inform_slots'].keys())[0]
        if agent_action['inform_slots'][inform_slot] == 'no match available':
            return random.choice(NOT_FOUND)

        if inform_slot != "time":
            sentence_pattern = random.choice(INFORM[inform_slot])
        else:
            if len(agent_action['inform_slots'][inform_slot]) > 1: # == 2
                sentence_pattern = random.choice(INFORM[inform_slot + '_double'])
            elif len(agent_action['inform_slots'][inform_slot]) == 1:
                sentence_pattern = random.choice(INFORM[inform_slot + '_single'])
            else:
                sentence_pattern = random.choice(EMPTY_SLOT)

        sentence = sentence_pattern.replace("*{}*".format(inform_slot), AGENT_INFORM_OBJECT[inform_slot])


        if len(agent_action['inform_slots'][inform_slot]) > 1:
            if inform_slot != "time":
                inform_value = ",\n".join(agent_action['inform_slots'][inform_slot])
                sentence = sentence.replace("*{}_instance*".format(inform_slot), "\n\"{}\"".format(inform_value))
            else:
                inform_value = [convert_from_unix_to_iso_format(x) for x in agent_action['inform_slots'][inform_slot]]
                sentence = sentence.replace("*{}_start_instance*".format(inform_slot), "\n\"{}\"".format(inform_value[0]))
                sentence = sentence.replace("*{}_end_instance*".format(inform_slot), "\n\"{}\"".format(inform_value[1]))
        elif len(agent_action['inform_slots'][inform_slot]) == 1:
            if inform_slot != "time":
                inform_value = agent_action['inform_slots'][inform_slot][0]
            else:
                inform_value = convert_from_unix_to_iso_format(agent_action['inform_slots'][inform_slot][0])
            sentence = sentence.replace("*{}_instance*".format(inform_slot), "\"{}\"".format(inform_value))
        else:
            sentence_pattern = random.choice(EMPTY_SLOT)
            sentence = sentence_pattern.replace("*request_slot*", AGENT_INFORM_OBJECT[inform_slot])
        # print(sentence_pattern)
    elif agent_intent == "request":
        request_slot = list(agent_action['request_slots'].keys())[0]
        check_request_repeat = False
        list_agent_request = state_tracker.list_agent_request
        for i in range(len(list_agent_request) - 1):
            history_request_slot = list(list_agent_request[i]['request_slots'].keys())[0]
            if history_request_slot == request_slot:
                check_request_repeat = True
        if check_request_repeat:
            sentence_pattern = random.choice(REQUEST_REPEAT)
            sentence = sentence_pattern.replace('*request_key*', AGENT_REQUEST_OBJECT[request_slot])
        else:
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
            # TO DO: chỉnh lại 	
            # tìm cách dựa vào current inform để lấy ra value inform phù hợp trong trường hợp matchfound 
            # nếu count <= 1 thì lấy thông tin chung bình thường , ngược lại tìm cách chọn ra từ curent inform những giá trị để lọc , tuy nhiên khó 
            # khăn là nó vừa chứa giá trị inform từ agent (lẻ, trong hoặc ngoài) và giá trị inform từ user (cập nhật trong và ngoài)

            key = agent_action['inform_slots']['activity']
            first_result_data = agent_action['inform_slots'][key][0]

            # #nếu là câu hỏi intent confirm thì cần response lại mà match hay không
            # print("-------------------------------inform slot :{}".format(inform_slot))
            print("---------------------------------confirm obj: {}".format(confirm_obj))
            response_match = ''

          
            if confirm_obj != None:
                if inform_slot not in list_map_key:
                    check_match = check_match_sublist_and_substring(confirm_obj[inform_slot],first_result_data[inform_slot])
                else: #nếu là 4 key map
                    if inform_slot != "time":
                        check_match = check_match_sublist_and_substring(confirm_obj[inform_slot],first_result_data[inform_slot])
                    else:
                        check_match = check_match_time(confirm_obj[inform_slot],first_result_data[inform_slot])
                    # neu chưa match với key chung thì tìm trong map
                    if not check_match:
                        if "time_works_place_address_mapping" in first_result_data and first_result_data["time_works_place_address_mapping"] not in [None,[]]:
                            list_obj_map = first_result_data["time_works_place_address_mapping"]
                            for obj_map in list_obj_map:
                                if inform_slot in obj_map:
                                    if inform_slot != "time":
                                        if check_match_sublist_and_substring(confirm_obj[inform_slot],obj_map[inform_slot]):
                                            check_match = True
                                            break
                                    else:
                                        if check_match_time(confirm_obj[inform_slot],obj_map[inform_slot]):
                                            check_match = True
                                            break

                value_match = ''
                if len(confirm_obj[inform_slot]) > 1:
                    if inform_slot != "time":
                        value_match = ',\n'.join(confirm_obj[inform_slot])
                    else:
                        value_match = 'nằm trong khoảng bắt đầu từ {0} và kết thúc lúc {1}'.format(convert_from_unix_to_iso_format(confirm_obj[inform_slot][0]),convert_from_unix_to_iso_format(confirm_obj[inform_slot][1]))
                else:
                    if inform_slot != "time":
                        value_match = confirm_obj[inform_slot][0]
                    else:
                        value_match = "sau thời gian " + convert_from_unix_to_iso_format(confirm_obj[inform_slot][0])
                if check_match:
                    # if inform_slot != "time":
                    response_match = "\n \n Đúng rồi! {0} là {1}".format(AGENT_INFORM_OBJECT[inform_slot],value_match)
                    # else:
                    #     response_match = "\n \n Đúng rồi! {0} là nằm trong khoảng {1}".format(AGENT_INFORM_OBJECT[inform_slot],value_match)
                else:
                    # if inform_slot != "time":
                    response_match = "\n \n Sai rồi! {0} không phải là {1}".format(AGENT_INFORM_OBJECT[inform_slot],value_match)
                    # else:
                        # response_match = "\n \n Sai rồi! {0} không phải là nằm trong khoảng {1}".format(AGENT_INFORM_OBJECT[inform_slot],value_match)


            if inform_slot != "activity":
                sentence_pattern = random.choice(MATCH_FOUND['found'])
                sentence = sentence_pattern.replace("*found_slot*", AGENT_INFORM_OBJECT[inform_slot])
                if len(first_result_data[inform_slot]) > 1:
                    if inform_slot != "time":
                        inform_value = ",\n".join(first_result_data[inform_slot])
                    else:
                        inform_value = "bắt đầu từ {0} và kết thúc lúc {1}".format(convert_from_unix_to_iso_format(first_result_data[inform_slot][0]),convert_from_unix_to_iso_format(first_result_data[inform_slot][1]))
                    sentence = sentence.replace("*found_slot_instance*", "\n\"{}\"".format(inform_value))
                elif len(first_result_data[inform_slot]) == 1:
                    if inform_slot != "time":
                        inform_value = first_result_data[inform_slot][0]
                    else:
                        inform_value = convert_from_unix_to_iso_format(first_result_data[inform_slot][0])
                    sentence = sentence.replace("*found_slot_instance*", "\"{}\"".format(inform_value))
                else: #slot mà user request của kết quả trả về là list rỗng  
                    # inform_value = "không có thông tin này"
                    sentence = EMPTY_SLOT[0].replace("*request_slot*",AGENT_INFORM_OBJECT[inform_slot])
            else:
                sentence = random.choice(MATCH_FOUND['found_activity'])

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
                            if map_key != "time":
                                if current_informs[map_key] != "anything" and not check_match_sublist_and_substring(current_informs[map_key],obj_map[map_key]):
                                    check_match = False
                                    break
                            else:
                                if current_informs[map_key] != "anything" and not check_match_time(current_informs[map_key],obj_map[map_key]):
                                    check_match = False
                                    break
                                
                    if check_match and obj_map not in list_obj_map_match:
                        list_obj_map_match.append(obj_map)

            if list_obj_map_match != []:
                response_obj += "Cụ thể các công việc thỏa điều kiện bạn cung cấp sẽ là (kèm theo thời gian, địa điểm, địa chỉ):\n"
                for obj_map_match in list_obj_map_match:
                    response_obj += "************************************************* \n"
                    for key in list_map_key:
                        if key != "time":
                            value_obj_inform = ', '.join(obj_map_match[key])
                        else:
                            if len(obj_map_match[key]) == 1:
                                value_obj_inform = convert_from_unix_to_iso_format(obj_map_match[key][0])
                            elif len(obj_map_match[key]) > 1:
                                value_obj_inform = "bắt đầu từ {0} và kết thúc lúc {1}".format(convert_from_unix_to_iso_format(obj_map_match[key][0]),convert_from_unix_to_iso_format(obj_map_match[key][1]))
                            else:
                                value_obj_inform = ''
                        response_obj += "+ {0} : {1} \n".format(AGENT_INFORM_OBJECT[key],value_obj_inform)
            # print(sentence)
            sentence += "\n" + response_obj + response_match
            print("-----------------------------match sentence")
            print(sentence)
    return sentence

# print(response_craft({'intent': 'inform', 'inform_slots': {'holder': ['đội công tác xã hội']}, 'request_slots': {}, 'round': 1, 'speaker': 'Agent'}))