import json
import os
import numpy as np


gesture_dir = 'gestures'
target_file = 'gestures.json'
filelist = [file for file in os.listdir(gesture_dir)
            if '.json' in file]
print(f'Found {len(filelist)} in {gesture_dir}.')

gestures = {}
for file in filelist:
    name = file.split('.')[0]
    with open(os.path.join(gesture_dir, file), 'r') as f:
        features = json.load(f)
    new_feat = []
    for feature in features:
        feature = np.array(feature)
        feature = np.hstack(feature)
        feature = np.delete(feature, np.where(feature == 0))
        if len(feature) != 25:
            print("Error")
        new_feat.append(feature)

    gestures[name] = np.array(new_feat).tolist()

with open(target_file, 'w') as f:
    json.dump(gestures, f)
