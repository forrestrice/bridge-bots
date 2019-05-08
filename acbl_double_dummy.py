import json
import os

HAND_RECORD_KEY = "handrecord"
'''

for dir_path, dir_names, file_names in os.walk("./results/acbl"):
    for file_name in file_names:
        if file_name.startswith("session"):
            with open(os.path.join(dir_path, file_name), "r") as session_file:
                session_json = json.load(session_file)
                if HAND_RECORD_KEY in session_json:
                    hand_records = session_json
'''

with open(
        "./results/acbl/Charleston_Swamp_Fox_Sectional_1903062/Stratified_Open_Pairs_1501/session1",
        "r") as session_file:
    session_json = json.load(session_file)
    if HAND_RECORD_KEY in session_json:
        hand_records = session_json[HAND_RECORD_KEY]
        first_record = hand_records[0]
        print(first_record)
