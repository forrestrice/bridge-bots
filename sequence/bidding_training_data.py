from typing import List

import numpy as np


class BiddingTrainingData:
    def __init__(self, bidding_indices: List[int], holding_array: np.ndarray):
        self.bidding_indices = bidding_indices
        self.holding_array = holding_array
