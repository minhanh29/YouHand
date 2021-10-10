import cv2
import json
import os
import mediapipe as mp
from encoder import KeyPoint, KeyPointList, Encoder
from model import EuclideanClassifier


# config
new_gesture = 'undefined'
gesture_dir = 'gestures'
isPredict = True
isUpdate = False
useMyDetector = False

# models
clf = EuclideanClassifier(gesture_dir)
mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1)

mpDraw = mp.solutions.drawing_utils
encoder = Encoder()
count = 0


def filter_keypoints(img, keypoints):
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


def detect_keypoints(img):
    results = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    if results.multi_hand_landmarks:
        for handlm in results.multi_hand_landmarks:
            my_points = filter_keypoints(img, handlm.landmark)
            keypointsList = KeyPointList(my_points)
            if isPredict:
                prediction = clf.predict(keypointsList.get_feature_list())

                org = my_points[0]
                cv2.rectangle(img, org.to_tuple(), (org.x+100, org.y+50),
                              (0, 0, 0), cv2.FILLED)
                cv2.putText(img, f"{prediction}", (org.x + 5, org.y + 30),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 2)

            if isUpdate:
                encoder.update(keypointsList.get_feature_list())
            keypointsList.draw_landmarks(img)
            # mpDraw.draw_landmarks(img, handlm, mpHands.HAND_CONNECTIONS)
    return img


cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
# cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)

while True:
    timer = cv2.getTickCount()
    success, frame = cap.read()

    if not success:
        continue

    img = cv2.flip(frame, 1)
    # info board
    cv2.rectangle(img, (0, 0), (150, 50), (0, 0, 0), cv2.FILLED)

    # imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # startTime = time.time()
    img = detect_keypoints(img)
    # endTime = time.time()
    # print("Process Time", endTime - startTime)

    fps = int(cv2.getTickFrequency() / (cv2.getTickCount() - timer))
    # old_time = new_time
    cv2.putText(img, f"FPS: {fps}", (5, 30), cv2.FONT_HERSHEY_COMPLEX,
                1, (0, 255, 0), 2)

    cv2.imshow("Img", img)

    keyPressed = cv2.waitKey(1)
    if keyPressed == ord('p'):
        isPredict = not isPredict
        if isPredict:
            print('\nTurned ON prediction mode.')
        else:
            print('\nTurned OFF prediction mode.')

    if keyPressed == ord('n'):
        print("Start")
        new_gesture = input("Enter new gesture name: ")
        print('Press S to start learning')

    if keyPressed == ord('s'):
        if not isUpdate:
            isUpdate = True
            print("Learning new gesture ...")

    if keyPressed == ord('d'):
        if isUpdate:
            feature = encoder.get_repr_feature()
            clf.add_feature(new_gesture, feature)
            isUpdate = False
            filename = f'{new_gesture}.json'
            save_path = os.path.join(gesture_dir, filename)
            with open(save_path, 'w') as f:
                json.dump(feature, f)
        print(f"Done. New gesture is saved to {save_path}")

    if keyPressed == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
