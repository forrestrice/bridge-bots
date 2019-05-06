import json
import logging
import pathlib
import time

from scrape.acbl_client import AcblClient

ALL_EVENTS_FILENAME = "all_events.json"
client = AcblClient("../acbl_token.txt")

logging.basicConfig(level=logging.INFO)
logging.getLogger("AcblClient").setLevel(logging.DEBUG)

# Download each session for the event
def process_event(event_json, tournament_dir_path, tournament_sanction):
    event_code = event_json["event_code"]
    name = "_".join(event_json["name"].split()).replace("/", "-") + "_" + event_code
    session_count = int(event_json["session_count"])
    logging.info("\tevent %s", name)
    event_dir_path = tournament_dir_path / name
    event_dir_path.mkdir(parents=False, exist_ok=True)
    for session_index in range(0, session_count):
        session_num = session_index + 1
        session_path = event_dir_path / f'session{session_num}'
        if session_path.exists():
            logging.info("\t\tskipping session %s", session_num)
        else:
            session_json = client.api_request_json("tournament/session",
                                    {"sanction": tournament_sanction,
                                     "event_code": event_code,
                                     "session_number": session_num,
                                     "with_handrecord": 1})

            with open(event_dir_path / f'session{session_num}', "w") as session_file:
                json.dump(session_json, session_file)
            #sleep here so that we only slow down if we are hitting the api
            time.sleep(0.3)


def process_tournament(tournament_json):
    sanction = tournament_json["sanction"]
    name = "_".join(tournament_json["name"].split()).replace("/", "-") + "_" + sanction

    logging.info("tournament %s", name)
    tournament_dir_path = results_dir_path / name
    tournament_dir_path.mkdir(parents=False, exist_ok=True)

    # Download all tournament events and store them in all_events.json
    all_events_path = tournament_dir_path / ALL_EVENTS_FILENAME
    if not all_events_path.exists():
        download_tournament_events(all_events_path, sanction)
    else:
        logging.info("%s already exists", ALL_EVENTS_FILENAME)

    with open(all_events_path, "r") as all_events_file:
        all_events = json.load(all_events_file)

    for event in all_events:
        process_event(event, tournament_dir_path, sanction)


def download_tournament_events(all_events_path, sanction):
    all_events_json = client.join_all_pages_json("tournament/event_query", {"sanction": sanction, "page_size": 50})
    with open(all_events_path, "w") as all_events_file:
        json.dump(all_events_json, all_events_file)



results_dir_path = pathlib.Path("../results/acbl/")
results_dir_path.mkdir(parents=True, exist_ok=True)
results_path = results_dir_path / "all_tournaments.json"
if not results_path.exists():

    all_tournaments = client.join_all_pages_json("tournament_query", {"page_size": 50, "start_date": "2018-01-01"})
    with open(results_path, "w") as tournament_file:
        json.dump(all_tournaments, tournament_file)
else:
    logging.info("%s already exists. Will not re-fetch", results_path)

logging.info("processing tournaments")

with open(results_path, "r") as tournament_file:
    all_tournaments = json.load(tournament_file)

exception_count = 0
for tournament in all_tournaments:
    try:
        process_tournament(tournament)
    except Exception as ex:
        exception_count += 1
        logging.error("error processing tournament %s: %s",tournament["name"], ex)

logging.info("encountered %s exceptions", exception_count)
exit(exception_count)

