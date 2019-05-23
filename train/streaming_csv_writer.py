import csv
import os
from typing import List


class StreamingCsvWriter:
    def __init__(self, file_path: str):
        if os.path.exists(file_path):
            os.remove(file_path)
        self.file = open(file_path, "w")
        self.writer = csv.writer(self.file)

    def write_row(self, row: List[str]):
        self.writer.writerow(row)

    def close(self):
        self.file.close()
