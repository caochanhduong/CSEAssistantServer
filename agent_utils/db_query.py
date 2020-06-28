from collections import defaultdict
from .dialogue_config import no_query_keys, usersim_default_key
import copy
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
import re
from pymongo import MongoClient
from datetime import *
import pytz

localTimezone = pytz.timezone('Asia/Saigon')
###### tạm thời để đây vì import từ constants báo lỗi no module name constants
list_map_key = ["works", "name_place", "address", "time"]

# app = Flask(__name__)
# CORS(app)
 
# app.config["MONGO_URI"] = "mongodb://caochanhduong:bikhungha1@ds261626.mlab.com:61626/activity?retryWrites=false"
# mongo = PyMongo(app)
 
 
def convert_from_unix_to_iso_format(input_unix_timestamp):
    return (datetime.fromtimestamp(input_unix_timestamp,localTimezone)).strftime('%d-%m-%Y %H:%M:%S')
# client = MongoClient()
# client = MongoClient('mongodb://caochanhduong:bikhungha1@ds261626.mlab.com:61626/activity?retryWrites=false')
# db = client.activity
class DBQuery:
    """Queries the database for the state tracker."""
 
    def __init__(self, database):
        """
        The constructor for DBQuery.
 
        Parameters:
            database (dict): The database in the format dict(long: dict)
        """
 
        self.db = database
        # {frozenset: {string: int}} A dict of dicts
        # self.cached_db_slot = defaultdict(dict)
        # {frozenset: {'#': {'slot': 'value'}}} A dict of dicts of dicts, a dict of DB sub-dicts
        # self.cached_db = defaultdict(dict)
        self.no_query = no_query_keys
        self.match_key = usersim_default_key
 
    def fill_inform_slot(self, inform_slot_to_fill, current_inform_slots):
        #TO TO :lấy kết quả VALUE có count max từ _count_slot_values, sau đó search lại trong db_results lấy giá trị đầu
	    # tiên có value giống với VALUE có count max (1 module) và trả về các object thỏa current inform (1 module) cũng như value max đó về
        """
        Given the current informs/constraints fill the informs that need to be filled with values from the database.
 
        Searches through the database to fill the inform slots with PLACEHOLDER with values that work given the current
        constraints of the current episode.
 
        Parameters:
            inform_slot_to_fill (dict): Inform slots to fill with values
            current_inform_slots (dict): Current inform slots with values from the StateTracker
 
        Returns:
            dict: inform_slot_to_fill filled with values
        """
        print("-----------------------------fill_inform_slot")
        # For this simple system only one inform slot should ever passed in
        assert len(inform_slot_to_fill) == 1
 
        key = list(inform_slot_to_fill.keys())[0]
 
        # This removes the inform we want to fill from the current informs if it is present in the current informs
        # so it can be re-queried
        current_informs = copy.deepcopy(current_inform_slots)
        current_informs.pop(key, None)
 
        # db_results is a dict of dict in the same exact format as the db, it is just a subset of the db
        db_results = self.get_db_results(current_informs)
 
        # filled_inform = {}
        # values_dict = self._count_slot_values(key, db_results)
        # if values_dict:
        #     # Get key with max value (ie slot value with highest count of available results)
        #     filled_inform[key] = list(max(values_dict, key=values_dict.get))
        # else:
        #     filled_inform[key] = 'no match available'
 
        # return filled_inform

        db_results_no_empty = {}
        
        if key != usersim_default_key:
            for i, data in db_results.items():
                if isinstance(data[key], list) and len(data[key]) > 0:
                    db_results_no_empty[i] = copy.deepcopy(data)
      
        filled_inform = {}
        db_results_search = {}
        current_results = []
        if db_results_no_empty:
            values_dict = self._count_slot_values(key, db_results_no_empty)
            db_results_search = db_results_no_empty
            # printprint("INFORM: filtered out, values_dict: {}".format(values_dict))
        else:
            values_dict = self._count_slot_values(key, db_results)
            db_results_search = db_results_no_empty
            # print("INFORM: can not filtered out, values_dict: {}".format(values_dict))

        if key == usersim_default_key:
            filled_inform[key] = list(db_results)[0]
        elif values_dict:
            # Get key with max value (ie slot value with highest count of available results)
            filled_inform[key] = list(max(values_dict, key=values_dict.get))
        else:
            filled_inform[key] = 'no match available'

        value_search = filled_inform[key]
        ## counter for limit 5 activities
        counter = 0
        if isinstance(value_search, list):
            for id in db_results_search.keys():
                if counter == 5:
                    break
                result_data = db_results_search[id]
                if result_data["time"] != []:
                    result_data["time"] = [convert_from_unix_to_iso_format(x) for x in result_data["time"]]
                if "time_works_place_address_mapping" in result_data and result_data["time_works_place_address_mapping"] is not None:
                    list_obj_map = result_data["time_works_place_address_mapping"]
                    list_result_obj_map = []
                    for obj_map in list_obj_map:
                        if obj_map["time"] not in [None,[]]:
                            obj_map["time"] = [convert_from_unix_to_iso_format(x) for x in obj_map["time"]]
                        list_result_obj_map.append(obj_map)
                result_data["time_works_place_address_mapping"] = list_obj_map
                current_results.append(result_data)
                counter = counter + 1

        return filled_inform, current_results
 
    def _count_slot_values(self, key, db_subdict):
        # TO DO: _count_slot_values: đối với các key bình thường thì đếm các value của từng key bình thường, còn đối với các 
    # key đặc biệt thì viết 1 module lấy current_inform ra, từ đó lấy ra được giá trị mà đi chung với điều kiện các key 
    # đặc biệt trong current inform rồi mới đếm (ví dụ dùng key works, name_place trong current_inform để xác định value 
    # của key time đi chung với works, name_place trong current_inform, sau đó đếm sự xuất hiện của từng value trong 
    # db_subdict) 
        """
        Return a dict of the different values and occurrences of each, given a key, from a sub-dict of database
 
        Parameters:
            key (string): The key to be counted
            db_subdict (dict): A sub-dict of the database
 
        Returns:
            dict: The values and their occurrences given the key
        """
        print("-----------------------------_count_slot_values")

        slot_values = defaultdict(int)  # init to 0
        for id in db_subdict.keys():
            current_option_dict = db_subdict[id]
            # If there is a match
            if key in current_option_dict.keys():
                slot_value = current_option_dict[key]
                tp_slot_value = tuple(slot_value)
                # This will add 1 to 0 if this is the first time this value has been encountered, or it will add 1
                # to whatever was already in there
                slot_values[tp_slot_value] += 1
        return slot_values

        # slot_values = defaultdict(int)  # init to 0
        # # print(slot_values)
        # for id in db_subdict.keys():
        #     current_option_dict = db_subdict[id]
        #     # If there is a match
        #     if key in current_option_dict.keys():
        #         slot_value = current_option_dict[key]
        #         if key in list_map_key:
        #             if "time_works_place_address_mapping" in current_option_dict and current_option_dict["time_works_place_address_mapping"] is not None:
        #                 list_obj_map = current_option_dict["time_works_place_address_mapping"]
        #                 for obj_map in list_obj_map:
        #                     if key in obj_map:
        #                         slot_value.extend(obj_map[key])
        #         # đồng bộ các value để không cần xét đến thứ tự xuất hiện
        #         slot_value = list(set(slot_value))

        #         # print(slot_value)
        #         if any(isinstance(i,list) for i in slot_value):
        #           slot_value = [value for sub_list in slot_value for value in sub_list]

        #         tp_slot_value = tuple(slot_value)
        #         # print(type(tp_slot_value))
        #         # This will add 1 to 0 if this is the first time this value has been encountered, or it will add 1
        #         # to whatever was already in there
        #         slot_values[tp_slot_value] += 1
        # return slot_values

 
    def get_db_results(self, constraints):
        # TO DO
        """
        Get all items in the database that fit the current constraints.
 
        Looks at each item in the database and if its slots contain all constraints and their values match then the item
        is added to the return dict.
 
        Parameters:
            constraints (dict): The current informs
 
        Returns:
            dict: The available items in the database
        """
        print("-----------------------------in get_db_results")

        # Filter non-queryable items and keys with the value 'anything' since those are inconsequential to the constraints
        new_constraints = {k: v for k, v in constraints.items() if k not in self.no_query and v != 'anything' and v != 'no match available'}
        # print("-----------------------------------DIEU KIEN")
        # print(new_constraints)
        tuple_new_constraint=copy.deepcopy(new_constraints)
        # print(tuple_new_constraint)
        inform_items ={k:tuple(v) for k,v in tuple_new_constraint.items()}.items()
        inform_items = frozenset(inform_items)
 
        # inform_items = frozenset(new_constraints.items())
        # cache_return = self.cached_db[inform_items]
 
        # if cache_return == None:
        #     # If it is none then no matches fit with the constraints so return an empty dict
        #     return {}
        # if it isnt empty then return what it is
        # if cache_return:
        #     return cache_return
        # else continue on
 
        available_options = {}
        regex_constraint = self.convert_to_regex_constraint(new_constraints)
        print("-----------------------------------DIEU KIEN")
        print(new_constraints)
        results = self.db.activities.find(regex_constraint)
        print("-----------------------------------KET QUA")
        
        for result in results:
            # print(result)
            #đổi từ object id sang string và dùng id đó làm key (thay vì dùng index của mảng để làm key vì không xác định đc index)
            result["_id"] = str(result["_id"])
            available_options.update({result['_id']:result})
            # self.cached_db[inform_items].update({result['_id']: result})
 
 
 
        # for id in self.database.keys():
        #     current_option_dict = self.database[id]
        #     # First check if that database item actually contains the inform keys
        #     # Note: this assumes that if a constraint is not found in the db item then that item is not a match
        #     if len(set(new_constraints.keys()) - set(self.database[id].keys())) == 0:
        #         match = True
        #         # Now check all the constraint values against the db values and if there is a mismatch don't store
        #         for k, v in new_constraints.items():
        #             if str(v).lower() != str(current_option_dict[k]).lower():
        #                 match = False
        #         if match:
        #             # Update cache
        #             self.cached_db[inform_items].update({id: current_option_dict})
        #             available_options.update({id: current_option_dict})
 
        # if nothing available then set the set of constraint items to none in cache
        # if not available_options:
        #     self.cached_db[inform_items] = None
 
        return available_options
    def get_db_results_for_slots(self, current_informs):
         #  TO DO:   + get_db_results_for_slots: viết 1 module để với mỗi key thì chỉ current inform còn các giá trị của chỉ key đó 
	# (ví dụ current inform có time, works ở ngoài và trong thì khi xét time chỉ xét time ở ngoài và trong, bỏ hết các giá trị 
	# của key works), còn với các key 
	# bình thường thì làm như bình thường (key:value)
        """
        Counts occurrences of each current inform slot (key and value) in the database items.
 
        For each item in the database and each current inform slot if that slot is in the database item (matches key
        and value) then increment the count for that key by 1.
 
        Parameters:
            current_informs (dict): The current informs/constraints
 
        Returns:
            dict: Each key in current_informs with the count of the number of matches for that key
        """
        print("-----------------------------get_db_results_for_slots")

        # The items (key, value) of the current informs are used as a key to the cached_db_slot
        # print()
        # print(type(self.cached_db_slot))
        tuple_current_informs=copy.deepcopy(current_informs)
        # print(tuple_current_informs)
        inform_items ={k:tuple(v) for k,v in tuple_current_informs.items()}.items()
        inform_items = frozenset(inform_items)
        # # A dict of the inform keys and their counts as stored (or not stored) in the cached_db_slot
        # cache_return = self.cached_db_slot[inform_items]
        temp_current_informs=copy.deepcopy(current_informs)
        # if cache_return:
        #     return cache_return
 
        # If it made it down here then a new query was made and it must add it to cached_db_slot and return it
        # Init all key values with 0
        db_results = {key: 0 for key in current_informs.keys()}
        db_results['matching_all_constraints'] = 0
 
        # for id in self.database.keys():
        # all_slots_match = True
        for CI_key, CI_value in current_informs.items():
        # Skip if a no query item and all_slots_match stays true
            if CI_key in self.no_query:
                continue
            # If anything all_slots_match stays true AND the specific key slot gets a +1
            if CI_value == 'anything':
                db_results[CI_key] = self.db.activities.count()
                del temp_current_informs[CI_key]
                continue
            db_results[CI_key]=self.db.activities.count(self.convert_to_regex_constraint({CI_key:CI_value}))
            # print(CI_key)
            # print(db_results[CI_key])
           
        # current_informs_constraint={k:v.lower() for k,v in temp_current_informs.items()}
        db_results['matching_all_constraints'] = self.db.activities.count(self.convert_to_regex_constraint(temp_current_informs))
       
        # # update cache (set the empty dict)
        # self.cached_db_slot[inform_items].update(db_results)
        # assert self.cached_db_slot[inform_items] == db_results
        return db_results
    # def convert_to_regex_constraint(self, constraints):
    #     list_and_out = []
    #     list_and_in = []
    #     ele_match_obj = {}
    #     list_or = []
    #     for k,values in constraints.items():
    #         list_pat = []
    #         for value in values:
    #             list_pat.append(re.compile(".*{0}.*".format(value)))
    #         # regex_constraint_dict[k] = {"$all":list_pat}
    #         if k not in ["works","name_place","address","time"]:
    #             list_and_out.append({k:{"$all":list_pat}})
    #         else:
    #             list_and_in.append({k:{"$all":list_pat}})
    #             ele_match_obj[k] = {"$all":list_pat}
    #     if list_and_in != [] :
    #         list_or = [{"$and":list_and_in},{"time_works_place_address_mapping":{"$all":[{"$elemMatch":ele_match_obj}]}}]
    #         list_and_out.append({"$or" : list_or})
    #     regex_constraint_dict = {"$and":list_and_out}
    #     return regex_constraint_dict

    def convert_to_regex_constraint(self, constraints):
        # TO DO :
        # + Chỗ convertregextoconstraint không cần phân biệt câu đầu tiên hay câu quá trình hội thoại, 
        # chỉ cần viết thêm 1 module lọc ra các key nào nằm ở cả key chung và trong object và đem các key đó 
        # đi query CÙNG NHAU ở ngoài và trong, 
	    # còn lại query theo ở ngoài
        print("-----------------------------convert_to_regex_constraint")

        list_and_out = []
        list_and_in = []
        ele_match_obj = {}
        list_or = []
        regex_constraint_dict = {}
        for k,values in constraints.items():
            if k not in list_map_key:
                list_pattern = []
                for value in values:
                    list_pattern.append(re.compile(".*{0}.*".format(value)))
                if list_pattern != []:
                    list_and_out.append({k: {"$all": list_pattern}})
            else:
                if k!="time":
                    for value in values:
                        list_and_in.append({
                            "$or" : [
                                        {
                                            k: {
                                                "$all": [re.compile(".*{0}.*".format(value))]
                                            }
                                        },
                                        {    
                                            "time_works_place_address_mapping": {
                                                "$all": [
                                                            {
                                                                "$elemMatch": {
                                                                        k: {
                                                                            "$all": [re.compile(".*{0}.*".format(value))]
                                                                        }
                                                                }
                                                            }
                                                        ]
                                            }
                                        }
                                    ]
                        })
                else:
                    if len(values) == 2: 
                        list_and_in.append({
                            "$or" : [
                                {
                                    k: { "$elemMatch" : {"$gte": values[0],"$lte": values[1]} }
                                },
                                {
                                    "time_works_place_address_mapping": {
                                                    "$all": [
                                                                {
                                                                    "$elemMatch": {
                                                                       k: { "$elemMatch" : {"$gte": values[0],"$lte": values[1]} }
                                                                    }
                                                                }
                                                            ]
                                                }
                                }
                            ]
                        })
                    if len(values) == 1: 
                        list_and_in.append({
                            "$or" : [
                                {
                                    k: { "$size": 1, "$elemMatch" : {"$gte": values[0]} }
                                },
                                {
                                    "time_works_place_address_mapping": {
                                                    "$all": [
                                                                {
                                                                    "$elemMatch": {
                                                                       k: { "$size": 1, "$elemMatch" : {"$gte": values[0]} }
                                                                    }
                                                                }
                                                            ]
                                                }
                                }
                            ]
                        })

        if list_and_in != []:
            list_and_out.append({"$and": list_and_in})

        if list_and_out != []:
            regex_constraint_dict = {"$and":list_and_out}
        return regex_constraint_dict

                


# from pymongo import MongoClient
# client = MongoClient('mongodb://caochanhduong:bikhungha1@ds261626.mlab.com:61626/activity?retryWrites=false')
# database = client.activity
# dbquery = DBQuery(database)
# print(dbquery.get_db_results({"name_activity":["mùa hè xanh"],"time":[1588870800]}))
# # print(dbquery.convert_to_regex_constraint({"name_activity":["đêm vui tất niên tết ấm áp"],"time":["10h","15/01/20"]}))