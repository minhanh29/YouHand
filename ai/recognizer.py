import cv2
import mediapipe as mp
from ai.encoder import KeyPoint, KeyPointList
from ai.classifiers import EuclideanClassifier, LogisticClassifier,\
    LinearClassifier, RandomForestClassifier
from database.database import UndirectedDatabase, DirectedDatabase
from ai.graph_util import GestureGraph
import sys
import os


def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)

    return os.path.join(datadir, filename)


class RecognizerController():
    STATIC = 0
    DYNAMIC = 1

    def __init__(self, database_path='../database/gestures_db.json',
                 classifier='linear', mode=0):
        # config
        self.new_gesture = 'new_gesture'
        self.mode = mode
        # self.db_controller = MyDatabase(database_path)
        # if mode == RecognizerController.DYNAMIC:
        #     self.undirected_db = UndirectedDatabase('database/undirected_dynamic_gesture.json')
        #     self.directed_db = DirectedDatabase('database/directed_dynamic_gesture.json')
        if mode == RecognizerController.STATIC:
            self.undirected_db = UndirectedDatabase(find_data_file('../database/undirected_gesture.json'))
            self.directed_db = DirectedDatabase(find_data_file('../database/directed_gesture.json'))
        # self.dynamic_db = DynamicDatabase('database/dynamic_gesture.json')

        self.isPredict = True
        self.show_keypoint = True
        self.isUpdate = False

        self.old_gesture = 'undefined'
        self.trainDynamic = False

        # models
        # best
        if classifier == 'linear':
            self.clf = LinearClassifier()

        # good
        elif classifier == 'euclidean':
            self.clf = EuclideanClassifier()

        # acceptable slow
        elif classifier == 'random_forest':
            self.clf = RandomForestClassifier()

        # super slow
        # elif classifier == 'neural_network':
        #     self.clf = NeuralNetworkClassifier()

        # worst
        elif classifier == 'logistic':
            self.clf = LogisticClassifier()
        else:
            raise ValueError('Classifier not supported.')

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(max_num_hands=1)

        # self.encoder = Encoder()
        self.my_graph = GestureGraph(self.clf, self.undirected_db, self.directed_db)
        # self.dynamic_manager = DynamicManager(self.my_graph, self.dynamic_db)
        # self.keypointList_matrix = []
        self.keypointList_list = []
        self.count = 0

    def change_classifer(self, classifier):
        # save the brain
        if classifier == 'linear':
            self.clf = LinearClassifier()

        elif classifier == 'euclidean':
            self.clf = EuclideanClassifier()

        elif classifier == 'random_forest':
            self.clf = RandomForestClassifier()

        # elif classifier == 'neural_network':
        #     self.clf = NeuralNetworkClassifier()

        elif classifier == 'logistic':
            self.clf = LogisticClassifier()
        else:
            raise ValueError('Classifier not supported.')

        self.my_graph.change_clf(self.clf)

    # def change_gesture_mode(self, mode):
    #     self.mode = mode
    #     if mode == RecognizerController.DYNAMIC:
    #         self.undirected_db = UndirectedDatabase('database/undirected_dynamic_gesture.json')
    #         self.directed_db = DirectedDatabase('database/directed_dynamic_gesture.json')
    #         self.my_graph = GestureGraph(self.clf, self.undirected_db, self.directed_db)
    #         self.dynamic_manager = DynamicManager(self.my_graph, self.dynamic_db)
    #     elif mode == RecognizerController.STATIC:
    #         self.undirected_db = UndirectedDatabase('database/undirected_gesture.json')
    #         self.directed_db = DirectedDatabase('database/directed_gesture.json')
    #         self.my_graph = GestureGraph(self.clf, self.undirected_db, self.directed_db)

    def filter_keypoints(self, img, keypoints):
        '''
        Filter 21 keypoints to 16 keypoints
        '''
        h = img.shape[0]
        w = img.shape[1]

        my_points = []
        accepted_index = [0, 2, 3, 4, 5, 8, 9, 12, 13, 16, 17, 20]
        for i in accepted_index:
            p = keypoints[i]
            my_p = KeyPoint(int(p.x*w), int(p.y*h))
            my_points.append(my_p)

        # middle points
        insert_index = [5, 8, 11, 14]  # insert new points
        # old points to calculate mean
        cal_index = [(6, 7), (10, 11), (14, 15), (18, 19)]
        for index, point in zip(insert_index, cal_index):
            lm1 = keypoints[point[0]]
            lm2 = keypoints[point[1]]
            lm = KeyPoint(int((lm1.x + lm2.x)/2 * w),
                          int((lm1.y + lm2.y)/2 * h))
            my_points.insert(index, lm)

        return my_points

    def detect_keypoints(self, img):
        results = self.hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        predictions = []
        result_points = []

        if results.multi_hand_landmarks:
            for handlm in results.multi_hand_landmarks:
                my_points = self.filter_keypoints(img, handlm.landmark)
                result_points = my_points
                keypointList = KeyPointList(my_points)
                if self.isPredict:
                    # if self.mode == RecognizerController.UNDIRECTED:
                    #     featureList = keypointsList.get_feature_list()
                    # elif self.mode == RecognizerController.DIRECTED:
                    #     featureList = keypointsList.get_directional_features()
                    # prediction = self.clf.predict(featureList)
                    # prediction = self.clf.predict(keypointsList)

                    prediction = self.my_graph.predict(keypointList)
                    # prediction = self.dynamic_manager.predict(keypointList)

                    # if self.mode == RecognizerController.DYNAMIC:
                    #     if prediction != 'undefined' and prediction != self.old_gesture:
                    #         self.old_gesture = prediction

                    #     text_size, base_line = cv2.getTextSize(f"{self.old_gesture}", cv2.FONT_HERSHEY_COMPLEX, 1.5, 2)
                    #     my_x = img.shape[1] - int(text_size[0] + 10) - 30
                    #     my_y = 40
                    #     cv2.rectangle(img, (my_x, my_y), (my_x+text_size[0] + 20, my_y+text_size[1] +base_line + 10),
                    #                   (0, 0, 0), cv2.FILLED)
                    #     cv2.putText(img, self.old_gesture, (my_x + 10, my_y + 5 + text_size[1]),
                    #                 cv2.FONT_HERSHEY_COMPLEX, 1.5, (0, 255, 0), 2)

                    predictions.append(prediction)

                    if prediction == 'undefined':
                        rec_color = (0, 255, 255)
                    else:
                        rec_color = (0, 255, 0)

                    # display prediction
                    org = my_points[0]
                    text_size, base_line = cv2.getTextSize(f"{prediction}", cv2.FONT_HERSHEY_COMPLEX, 1, 2)
                    my_x = org.x - int(text_size[0]/2 + 10)
                    my_y = org.y + 10
                    cv2.rectangle(img, (my_x, my_y), (my_x+text_size[0] + 20, my_y+text_size[1] +base_line + 10),
                                  rec_color, cv2.FILLED)
                    cv2.putText(img, f"{prediction}", (my_x + 10, my_y + 5 + text_size[1]),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)

                if self.isUpdate:
                    # cv2.putText(img, "Press Stop Training when completed", (30, 60),
                    #             cv2.FONT_HERSHEY_COMPLEX, 0.8,
                    #             (0, 0, 255), 2)

                    # display new gesture name
                    org = my_points[0]
                    text_size, base_line = cv2.getTextSize(f"{self.new_gesture}", cv2.FONT_HERSHEY_COMPLEX, 1.5, 2)
                    my_x = org.x - int(text_size[0]/2 + 10)
                    my_y = org.y + 10
                    cv2.rectangle(img, (my_x, my_y), (my_x+text_size[0] + 20, my_y+text_size[1] +base_line + 10),
                                  (0, 0, 255), cv2.FILLED)
                    cv2.putText(img, f"{self.new_gesture}", (my_x + 10, my_y + 5 + text_size[1]),
                                cv2.FONT_HERSHEY_COMPLEX, 1.5, (0, 0, 0), 2)
                    self.keypointList_list.append(keypointList)
                    # if self.mode == RecognizerController.UNDIRECTED:
                    #     self.encoder.update(keypointsList.get_feature_list())
                    # elif self.mode == RecognizerController.DIRECTED:
                    #     self.encoder.update(keypointsList.get_directional_features())
                if self.show_keypoint:
                    keypointList.draw_landmarks(img)

        # dynamic training
        # if self.mode == RecognizerController.DYNAMIC and self.trainDynamic:
        #     if not self.isUpdate:
        #         cv2.putText(img, "Press S to start, D to pause",
        #                     (300, 40), cv2.FONT_HERSHEY_COMPLEX, 1,
        #                     (255, 0, 0), 2)

        return img, (predictions, result_points)

    # def finish_dynamic_update(self):
    #     print("Update")
    #     self.keypointList_matrix.append(self.keypointList_list)
    #     self.keypointList_list = []
    #     self.isUpdate = False

    def save_gesture(self):
        if self.mode == RecognizerController.STATIC:
            if self.isUpdate:
                self.my_graph.update(self.new_gesture, self.keypointList_list)
                self.keypointList_list = []

                # no more learning
                self.isUpdate = False

        # elif self.mode == RecognizerController.DYNAMIC:
        #     if self.isUpdate:
        #         self.isUpdate = False
        #         self.finish_dynamic_update()
        #     self.trainDynamic = False

        #     self.dynamic_manager.update(self.new_gesture, self.keypointList_matrix)
        #     self.keypointList_matrix = []
        #     self.keypointList_list = []

        print("saved gesture", self.new_gesture)
        return f"Gesture '{self.new_gesture}' is saved successfully!"

    def delete_gesture(self, gesture):
        # if self.mode == RecognizerController.DYNAMIC:
        #     return self.dynamic_manager.delete(gesture)
        return self.my_graph.delete(gesture)

    def set_max_hands(self, value):
        self.hands = self.mpHands.Hands(max_num_hands=value)

    def reset_hand(self):
        self.hands = self.mpHands.Hands(max_num_hands=1)

    def change_db(self, database_path):
        # TODO: delete this function
        # self.db_controller.change_db(database_path)
        pass

    def get_gesture_num(self):
        # if self.mode == RecognizerController.DYNAMIC:
        #     return self.dynamic_manager.num_gestures()
        return self.my_graph.num_gestures()

    def get_gesture_names(self):
        # if self.mode == RecognizerController.DYNAMIC:
        #     return self.dynamic_manager.gesture_names()
        return self.my_graph.gesture_names()

    def rename_gesture(self, old_name, new_name):
        # if self.mode == RecognizerController.DYNAMIC:
        #     return self.dynamic_manager.rename(old_name, new_name)
        return self.my_graph.rename(old_name, new_name)
