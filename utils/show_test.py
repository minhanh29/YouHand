import cv2
from recognizer import RecognizerController
import os
import json
import pandas as pd
import numpy as np
import random
from sklearn.metrics import confusion_matrix, roc_auc_score
import itertools
import matplotlib.pyplot as plt

data_dir = '../dataset/senz3d'
gesture_list = os.listdir(data_dir)
gesture_list = [d for d in gesture_list if os.path.isdir(os.path.join(data_dir, d))]

label_map = {
    'G1': 0,
    'G2': 2,
    'G3': 3,
    'G4': 4,
    'G5': 5,
    'G6': 6,
    'G7': 7,
    'G8': 8,
    'G9': 9,
    'G10': 10,
    'G11': 11,
    'undefined': 12
}

cm_classes = gesture_list.copy()
cm_classes.append('other')

def convert_label(pred):
    return label_map[pred]

# create a dataframe mapping image path with the labels
df_list = []
for gesture in gesture_list:
    ges_path = os.path.join(data_dir, gesture)
    img_list = os.listdir(ges_path)
    img_list = [img for img in img_list if '.png' in img]
    for img in img_list:
        img_path = os.path.join(ges_path, img)
        df_list.append([img_path, gesture])
main_df = pd.DataFrame(df_list, columns=['path', 'label'])

def get_predictions(clf):
    y_pred = []
    y_true = []
    count = 0
    for _, row in main_df.iterrows():
        img = cv2.imread(row['path'])
        if random.random() < 0.5:
            img = cv2.flip(img, 1)
        y_true.append(row['label'])
#         y_pred.append(clf.get_prediction(img))
        cv2.imshow("Img", clf.detect_keypoints(img))
        clf.reset_hand()
        cv2.waitKey(200)
        count += 1
        if count > 100:
            break
    return y_true, y_pred

def save_keypoints(clf):
    classes = ['G6', 'G1', 'G8', 'G9', 'G7', 'G2', 'G5', 'G4', 'G3', 'G11', 'G10']
    for label in classes:
        sub_df = main_df[main_df['label'] == label]

        result_df_list = []
        for _, row in sub_df.iterrows():
            img = cv2.imread(row['path'])
            if random.random() < 0.5:
                img = cv2.flip(img, 1)
    #         y_pred.append(clf.get_prediction(img))
            feature = clf.get_feature(img)
            # clf.reset_hand()
            if feature is None:
                continue
            result_df_list.append(feature)

        result_df_list = np.array(result_df_list).tolist()
        with open(f'keypoint_data/{label}.json', 'w') as f:
            json.dump(result_df_list, f)
            print(label)

linear_clf = RecognizerController('gestures_encode_name', 'linear')
save_keypoints(linear_clf)
# y_true, y_pred = get_predictions(linear_clf)
