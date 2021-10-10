import tensorflow as tf
import cv2
import numpy as np

model = tf.lite.Interpreter('hand_landmark/hand_landmark.tflite')
model.allocate_tensors()
input_details = model.get_input_details()
output_details = model.get_output_details()
input_shape = input_details[0]['shape']
print(input_shape)
print('Input detail', input_details)
print('Output detail', output_details)

img = cv2.imread('sample.jpg')
img = cv2.resize(img, (224, 224))
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
input_img = np.array([img], dtype='float32')
model.set_tensor(input_details[0]['index'], input_img)
model.invoke()

regressOut = model.get_tensor(output_details[0]['index'])
print('regression', regressOut)
classifyOut = model.get_tensor(output_details[1]['index'])
print('classify', classifyOut)
classifyOut = model.get_tensor(output_details[2]['index'])
print('classify', classifyOut)
