import json
import os
import pprint

sessions_with_records = 0
total_records = 0
HAND_RECORD_KEY = "handrecord"
for dir_path, dir_names, file_names in os.walk("../results/acbl"):
    for file_name in file_names:
        if file_name.startswith("session"):
            with open(os.path.join(dir_path, file_name), "r") as file:
                #print(file.name)
                session_json = json.load(file)
                #pprint.pprint(session_json)
                #hand_records = session_json["handrecord"]
                if HAND_RECORD_KEY in session_json:
                    sessions_with_records += 1
                    hand_count = len(session_json[HAND_RECORD_KEY])
                    total_records += hand_count
                    if hand_count:
                        print(file.name)
print("{} sessions have records with {} total records".format(sessions_with_records, total_records))