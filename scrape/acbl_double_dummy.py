import json
import logging
import os
import pickle
from pprint import pprint

from bridge.double_dummy import DoubleDummyDeal

logging.basicConfig(level=logging.INFO)

HAND_RECORD_KEY = "handrecord"
processed_deals = set()
error_count = 0
duplicate_count = 0


with open("./results/double_dummy/all_deals.pickle", "wb") as dd_pickle_file:
    for dir_path, dir_names, file_names in os.walk("./results/acbl"):
        for file_name in file_names:
            if file_name.startswith("session"):
                with open(os.path.join(dir_path, file_name), "r") as session_file:
                    session_json = json.load(session_file)
                    if HAND_RECORD_KEY in session_json:
                        logging.info("processing file %s", session_file.name)
                        hand_records = session_json[HAND_RECORD_KEY]
                        for hand_record in hand_records:
                            if len(processed_deals) % 100 == 0:
                                logging.info("processed %s deals", len(processed_deals))
                            try:
                                ddd = DoubleDummyDeal.from_acbl_dict(hand_record)
                                binary_deal = ddd.deal.serialize()
                                if binary_deal in processed_deals:
                                    duplicate_count += 1
                                else:
                                    processed_deals.add(binary_deal)
                                    pickle.dump(ddd, dd_pickle_file)
                            except Exception as e:
                                error_count += 1
                                logging.error(e)

logging.info("Error count: %s", error_count)
logging.info("Duplicated deals: %s", duplicate_count)
logging.info("Unique Deals: %s", len(processed_deals))
