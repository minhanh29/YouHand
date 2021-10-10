import numpy as np
from itertools import product
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from som.utils import euclidean_distance, loading_bar


class SOM:
    def __init__(self, map_size, input_shape,
                 learning_rate=0.5, std=4.0):
        self.map_size = map_size
        self.input_shape = input_shape
        self.learning_rate = learning_rate
        self.std = std
        self.min_learning_rate = 0.001
        self.min_std = 0.05

        self.label_map = {}
        self.default_value = 'undefined'
        self.compressed_map = []
        self.label_list = []

        # Compute the neighborhood map for all nodes
        self.neighborhood_map = np.zeros((*map_size, *map_size))
        indices = product(np.arange(self.map_size[0]),
                          np.arange(self.map_size[1]))
        indices_arr = np.array(list(indices))
        indices_reshape = indices_arr.reshape(self.map_size[0],
                                              self.map_size[1], 2)
        for index in indices_arr:
            distance = euclidean_distance(indices_reshape, np.array(index))
            self.neighborhood_map[tuple(index)] = -np.square(distance)

        # initialize the weights
        self.random_init()

    def random_init(self):
        '''
        Randomly initialize the weight values
        '''
        self.som_map = np.random.rand(*self.map_size, *self.input_shape)

    def pca_init(self, data):
        '''
        Initialise the weights with PCA

        data: ndarray with rank 2
        '''
        if len(np.array(data).shape) > 2:
            raise ValueError("Expect data input of rank 2.")

        pca = PCA(n_components=64)
        pca.fit(data)
        a = pca.singular_values_

        som_map = np.zeros((*self.map_size, data.shape[1]))
        indices = product(list(range(som_map.shape[0])),
                          list(range(som_map.shape[1])))
        for index in indices:
            som_map[index] = np.random.choice(a, 64)
        self.som_map = som_map

    def train(self, data, labels, epochs=10, reset_label=True, verbose=2):
        '''
        Train the model

        data: array of features
        (features must have the same shape as the input_shape)

        labels: ndarray with coressponding labbels

        verbose: 1 - only show epoch progress, 2 - show all iterations progress
        '''

        # print("Start training")
        data_size = len(data)
        num_iterations = epochs * data_size
        long_verbose = verbose == 2
        for e in range(epochs):
            # shuffle the data
            shuffle_data = data.copy()
            np.random.shuffle(shuffle_data)

            if long_verbose:
                print(f"\nEpoch {e+1}/{epochs}: ")
            for s, input_vec in enumerate(shuffle_data):
                # Randomly pick an input vector
                # data_index = np.random.randint(len(data))
                # input_vec = data[data_index]
                # find the BMU
                u = self.get_bmu(input_vec)

                # decay the rate
                # learning rate
                lr = self.decay_rate(self.learning_rate, e * data_size + s,
                                     num_iterations)
                lr = max(lr, self.min_learning_rate)
                # standard deviation
                c_std = self.decay_rate(self.std, e * data_size + s,
                                        num_iterations)
                c_std = max(c_std, self.min_std)

                # Update the weight vectors of the nodes in the neighborhood
                # of the BMU (including the BMU itself)
                # neighborhood function
                thetha = self.gaussian(u, c_std)
                rate = thetha * lr

                # diff between a node and the input vector
                delta = input_vec - self.som_map
                rate = np.expand_dims(rate, axis=-1)
                rate = np.repeat(rate, delta.shape[2], axis=-1)

                # update the weights
                self.som_map = self.som_map + rate * delta

                if long_verbose:
                    if s % 20 == 0:
                        loading_bar(s, data_size)
            if long_verbose:
                loading_bar(s, data_size)
            else:
                loading_bar(e, epochs)

        # create label map
        self.create_label_map(data, labels, reset_label)

        # compress the model
        self.compress_model(self.label_map)
        print("\nDone.")

    def create_label_map(self, data, labels, reset_label=True):
        '''
        Create label map mapping indices to the coressponding label
        '''
        distance_map = {}
        if reset_label:
            self.label_map = {}
        for x, y in zip(data, labels):  # scatterplot
            coord, d = self.get_bmu(x, return_distance=True)
            if coord in self.label_map and d > distance_map[coord]:
                continue
            self.label_map[coord] = y
            distance_map[coord] = d

    def compress_model(self, label_map):
        '''
        Put all the nodes to 1D array with no holes

        label_map: dictionary mapping indices with label

        Create a compressed_map (1D list) containing all the features
        and a label_list with coressponding label
        '''
        compressed_map = []
        label_list = []
        for position in label_map:
            # label name
            label = label_map[position]

            # weights
            weights = self.som_map[position]
            compressed_map.append(weights)
            label_list.append(label)
        self.compressed_map = np.array(compressed_map)
        self.label_list = np.array(label_list)

    def get_prediction(self, input_vec):
        '''
        Return the prediction given a singlular input

        input_vec: ndarray with the same shape as input_shape
        '''
        distance = euclidean_distance(input_vec, self.compressed_map)
        i = np.argmin(distance)
        return self.label_list[i]

    def predict(self, data):
        '''
        Return the predictions given a list of inputs

        data: array of inputs to predict
        '''

        # predictions = []
        # key_arr = np.array(list(self.label_map.keys()))
        # for x in data:
        #     coord = self.get_bmu(x)
        #     if coord not in self.label_map:
        #         c_arr = np.array(coord)
        #         # distance = self.euclidean_distance(c_arr, key_arr)
        #         distance = euclidean_distance(c_arr, key_arr)
        #         i = np.argmin(distance)
        #         coord = tuple(key_arr[i])
        #     pred = self.label_map.get(coord, self.default_value)
        #     predictions.append(pred)
        # return np.array(predictions)
        return np.array(list(map(self.get_prediction, data)))

    def get_bmu(self, input_vec, return_distance=False):
        '''
        Return the indices position of the Best Matching Unit (BMU)

        input_vec: ndarray with the same shape as input_shape
        '''
        # d = self.euclidean_distance(input_vec, self.som_map)
        d = euclidean_distance(input_vec, self.som_map)
        i = np.argmin(d)
        row = i // self.map_size[0]
        col = i - self.map_size[0] * row

        if return_distance:
            return (row, col), d[row, col]

        return (row, col)

    def decay_rate(self, rate, current_iter, max_iterations):
        '''
        Return the rate coressponding to the current iteration
        using asymptotic decay function

        rate: learning_rate or standard deviation (std)
        current_iter: current iteration
        '''
        return rate / (1+current_iter/(max_iterations/2))

    def gaussian(self, center_index, std):
        '''
        Neighborhood function: Compute the value based on the gaussian formula.
        The numerator is the square of the euclidean distance between the
        center index and the target index (pre-computed)

        center_index: tuple containing indices of the BMU
        '''
        numer = self.neighborhood_map[tuple(center_index)]
        denom = 2 * std * std

        # gaussian formula
        return np.exp(numer / denom)

    def show_weight_map(self):
        '''
        Show the 2D representation of the weight map
        '''
        # show the som map
        plt.figure(figsize=(8, 8))
        for coord in self.label_map:  # scatterplot
            y = self.label_map[coord]
            plt.text(coord[0]+.5, coord[1]+.5,  str(y),
                     color=plt.cm.rainbow(y / 10.),
                     fontdict={'weight': 'bold', 'size': 11})
        plt.title("Self-organizing Map")
        plt.axis([0, self.map_size[0], 0, self.map_size[1]])
        plt.show()
