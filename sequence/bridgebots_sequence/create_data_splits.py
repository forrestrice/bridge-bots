import logging
import pickle
import random
from pathlib import Path
from typing import List, Tuple

from bridgebots import DealRecord


def create_data_splits(
    source_pickle: Path,
    save_dir: Path,
    splits: Tuple[Tuple[str, float]] = (("train", 0.8), ("validation", 0.1), ("test", 0.1)),
    shuffle: bool = True,
    max_records: int = None,
):
    """
    Splits DealRecord data for model training and evaluation
    :param source_pickle: DealRecord pickle file
    :param save_dir: Write splits to this directory
    :param splits: A tuple of name,weight pairs for splitting (e.g. train/validation/test)
    :param shuffle: Shuffle all data before writing
    """
    with open(source_pickle, "rb") as pickle_file:
        deal_records: List[DealRecord] = pickle.load(pickle_file)

    logging.info(f"Loaded {len(deal_records)} DealRecord")

    if shuffle:
        random.shuffle(deal_records)

    weights = []
    split_records = []
    for split, weight in splits:
        split_records.append((split, []))
        weights.append(weight)

    for i, deal_record in enumerate(deal_records):
        split_name, split_record_list = random.choices(split_records, weights)[0]
        split_record_list.append(deal_record)
        if max_records and i > max_records:
            break

    for split_name, split_record_list in split_records:
        # Chunk writes to make pickle happy with large batches of records
        split_path = save_dir / (split_name + ".pickle")
        save_dir.mkdir(parents=True, exist_ok=True)
        with open(split_path, "wb") as split_file:
            pickle.dump(split_record_list, split_file)
            logging.info(f"Wrote {len(split_record_list)} records to {split_file.name}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    create_data_splits(
        Path("/Users/frice/bridge/vugraph_project/all_deals.pickle"),
        Path("/Users/frice/bridge/bid_learn/deals/toy/"),
        max_records=100,
    )
