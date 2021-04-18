import csv
from pathlib import Path

from bs4 import BeautifulSoup

target_file_prefix = "/Users/frice/bridge/results"
target_file_suffix = ".html"
target_file_middle = "18"
target_file_path = Path(target_file_prefix, target_file_middle + target_file_suffix)

results_dicts = []
with open(target_file_path, "r") as results_file:
    results_contents = results_file.read()
    results_soup = BeautifulSoup(results_contents, "html.parser")
    results_table = results_soup.find("table", class_="body")
    results_rows = results_table.findAll("tr", class_="tourney")
    for row in results_rows:
        row_dict = {}
        results_cols = row.findAll("td")
        for col in results_cols:
            col_class = col.get("class")
            if col_class:
                first_class = col_class[0]
                if first_class in ["movie", "traveller"]:
                    col_text = col.find("a").get("href")
                elif first_class in ["score", "negscore"]:
                    col_text = col.getText()
                    if "%" in col_text:
                        first_class = "percentage"
                    else:
                        first_class = "score"
                else:
                    col_text = col.getText()
                row_dict[first_class] = col_text
        results_dicts.append(row_dict)


for result in results_dicts:
    print(result)

results_path = "/Users/frice/bridge/results/" + target_file_middle + ".csv"
with open(results_path, "w", newline="") as csvfile:
    fieldnames = ["handnum", "north", "south", "east", "west", "result", "score", "percentage", "movie", "traveller"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for record in results_dicts:
        writer.writerow(record)
