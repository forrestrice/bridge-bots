import json
import logging
import pathlib
import time
from pprint import pprint
from requests import get





class AcblClient:
    def __init__(self, token_file):
        self.token = open(token_file, "r").read()
        self.auth_headers = {"accept": "application/json", "Authorization": "Bearer " + self.token}
        self.base_url = "https://api.acbl.org/v1/"
        self.logger = logging.getLogger("AcblClient")

    def api_request_json(self, path, params):
        try:
            return get(self.base_url + path, headers=self.auth_headers, params=params).json()
        except Exception as ex:
            self.logger.error("Exception fetching path=%s, params=%s: %s", path, params, ex)
            raise ex


    def _authorized_request_json(self, full_path):
        return get(full_path, headers=self.auth_headers).json()

    def join_all_pages_json(self, path, params):
        all_data = []
        first_resp_json = self.api_request_json(path, params)
        all_data.extend(first_resp_json["data"])
        next_page = first_resp_json["next_page_url"]
        while next_page != None:
            success = False
            for i in range(0,3):
                try:
                    self.logger.debug("next_page: %s", next_page)
                    time.sleep(0.5)
                    resp_json = self._authorized_request_json(next_page)
                    all_data.extend(resp_json["data"])
                    next_page = resp_json["next_page_url"]
                    success = True
                    break
                except Exception as e:
                    self.logger.error(e)
                    continue
            if not success:
                raise Exception("failed after 3 retries")

        return all_data
