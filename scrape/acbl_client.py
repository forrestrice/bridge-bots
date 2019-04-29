import json
import pathlib
from pprint import pprint
from requests import get





class AcblClient:
    def __init__(self, token_file):
        self.token = open("../acbl_token.txt", "r").read()
        self.auth_headers = {"accept": "application/json", "Authorization": "Bearer " + token}
        self.base_url = "https://api.acbl.org/v1/"

    def api_request(path, params):
        return get(self.base_url + path, headers=self.auth_headers, params=params)