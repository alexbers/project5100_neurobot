import os
import time
import random
import math
import sys

import numpy as np

from catboost import CatBoostRegressor, CatBoostClassifier, Pool, cv

class NNet:
    def __init__(self, base_filename):
        self.model_v = CatBoostRegressor()
        self.model_pi = CatBoostClassifier()
        
        self.model_v.load_model(base_filename + ".v")
        self.model_pi.load_model(base_filename + ".pi")

    def predict(self, board):
        board = board.as_float_list()[np.newaxis, :]

        v = self.model_v.predict(board, thread_count=1)[0]
        if v > 1.0:
            v = 1.0
        if v < -1:
            v = -1.0

        pi = self.model_pi.predict_proba(board, thread_count=1)[0]
        return pi, v
