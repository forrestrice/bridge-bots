import json
import pathlib
from pprint import pprint
from requests import get

token = open("../acbl_token.txt", "r").read()

headers = {"accept": "application/json", "Authorization": "Bearer " + token}
base_url = "https://api.acbl.org/v1/"
base_results = "../results/nabc/"


def list_nabcs():
    return api_request("tournament_query", {"category": "n", "page_size": 50})


def list_events(sanction_id):
    return join_all_pages_json("tournament/event_query", {"sanction": sanction_id, "page_size": 50})


def join_all_pages_json(path, params):
    all_data = []
    first_resp_json = api_request(path, params).json()
    all_data.extend(first_resp_json["data"])
    next_page = first_resp_json["next_page_url"]
    while next_page != None:
        resp_json = authorized_request(next_page).json()
        all_data.extend(resp_json["data"])
        next_page = resp_json["next_page_url"]
    return all_data


def api_request(path, params):
    return get(base_url + path, headers=headers, params=params)


def authorized_request(full_path):
    return get(full_path, headers=headers)


def fetch_nabc_event_lists():
    for tournament in list_nabcs().json()["data"]:
        print(tournament["name"], tournament["sanction"])
        my_tournament_name = "_".join(tournament["name"].split())
        results_path = pathlib.Path(base_results + my_tournament_name)
        results_path.mkdir(parents=True, exist_ok=True)
        all_events_path = results_path / "all_events.json"

        events = list_events(tournament["sanction"])
        print("writing", len(events), "events to all_events.json")
        with open(all_events_path, "w") as events_file:
            json.dump(events, events_file)


def fetch_event(event_json):
    event_resp = api_request("tournament/event",
                             {"event_code": event_json["event_code"],
                              "sanction": event_json["sanction"],
                              "with_sessions": 1})
                              #"full_monty": 1})
    pprint(event_resp.json())
    first_session = event_resp.json()["sessions"][0]
    session_json = api_request("tournament/session",
                {"event_code": event_json["event_code"],
                 "sanction": event_json["sanction"],
                 "session_number": first_session["session_number"],
                 "with_handrecord":1})
    print("\n")
    pprint(session_json.json())



fetch_event({"event_code": "21PO", "sanction": 1903017})
