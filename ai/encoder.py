import cv2
import math
import numpy as np
# import pandas as pd
from sklearn.cluster import MeanShift, KMeans
from som.som import SOM


class KeyPoint():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def to_list(self):
        return [self.x, self.y]

    def to_tuple(self):
        return (self.x, self.y)

    def __repr__(self):
        return f"({self.x}, {self.y})"


class KeyPointList():
    def __init__(self, keypoints):
        self.keypoints = keypoints
        self.connect_points = [(0, 1), (1, 2), (2, 3),  # thumb
                               (0, 4), (4, 5), (5, 6),  # index
                               (0, 7), (7, 8), (8, 9),  # middle
                               (0, 10), (10, 11), (11, 12),  # ring
                               (0, 13), (13, 14), (14, 15),  # pinky
                               (1, 4), (4, 7), (7, 10), (10, 13)]

        # eliminated vectors
        self.width_elim = [(10, 13), (7, 10), (0, 10), (1, 2),
                           (2, 3), (0, 13), (4, 7)]
        self.angle_elim = [(10, 13), (7, 10), (0, 10), (0, 13)]
        self.point_elim  = [4, 7, 10]
        self.point_elim_width = 13

    # in radian
    def get_angle(self, vector_1, vector_2):
        # unit_vector_1 = vector_1 / np.linalg.norm(vector_1)
        # unit_vector_2 = vector_2 / np.linalg.norm(vector_2)
        # dot_product = np.dot(unit_vector_1, unit_vector_2)
        # angle = np.arccos(dot_product)
        dot_product = np.dot(vector_1, vector_2)
        length_product = np.linalg.norm(vector_1) * np.linalg.norm(vector_2)
        if length_product <= 0:
            return 0
        try:
            angle = np.arccos(dot_product / (length_product + 0.0001))
            return angle
        except RuntimeWarning:
            return 0

    def compute_cross_factor(self, vec1, vec2):
        '''
        compute the cross product of 2 vector and
        return the sign of the product 1 or -1
        '''
        cross_product = vec1[0] * vec2[1] - vec1[1] * vec2[0]
        return 1 if cross_product >= 0 else -1

    def get_undirected_feature(self):
        feature = []

        # base vector 0 -> 7
        pt1 = self.keypoints[0]
        pt2 = self.keypoints[7]
        base_vec = (pt2.x - pt1.x, pt2.y - pt1.y)
        base_width = math.dist(pt1.to_list(), pt2.to_list())

        # vector to decide angle direction 0 -> 10
        pt1 = self.keypoints[0]
        pt2 = self.keypoints[10]
        direction_vec = (pt2.x - pt1.x, pt2.y - pt1.y)

        # compute cross product to determine direction
        # standardize the direction is either 1 or -1
        direction_factor = self.compute_cross_factor(base_vec, direction_vec)

        # print("Start")
        for pair in self.connect_points:
            # eliminate unimportant vectors
            if pair[0] == 0 and pair[1] == 7:
                continue
            if pair in self.width_elim and pair in self.angle_elim:
                continue

            pt1 = self.keypoints[pair[0]]
            pt2 = self.keypoints[pair[1]]

            if pair not in self.width_elim:
                width = math.dist(pt1.to_list(), pt2.to_list())
                width = width / base_width
                feature.append(width)

            if pair not in self.angle_elim:
                # angle must not be none
                vec = (pt2.x - pt1.x, pt2.y - pt1.y)
                angle = self.get_angle(base_vec, vec)

                # the direction of the angle
                direction = self.compute_cross_factor(base_vec, vec)\
                    * direction_factor
                angle = angle * direction
                feature.append(angle)

        return np.array(feature)

    def get_directed_feature(self):
        feature = []

        # base vector 0 -> 7
        pt1 = self.keypoints[0]
        pt2 = self.keypoints[7]
        base_width = math.dist(pt1.to_list(), pt2.to_list())

        # vector to decide angle direction 0 -> 10
        base_y = np.array([0, -1])
        base_x = np.array([1, 0])

        # print("Start")
        for pair in self.connect_points:
            # eliminate unimportant vectors
            if pair[0] == 0 and pair[1] == 7:
                continue
            if pair in self.width_elim and pair in self.angle_elim:
                continue

            pt1 = self.keypoints[pair[0]]
            pt2 = self.keypoints[pair[1]]

            if pair not in self.width_elim:
                width = math.dist(pt1.to_list(), pt2.to_list())
                width = width / base_width
                feature.append(width)

            if pair not in self.angle_elim:
                # angle must not be none
                vec = (pt2.x - pt1.x, pt2.y - pt1.y)
                angle_x = self.get_angle(base_x, vec)
                comp = np.pi / 2
                # if angle_x > comp:
                #     angle_x = angle_x - np.pi
                angle_y = self.get_angle(base_y, vec)
                if angle_x > comp:
                    angle = angle_y
                else:
                    angle = -angle_y
                feature.append(angle)

        return np.array(feature)

    def get_transition_feature(self, prev_keypointList):
        feature = []

        # base vector 0 -> 7
        pt1 = self.keypoints[0]
        pt2 = self.keypoints[7]
        base_width = math.dist(pt1.to_list(), pt2.to_list())

        # vector to decide angle direction 0 -> 10
        base_y = np.array([0, -1])
        base_x = np.array([1, 0])

        prev_keypoints = prev_keypointList.keypoints

        # only consider the wrist point
        current_pt = self.keypoints[0]
        prev_pt = prev_keypoints[0]

        vec = np.array([current_pt.x - prev_pt.x, current_pt.y - prev_pt.y])
        width = math.dist(current_pt.to_list(), prev_pt.to_list())
        width = width / base_width
        feature.append(width)

        vec = (current_pt.x - prev_pt.x, current_pt.y - prev_pt.y)

        angle_x = self.get_angle(base_x, vec)
        comp = np.pi / 2
        angle_y = self.get_angle(base_y, vec)
        if angle_x > comp:
            angle = angle_y
        else:
            angle = -angle_y
        feature.append(angle)

        return feature
        # return np.array(feature)
        # for i in range(len(self.keypoints)):
        #     if i in self.point_elim:
        #         continue

        #     prev_pt = prev_keypoints[i]
        #     current_pt = self.keypoints[i]

        #     if i != self.point_elim_width:
        #         width = math.dist(current_pt.to_list(), prev_pt.to_list())
        #         width = width / base_width
        #         feature.append(width)

        #     vec = (current_pt.x - prev_pt.x, current_pt.y - prev_pt.y)

        #     angle_x = self.get_angle(base_x, vec)
        #     comp = np.pi / 2
        #     angle_y = self.get_angle(base_y, vec)
        #     if angle_x > comp:
        #         angle = angle_y
        #     else:
        #         angle = -angle_y
        #     feature.append(angle)

        # return np.array(feature)


    def draw_point(self, img, pt, color=(0, 0, 255)):
        cv2.circle(img, (pt.x, pt.y), 5, color, -1)

    def connect_point(self, img, pt1, pt2, color=(0, 255, 255)):
        cv2.line(img, (pt1.x, pt1.y), (pt2.x, pt2.y), color, 3)

    def draw_landmarks(self, img):
        for index, pair in enumerate(self.connect_points):
            self.connect_point(img, self.keypoints[pair[0]],
                               self.keypoints[pair[1]])

        for index, pt in enumerate(self.keypoints):
            self.draw_point(img, pt)


class Encoder():
    def __init__(self):
        self.features = []
        self.width_elim = [(10, 13), (7, 10), (0, 10), (1, 2),
                           (2, 3), (0, 13), (4, 7)]
        self.angle_elim = [(10, 13), (7, 10), (0, 10), (0, 13)]

    def set_features(self, feature_list):
        for feature in feature_list:
            self.update(feature)

    def update(self, feature):
        # check nan
        array_sum = np.sum(feature)
        array_has_nan = np.isnan(array_sum)
        if not array_has_nan:
            self.features.append(feature)

    def get_repr_feature(self, is_directed=False):
        np_features = np.array(self.features)

        # compute all possible centroids
        print("Finding all possible centroids...")
        if is_directed:
            # SOM
            model = SOM((10, 10), (25,))
            y = np.repeat(1, len(np_features))
            model.train(np_features, y, verbose=1)
            centroids = model.compressed_map
            centroid_count = len(centroids)
            # clustering = DBSCAN(eps=0.3, min_samples=5).fit(np_features)
            # centroids = clustering.components_
            print("Directed gesture")
        else:
            clustering = MeanShift(bandwidth=2).fit(np_features)
            centroids = clustering.cluster_centers_

            # at least 3
            centroid_count = max(len(centroids), 3)

            kmeans = KMeans(n_clusters=centroid_count, random_state=0)
            kmeans.fit(np_features)
            centroids = kmeans.cluster_centers_

        print(f"Found {centroid_count} centroids")

        # df = pd.DataFrame(centroids)
        # print(df.head(len(centroids)))

        return np.array(centroids)


