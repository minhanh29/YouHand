from ai.encoder import Encoder
from database.database import UndirectedDatabase, DirectedDatabase
import numpy as np


class GestureGraph():
    def __init__(self, classifier,
                 undirected_db: UndirectedDatabase,
                 directed_db: DirectedDatabase):
        self.clf = classifier
        self.undirected_db = undirected_db
        self.directed_db = directed_db

        self.undirected_node_dict = {}
        # for belonging to a group (node)
        self.score_thres = 0.85
        self.load_graph()

    def load_graph(self):
        # load the undirected nodes
        undirected_data = self.undirected_db.all()
        undirected_data = sorted(undirected_data, key=lambda k: k['id'])
        for data in undirected_data:
            node = UndirectedNode(label=data['name'],
                                  m_id=data['id'],
                                  undirected_db=self.undirected_db,
                                  directed_db=self.directed_db,
                                  feature_list=data['feature'])
            self.undirected_node_dict[data['id']] = node

    def predict(self, keypointList, return_id=False):
        '''
        keypointList: KeyPointList

        Return the label for this feature
        '''
        if len(self.undirected_node_dict) == 0:
            if return_id:
                return 'undefined', None
            return 'undefined'

        feature = keypointList.get_undirected_feature()

        # check the child nodes
        node_id = self.clf.predict(self.undirected_node_dict, feature)
        # print("Undirected", node_id)

        if node_id is None:
            if return_id:
                return 'undefined', None
            return 'undefined'

        return self.undirected_node_dict[node_id].predict(self.clf, keypointList,
                                                          return_id=return_id)

    def update(self, label, keypointList_list):
        '''
        label: label of the gesture
        keypointList_list: list of KeyPointList
        '''
        # undirected phase
        if len(self.undirected_node_dict) == 0:
            # just train and update the node list
            first_node = UndirectedNode(label, '0',
                                        undirected_db=self.undirected_db,
                                        directed_db=self.directed_db,
                                        keypointList_list=keypointList_list)
            self.undirected_node_dict['0'] = first_node
            return '0_0'

        # check if it belongs to any group
        # all groups have 0 score at first
        score_dict = {}

        new_feature_list = []
        for keypointList in keypointList_list:
            undirected_feature = keypointList.get_undirected_feature()
            new_feature_list.append(undirected_feature)
            node_id = self.clf.predict(self.undirected_node_dict, undirected_feature)
            if node_id is not None:
                if node_id in score_dict:
                    score_dict[node_id] += 1
                else:
                    score_dict[node_id] = 1

        # the most likely group
        score = 0
        thres = int(self.score_thres * len(keypointList_list))

        if len(score_dict) > 0:
            result = max(score_dict.items(), key=lambda x: x[1])
            node_id = result[0]
            score = result[1]

        if score > thres:
            # update the node
            node = self.undirected_node_dict[node_id]
            return node.update(label, new_feature_list, keypointList_list, self.clf,
                               score=score/len(keypointList_list))
        else:
            # add new node
            new_node_id = self.get_new_id()
            new_node = UndirectedNode(label, new_node_id,
                                      undirected_db=self.undirected_db,
                                      directed_db=self.directed_db,
                                      keypointList_list=keypointList_list)
            self.undirected_node_dict[new_node_id] = new_node
            return f"{new_node_id}_0"

    def get_new_id(self):
        if len(self.undirected_node_dict) == 0:
            return "0"

        id_list = []
        for node_id in self.undirected_node_dict:
            id_list.append(int(node_id))
        last_id = max(id_list)
        return f"{last_id+1}"

    def change_clf(self, classifier):
        self.clf = classifier

    def get_clf(self):
        return self.clf

    def num_gestures(self):
        count = 0
        for node_id in self.undirected_node_dict:
            node = self.undirected_node_dict[node_id]
            count += node.num_gestures()
        return count

    def gesture_names(self):
        name_list = []
        for node_id in self.undirected_node_dict:
            node = self.undirected_node_dict[node_id]
            name_list.extend(node.gesture_names())
        name_list.sort()
        return name_list

    def delete(self, gesture_name):
        '''
        gesture_name: the gesture name
        '''
        data_list = self.directed_db.get(gesture_name)
        if len(data_list) == 0:
            return False

        # delete not in the graph
        data = data_list[0]

        # find the parent undirected node
        und_id = data['und_id']
        node = self.undirected_node_dict[und_id]

        # delete the node
        if not node.delete(data['id']):
            return False

        # delete this parent node as well
        if node.num_gestures() == 0:
            self.undirected_node_dict.pop(und_id)
            self.undirected_db.delete(und_id)

        return True

    def rename(self, old_name, new_name):
        '''
        Rename a gesture
        '''
        data_list = self.directed_db.get(old_name)
        if len(data_list) == 0:
            return False

        # rename not in the graph
        data = data_list[0]

        # find the parent undirected node
        und_id = data['und_id']
        node = self.undirected_node_dict[und_id]

        # rename the node
        return node.rename(data['id'], new_name)

class UndirectedNode():
    def __init__(self, label, m_id,
                 undirected_db: UndirectedDatabase,
                 directed_db: DirectedDatabase,
                 keypointList_list=None,
                 feature_list=None):
        self.label = label
        self.id = m_id
        self.undirected_db = undirected_db
        self.directed_db = directed_db
        self.directed_node_dict = {}

        if feature_list is not None:
            self.feature_list = feature_list
            directed_data = self.directed_db.get_directed_data(self.id)
            for data in directed_data:
                node = DirectedNode(data['name'], data['id'], self.id,
                                    self.directed_db, feature_list=data['feature'])
                self.directed_node_dict[data['id']] = node

        elif keypointList_list is not None:
            encoder = Encoder()
            # convert keypoints to feature
            for keypointList in keypointList_list:
                encoder.update(keypointList.get_undirected_feature())

            # update undirected node
            print(f"\nProcessing undirected gesture {label}")
            self.feature_list = encoder.get_repr_feature()
            self.undirected_db.insert_or_update(self.label, self.feature_list.tolist(),
                                                m_id=self.id)

            # update the first child directed node
            node_id = f"{self.id}_0"
            node = DirectedNode(label, node_id, self.id,
                                self.directed_db,
                                keypointList_list=keypointList_list)
            self.directed_node_dict[node_id] = node

        self.score_thres = 0.8

    def update(self, label, new_feature_list, keypointList_list, clf, score=0.75):
        '''
        Update the centroids and directed node
        '''

        # update the centroids
        print(f"\nProcessing undirected gesture {label}")

        # update features
        if score < 0.9:
            encoder = Encoder()
            repeate_num = len(new_feature_list)
            features = np.concatenate([np.repeat(self.feature_list, repeate_num, axis=0),
                                      new_feature_list])
            encoder.set_features(features)
            self.feature_list = encoder.get_repr_feature()
            # self.feature_list = np.concatenate([self.feature_list, new_feature])
            self.undirected_db.insert_or_update(self.label, self.feature_list.tolist())

        # check if it belongs to any group
        # all groups have 0 score at first
        score_dict = {}

        new_directed_feature_list = []
        for keypointList in keypointList_list:
            directed_feature = keypointList.get_directed_feature()
            new_directed_feature_list.append(directed_feature)
            node_id = clf.predict(self.directed_node_dict, directed_feature)
            if node_id is not None:
                if node_id in score_dict:
                    score_dict[node_id] += 1
                else:
                    score_dict[node_id] = 1

        # the most likely group
        score = 0
        thres = int(self.score_thres * len(keypointList_list))

        if len(score_dict) > 0:
            result = max(score_dict.items(), key=lambda x: x[1])
            node_id = result[0]
            score = result[1]

        if score > thres:
            # update the node
            node = self.directed_node_dict[node_id]
            # return node.update(label, new_directed_feature_list)
            return node_id
        else:
            # add new node
            new_node_id = self.get_new_id()
            new_node = DirectedNode(label, new_node_id, self.id, self.directed_db,
                                    keypointList_list=keypointList_list)
            self.directed_node_dict[new_node_id] = new_node
            return new_node_id

    def get_new_id(self):
        if len(self.directed_node_dict) == 0:
            return f"{self.id}_0"

        id_list = []
        for node_id in self.directed_node_dict:
            id_list.append(int(node_id.split("_")[-1]))
        last_id = max(id_list)
        return f"{self.id}_{last_id+1}"

    def predict(self, classifier, keypointList, return_id=False):
        '''
        Assume that this node is matched chosen. Just check the child node
        '''

        # only 1 node, just return the label
        if len(self.directed_node_dict) == 1:
            if return_id:
                return self.label, list(self.directed_node_dict.keys())[0]
            return self.label

        feature = keypointList.get_directed_feature()
        # check the child nodes
        # print("Directed")
        node_id = classifier.predict(self.directed_node_dict,
                                     feature, strong=False)

        # print("Directed", node_id)
        # no node matches
        if node_id is None:
            if return_id:
                return 'undefined', None
            return 'undefined'

        return self.directed_node_dict[node_id].predict(classifier, feature,
                                                        return_id=return_id)

    def num_gestures(self):
        return len(self.directed_node_dict)

    def gesture_names(self):
        name_list = []
        for node_id in self.directed_node_dict:
            node = self.directed_node_dict[node_id]
            name_list.append(node.label)
        return name_list

    def delete(self, d_id):
        '''
        d_id: id of the directed node
        '''
        if d_id not in self.directed_node_dict:
            print("Gesture does not exist")
            return False

        self.directed_node_dict.pop(d_id)

        # delete node in the database
        self.directed_db.delete(d_id)

        return True

    def rename(self, d_id, new_name):
        if d_id not in self.directed_node_dict:
            print("Gesture does not exist")
            return False

        # rename the node
        if not self.directed_node_dict[d_id].rename(new_name):
            return False

        if self.num_gestures() == 1:
            # rename this undirected node as well
            self.label = new_name
            return self.undirected_db.rename(self.id, new_name)
        return True

class DirectedNode():
    def __init__(self, label, m_id, und_id,
                 directed_db: DirectedDatabase,
                 keypointList_list=None,
                 feature_list=None):
        self.label = label
        self.directed_db = directed_db
        self.id = m_id
        self.und_id = und_id

        if feature_list is not None:
            self.feature_list = feature_list

        elif keypointList_list is not None:
            print(f"\nProcessing directed gesture {label}")
            encoder = Encoder()
            # convert keypoints to feature
            for keypointList in keypointList_list:
                encoder.update(keypointList.get_directed_feature())
            self.feature_list = encoder.get_repr_feature(is_directed=True)
            self.directed_db.insert_or_update(self.label, self.feature_list.tolist(),
                                              self.id, self.und_id)

    def update(self, label, new_directed_feature_list):
        '''
        Update the node feature
        Return the updated node's label
        '''

        print(f"\nProcessing directed gesture {label}")
        encoder = Encoder()
        features = np.concatenate([np.repeat(self.feature_list, 10, axis=0),
                                  new_directed_feature_list])
        encoder.set_features(features)
        self.feature_list = encoder.get_repr_feature(is_directed=True)
        self.directed_db.insert_or_update(self.label, self.feature_list.tolist())

        return self.label

    def predict(self, classifier, feature, return_id=False):
        '''
        Assume that this node is matched chosen. Just check the child node
        '''
        # TODO: add positional layer
        if return_id:
            return self.label, self.id
        return self.label

    def rename(self, new_name):
        self.label = new_name
        return self.directed_db.rename(self.id, new_name)
