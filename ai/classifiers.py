import numpy as np
import pickle
import os
import sys


def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)

    return os.path.join(datadir, filename)


class MyClassifier():
    def print_result(self, val_list, label_list):
        round_list = np.round(val_list, 2).tolist()

        print("%-8s" % "Value", end='')
        for dis in round_list:
            print("%10s" % str(dis), end='')
        print()
        print("%-8s" % "Label", end='')
        for label in label_list:
            print("%10s" % str(label), end='')
        print('\n')

    def predict(self, base_feature_dict, feature, strong=True) -> int:
        pass


class EuclideanClassifier(MyClassifier):
    def __init__(self):
        super().__init__()
        # weight of width in the compute_distance
        self.alpha = 0.4

        # differentiate between undefined and learned gestures
        self.distance_thres = 2.5
        self.soft_thres = 7

    def compute_distance(self, feature1, feature2):
        feature1 = np.array(feature1)
        feature2 = np.array(feature2)
        # angle distance
        return np.linalg.norm(feature1-feature2, ord=2, axis=-1)

    def predict(self, base_feature_dict, feature, strong=True):
        '''
        feature: 2-D array with n rows (features), each row contains
        2 values - width ratio and angle (in radian)

        base_feature_list: list of list of centroids

        Returns the index of the group that feature belongs to or -1
        '''
        if len(base_feature_dict) == 0:
            return None

        distance_list = []
        id_list = []
        thres = self.distance_thres if strong else self.soft_thres

        for base_id in base_feature_dict:
            # predefined feature
            base_features = base_feature_dict[base_id].feature_list
            d = np.min(self.compute_distance(base_features, feature))
            distance_list.append(d)
            id_list.append(base_id)

        index = np.argmin(distance_list)
        # if id_list[index] == 'dummy':
        #     print(distance_list[index])
        if distance_list[index] < thres:
            return id_list[index]
        return None


class RegressionClassifier(MyClassifier):
    def __init__(self, model_path=None):
        super().__init__()

        # load model
        if model_path is not None:
            model_path = find_data_file(model_path)
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)

        self.score_thes = 0
        self.soft_thres = 0.1

    def get_score(self, features, feature):
        # delete rebundant data
        # check shape
        if len(feature) != 25:
            return [0]
        features = np.array(features)
        feature = np.array(feature)
        input_arr = np.abs(features - feature)

        # check nan
        array_sum = np.sum(input_arr)
        array_has_nan = np.isnan(array_sum)
        if array_has_nan:
            return [0]

        predictions = self.model.predict(input_arr)
        return predictions

    def predict(self, base_feature_dict, feature, strong=True):
        '''
        feature: 2-D array with n rows (features), each row contains
        2 values - width ratio and angle (in radian)

        base_feature_list: list of list of centroids

        Returns the index of the group that feature belongs to or -1
        '''
        if len(base_feature_dict) == 0:
            return None

        score_list = []
        id_list = []
        thres = self.score_thes if strong else self.soft_thres

        for base_id in base_feature_dict:
            # predefined feature
            score = 0
            base_features = base_feature_dict[base_id].feature_list
            score = np.max(self.get_score(base_features, feature))
            score_list.append(score)
            id_list.append(base_id)

        index = np.argmax(score_list)
        # if type(id_list[index]) == int:
        # print(score_list[index])
        if score_list[index] > thres:
            return id_list[index]

        return None


class LogisticClassifier(RegressionClassifier):
    def __init__(self):
        super().__init__(os.path.join('models', 'logistic_comp.pickle'))

    def predict(self, base_feature_dict, feature, strong=True):
        '''
        feature: 2-D array with n rows (features), each row contains
        2 values - width ratio and angle (in radian)

        base_feature_list: list of list of centroids

        Returns the index of the group that feature belongs to or -1
        '''
        if len(base_feature_dict) == 0:
            return None

        score_list = []
        id_list = []

        for base_id in base_feature_dict:
            # predefined feature
            score = 0
            base_features = base_feature_dict[base_id].feature_list
            score = np.sum(self.get_score(base_features, feature))
            score_list.append(score)
            id_list.append(base_id)

        index = np.argmax(score_list)
        if score_list[index] > 0:
            return id_list[index]
        return None

class LinearClassifier(RegressionClassifier):
    def __init__(self):
        super().__init__(os.path.join('models', 'linear_comp.pickle'))
        self.score_thes = 0.73


class RandomForestClassifier(RegressionClassifier):
    def __init__(self):
        super().__init__(os.path.join('models', 'random_forest_comp.pickle'))

        with open('models/rf_pca.pickle', 'rb') as f:
            self.pca = pickle.load(f)
        self.score_thes = 0.5

    def get_score(self, features, feature):
        # check shape
        if len(feature) != 25:
            return [0]

        features = np.array(features)
        feature = np.array(feature)
        input_arr = np.abs(features - feature)

        # check nan
        array_sum = np.sum(input_arr)
        array_has_nan = np.isnan(array_sum)
        if array_has_nan:
            return [0]

        input_pca = self.pca.transform(input_arr)
        predictions = self.model.predict(input_pca)
        return predictions
