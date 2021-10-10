import numpy as np
import pandas as pd
import json
import os


width_elim = [(10, 13), (7, 10), (0, 10), (1, 2),
                   (2, 3), (0, 13), (4, 7)]
angle_elim = [(10, 13), (7, 10), (0, 10), (0, 13)]

connect_points = [(0, 1), (1, 2), (2, 3),  # thumb
                  (0, 4), (4, 5), (5, 6),  # index
                  (0, 7), (7, 8), (8, 9),  # middle
                  (0, 10), (10, 11), (11, 12),  # ring
                  (0, 13), (13, 14), (14, 15),  # pinky
                  (1, 4), (4, 7), (7, 10), (10, 13)]


def json_to_csv(np_features, dest):
    stacked_data = []
    for feat in np_features:
        feat = np.hstack(feat)
        stacked_data.append(feat)
    stacked_data = np.array(stacked_data)
    # for feautre selection
    raw_columns = []
    for pair in connect_points:
        if pair[0] == 0 and pair[1] == 7:
            continue
        if pair in width_elim and pair in angle_elim:
            continue
        raw_columns.append(f"width_{pair[0]}_{pair[1]}")
        raw_columns.append(f"angle_{pair[0]}_{pair[1]}")
    raw_df = pd.DataFrame(stacked_data, columns=raw_columns)
    raw_df.to_csv(dest)


data_dir = 'gestures'
target_dir = f"{data_dir}/csv"

file_list = os.listdir(data_dir)
file_list = [file for file in file_list if '.json' in file]
for file in file_list:
    with open(f"{data_dir}/{file}", 'r') as f:
        data = json.load(f)

        name = file.split('.')[0]
        json_to_csv(data, f"{target_dir}/{name}.csv")
