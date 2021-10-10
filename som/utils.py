import numpy as np
import itertools
import sys
import matplotlib.pyplot as plt

from sklearn.metrics import confusion_matrix


def euclidean_distance(x1, x2):
    '''
    Compute the euclidean distance

    x1, x2:  ndarray (can have different shapes)
    '''
    return np.linalg.norm(x1 - x2, axis=-1)


def plot_confusion_matrix(y_true, y_pred, classes):
    '''
    For public call
    '''
    cm = confusion_matrix(y_true=y_true, y_pred=y_pred)
    cmap = plt.cm.Blues
    title = 'Confusion matrix'

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    print(cm)

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j], horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.show()


def get_accuracy(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    result = y_true - y_pred
    error = np.count_nonzero(result)
    return 1 - error / len(y_true)


def loading_bar(count, total):
    '''
    Print progess bar on the screen
    '''
    i = int((count+1)/total * 50)
    sys.stdout.write('\r')
    sys.stdout.write('[%-50s] %d%%  %d / %d' % ('='*i, i*2, count+1, total))
    sys.stdout.flush()
