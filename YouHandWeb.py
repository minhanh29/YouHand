import streamlit as st
import os
import sys
import cv2
import numpy as np
import time
from urllib.parse import urlparse, parse_qs
from PIL import Image
from ai.recognizer import RecognizerController
from database.database import MappingDatabase


def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)

    return os.path.join(datadir, filename)


def get_video_id(value):
    query = urlparse(value)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    # fail?
    return None


class MyWebCam:
    def __init__(self, webcam_key, cap_key, controller_key, frame_key):
        self.webcam_key = webcam_key
        self.cap_key = cap_key
        self.controller_key = controller_key
        self.frame_key = frame_key
        self.register_state()

    def register_state(self):
        # use for switching between use and stop webcam
        if self.frame_key not in st.session_state:
            st.session_state[self.frame_key] = None

    def open_webcam(self, window, commandHandler=None):
        # img = Image.open('media/modern_dashboard.png')
        FRAME = window.image(np.zeros((720, 1280, 3), dtype='uint8'))
        # FRAME = st.session_state[self.frame_key]
        # if FRAME is None:
            # FRAME = window.image(np.zeros((720, 1280, 3), dtype='uint8'))
            # st.session_state[self.frame_key] = FRAME

        cap = st.session_state[self.cap_key]
        if cap is None:
            cap = cv2.VideoCapture(0)
            st.session_state[self.cap_key] = cap

        controller = st.session_state[self.controller_key]
        while cap.isOpened():
            timer = cv2.getTickCount()
            success, frame = cap.read()

            if not success:
                continue

            frame = cv2.flip(frame, 1)
            frame, data = controller.detect_keypoints(frame)
            if commandHandler is not None:
                predictions, keypoints = data
                commandHandler.handle_prediction(predictions, keypoints)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            fps = int(cv2.getTickFrequency() / (cv2.getTickCount() - timer))
            cv2.putText(frame, f"FPS: {fps}", (5, 30), cv2.FONT_HERSHEY_COMPLEX,
                        1, (0, 255, 0), 2)

            FRAME.image(frame)

    def close_webcam(self, window):
        cap = st.session_state[self.cap_key]
        if cap is not None:
            cap.release()
            st.session_state[self.cap_key] = None

        img = Image.open('media/modern_dashboard.png')
        window.image(img)


class AITrainingPage:
    def __init__(self):
        self.train_key = 'my_training_state'
        self.webcam_key = 'my_webcam_state'
        self.cap_key = "my_cap_state"
        self.controller_key = "my_controller_key"
        self.frame_key = "train_frame_key"
        self.register_state()

        self.webcam = MyWebCam(self.webcam_key, self.cap_key,
                               self.controller_key, self.frame_key)

    def render(self):
        self.control_pannel()
        self.body()

    def register_state(self):
        # use for switching between use and stop webcam
        if self.webcam_key not in st.session_state:
            st.session_state[self.webcam_key] = False
        if self.train_key not in st.session_state:
            st.session_state[self.train_key] = False

        if self.cap_key not in st.session_state:
            st.session_state[self.cap_key] = None
        if self.controller_key not in st.session_state:
            st.session_state[self.controller_key] = RecognizerController()

    def control_pannel(self):
        # webcam button
        if st.session_state[self.webcam_key]:
            st.sidebar.button('Close Webcam',
                              on_click=self.disable_webcam)
        else:
            st.sidebar.button('Open Webcam',
                              on_click=self.enable_webcam)

        # train AI button
        if st.session_state[self.train_key]:
            st.sidebar.button("Stop Training",
                              on_click=self.disable_training)
        else:
            st.sidebar.button("Start Training",
                              on_click=self.enable_training)

    def body(self):
        if st.session_state[self.webcam_key]:
            # self.open_webcam()
            self.webcam.open_webcam(st)
        else:
            # self.close_webcam()
            self.webcam.close_webcam(st)

        if st.session_state[self.train_key]:
            self.start_training()
        else:
            self.stop_training()

    def enable_webcam(self):
        st.session_state[self.webcam_key] = True

    def disable_webcam(self):
        st.session_state[self.webcam_key] = False

    def enable_training(self):
        st.session_state[self.train_key] = True

    def disable_training(self):
        st.session_state[self.train_key] = False

    def start_training(self):
        print("Training")

    def stop_training(self):
        print("Stop training")


class ControlVideoPage:
    def __init__(self):
        self.connect_key = "connect_youtube"
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        self.component_path = os.path.join(parent_dir)
        self.component_key = "youtube_controller"
        self.vid_component = st.components.v1.declare_component("test", path=self.component_path)

        self.vid_url = ""
        self.load_key = "load_video"
        self.cmd_key = "control_video"
        self.payload_key = "payload_key"

        self.webcam_key = 'my_webcam_state'
        self.cap_key = "my_cap_state"
        self.controller_key = "my_controller_key"
        self.frame_key = "control_frame_key"

        # sending message to frontend
        self.latency_key = "control_latency"

        self.register_state()

        self.webcam = MyWebCam(self.webcam_key, self.cap_key,
                               self.controller_key, self.frame_key)
        self.static_db_path = os.path.join('database', 'static_command_db.json')
        self.static_db_path = find_data_file(self.static_db_path)

        self.command_db = MappingDatabase(self.static_db_path)
        self.commandHandler = CommandHandler(self.command_db, self)

    def register_state(self):
        if self.load_key not in st.session_state:
            st.session_state[self.load_key] = False
        if self.cmd_key not in st.session_state:
            st.session_state[self.cmd_key] = False
        if self.webcam_key not in st.session_state:
            st.session_state[self.webcam_key] = False
        if self.cap_key not in st.session_state:
            st.session_state[self.cap_key] = None
        if self.controller_key not in st.session_state:
            st.session_state[self.controller_key] = RecognizerController()

        if self.payload_key not in st.session_state:
            st.session_state[self.payload_key] = False
        if self.latency_key not in st.session_state:
            st.session_state[self.latency_key] = time.time()

    def render(self):
        self.control_pannel()
        self.body()
        self.webcam.open_webcam(st.sidebar, self.commandHandler)

    def control_pannel(self):
        self.vid_url = st.sidebar.text_input("YouTube URL", "")
        st.sidebar.button("Connect",
                          self.connect_key,
                          on_click=self.connect_youtube)

    def body(self):
        if st.session_state[self.load_key]:
            cmd_payload = st.session_state[self.payload_key]
            self.vid_component(cmd_type="load",
                               cmd_payload=cmd_payload,
                               key=self.component_key)
            st.session_state[self.load_key] = False
        elif st.session_state[self.cmd_key]:
            # vid_id = get_video_id(self.vid_url)
            cmd_payload = st.session_state[self.payload_key]
            self.vid_component(cmd_type="control",
                               cmd_payload=cmd_payload,
                               key=self.component_key)
            st.session_state[self.cmd_key] = False
        else:
            self.vid_component(key=self.component_key)

    def connect_youtube(self):
        st.session_state[self.load_key] = True
        st.session_state[self.cmd_key] = False
        st.session_state[self.payload_key] = get_video_id(self.vid_url)
        # print("Url", self.vid_url)
        # print("Id", vid_id)

    def enable_cmd(self):
        st.session_state[self.cmd_key] = True
        st.session_state[self.load_key] = False
        self.commandHandler.update_state()
        if time.time() - st.session_state[self.latency_key] > 0.3:
            st.session_state[self.latency_key] = time.time()
            st.experimental_rerun()

    def play(self):
        st.session_state[self.payload_key] = "0"
        self.enable_cmd()

    def pause(self):
        st.session_state[self.payload_key] = "1"
        self.enable_cmd()

    def forward10s(self):
        print("forward")
        st.session_state[self.payload_key] = "2"
        self.enable_cmd()

    def backward10s(self):
        st.session_state[self.payload_key] = "3"
        self.enable_cmd()

    def increaseVol(self):
        st.session_state[self.payload_key] = "4"
        self.enable_cmd()

    def decreaseVol(self):
        st.session_state[self.payload_key] = "5"
        self.enable_cmd()

    def fullscreen(self):
        st.session_state[self.payload_key] = "6"
        self.enable_cmd()

    def skip_ad(self):
        st.session_state[self.payload_key] = "7"
        self.enable_cmd()


class CommandHandler:
    def __init__(self, command_db, youtubeController):
        self.command_db = command_db
        self.youtubeController = youtubeController

        self.keypoints_key = "cmd_keypoints_key"
        self.isSeeking_key = "cmd_isSeeking_key"
        self.isVol_key = "cmd_isVol_key"
        self.seekTimer_key = "cmd_seekTimer_key"
        self.fullscreenTimer_key = "cmd_fullscreenTimer_key"
        self.isCommanding_key = "cmd_isCommanding_key"
        self.stopTimer_key = "cmd_stopTimer_key"
        self.firstPos_key = "cmd_firstPos"

        # self.keypoints = None
        # self.isSeeking = False
        # self.isVol = False
        # self.seekTimer = 0  # seeking needs some delays in between
        # self.fullscreenTimer = 0
        # self.isCommanding = False
        # self.stopTimer = 0

        self.register_state()
        self.retrieve_state()

    def register_state(self):
        if self.keypoints_key not in st.session_state:
            st.session_state[self.keypoints_key] = None
        if self.isSeeking_key not in st.session_state:
            st.session_state[self.isSeeking_key] = False
        if self.isVol_key not in st.session_state:
            st.session_state[self.isVol_key] = False
        if self.seekTimer_key not in st.session_state:
            st.session_state[self.seekTimer_key] = 0
        if self.fullscreenTimer_key not in st.session_state:
            st.session_state[self.fullscreenTimer_key] = 0
        if self.isCommanding_key not in st.session_state:
            st.session_state[self.isCommanding_key] = False
        if self.stopTimer_key not in st.session_state:
            st.session_state[self.stopTimer_key] = 0
        if self.firstPos_key not in st.session_state:
            st.session_state[self.firstPos_key] = None

    def retrieve_state(self):
        self.keypoints = st.session_state[self.keypoints_key]
        self.isSeeking = st.session_state[self.isSeeking_key]
        self.isVol = st.session_state[self.isVol_key]
        self.seekTimer = st.session_state[self.seekTimer_key]
        self.fullscreenTimer = st.session_state[self.fullscreenTimer_key]
        self.isCommanding = st.session_state[self.isCommanding_key]
        self.stopTimer = st.session_state[self.stopTimer_key]
        self.firstPos = st.session_state[self.firstPos_key]

    def update_state(self):
        st.session_state[self.keypoints_key] = self.keypoints
        st.session_state[self.isSeeking_key] = self.isSeeking
        st.session_state[self.isVol_key] = self.isVol
        st.session_state[self.seekTimer_key] = self.seekTimer
        st.session_state[self.fullscreenTimer_key] = self.fullscreenTimer
        st.session_state[self.isCommanding_key] = self.isCommanding
        st.session_state[self.stopTimer_key] = self.stopTimer
        st.session_state[self.firstPos_key] = self.firstPos

    def handle_prediction(self, predictions, keypoints):
        if self.isCommanding and len(keypoints) == 0:
            if time.time() - self.stopTimer > 0.5:
                # print('Stop command')
                self.isCommanding = False
                self.disable_all()
            return

        self.stopTimer = time.time()
        self.keypoints = keypoints

        for prediction in predictions:
            self.bind_command(prediction)

    def bind_command(self, gesture):
        # get the corresponding command
        command = self.command_db.get_command(gesture)

        # check if there is a valid hand on the screen
        if command == 'indicator':
            if not self.isCommanding:
                self.isCommanding = True
                # print('Start command')
            self.disable_all()

        if not self.isCommanding:
            return

        if command == 'pause':
            self.youtubeController.pause()
            return

        elif command == 'play':
            self.youtubeController.play()
            return

        elif command == 'skip_ad':
            self.youtubeController.skip_ad()
            return

        elif command == 'fullscreen':
            if time.time() - self.fullscreenTimer < 2:
                return
            self.fullscreenTimer = time.time()
            self.youtubeController.fullscreen()

        elif command == 'forward':
            if not self.isSeeking:
                self.disable_all()
            self.handle_forward()
            return

        elif command == 'backward':
            if not self.isSeeking:
                self.disable_all()
            self.handle_backward()
            return

        elif command == 'volume':
            if not self.isVol:
                self.disable_all()
            self.handle_volume()
            return

    # disable all modes: seeking, vol, ...
    def disable_all(self):
        self.isSeeking = False
        self.isVol = False

    def handle_forward(self):
        if self.keypoints is None:
            return

        # start seeking
        if not self.isSeeking:
            if time.time() - self.seekTimer < 0.3:  # still in delay
                return
            self.seekTimer = time.time()
            # print("start seeking")
            self.isSeeking = True
            self.firstPos = self.keypoints[6]

        # if time.time() - self.seekTimer > 5:  # expire, reset
        #     self.firstPos = self.keypoints[0]
        #     self.seekTimer = time.time()

        # get the index finger tip
        currentPos = self.keypoints[6]

        # compute moving distance
        # focus on x axis
        distance = abs(currentPos.x - self.firstPos.x)

        knuckle = self.keypoints[4]
        base_distance = np.linalg.norm([
            currentPos.x - knuckle.x,
            currentPos.y - knuckle.y
        ])
        # print('dis', distance)
        # print('Base', base_distance)

        # start job
        if distance > base_distance * 2/3.0:
            # compute the direction
            direction = currentPos.x - self.firstPos.x
            # go right
            if direction > 0:
                self.youtubeController.forward10s()
            self.isSeeking = False

    def handle_backward(self):
        if self.keypoints is None:
            return

        # start seeking
        if not self.isSeeking:
            if time.time() - self.seekTimer < 0.3:  # still in delay
                return
            self.seekTimer = time.time()
            # print("start seeking")
            self.isSeeking = True
            self.firstPos = self.keypoints[6]

        # if time.time() - self.seekTimer > 5:  # expire, reset
        #     self.firstPos = self.keypoints[0]
        #     self.seekTimer = time.time()

        # get the index finger tip
        currentPos = self.keypoints[6]

        # compute moving distance
        # focus on x axis
        distance = abs(currentPos.x - self.firstPos.x)

        knuckle = self.keypoints[4]
        base_distance = np.linalg.norm([
            currentPos.x - knuckle.x,
            currentPos.y - knuckle.y
        ])
        # print('dis', distance)
        # print('Base', base_distance)

        # start job
        if distance > base_distance * 2/3.0:
            # compute the direction
            direction = currentPos.x - self.firstPos.x
            # go right
            if direction < 0:
                self.youtubeController.backward10s()
            self.isSeeking = False
            self.seekTimer = time.time()

    def handle_volume(self):
        if self.keypoints is None:
            return

        # start seeking
        if not self.isVol:
            # print("start vol")
            self.isVol = True
            self.firstPos = self.keypoints[6]

        # get the index finger tip
        currentPos = self.keypoints[6]

        # compute moving distance
        # focus on y axis
        distance = abs(currentPos.y - self.firstPos.y)

        knuckle = self.keypoints[4]
        base_distance = np.linalg.norm([
            currentPos.x - knuckle.x,
            currentPos.y - knuckle.y
        ])

        # start job
        if distance > base_distance * 0.15:
            # compute the direction
            direction = currentPos.y - self.firstPos.y
            # go down
            if direction > 0:
                self.youtubeController.decreaseVol()
            # go up
            else:
                self.youtubeController.increaseVol()
            self.isVol = False

st.title('YouHand | Customizable Gesture Recognizer')

st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        width: 350px
    }
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
        width: 350px
        margin-left: -350px
    }
    </style>
    """,
    unsafe_allow_html=True
)

rerun_key = "rerun_key"
if rerun_key not in st.session_state:
    st.session_state[rerun_key] = True
    print("first ru run")
    st.experimental_rerun()

st.sidebar.title("YouHand")
st.sidebar.subheader('Control Pannel')

my_modes = ['Train AI', 'Control Video']

appMode = st.sidebar.selectbox('Choose the app mode',
                               my_modes, index=1)


# control_webcam_key = 'my_webcam_state'
# control_cap_key = "my_cap_state"

if appMode == my_modes[0]:
    # if control_cap_key in st.session_state:
    #     cap = st.session_state[control_cap_key]
    #     if cap is not None:
    #         cap.release()
    #         st.session_state[control_cap_key] = None

    st.subheader("AI Training")
    trainingPage = AITrainingPage()
    trainingPage.render()

    # st.video('https://youtu.be/FvRy0QdbvZs')
    st.markdown("This web app is just a demo version of YouHand. Please download desktop app version to get full features.")

elif appMode == my_modes[1]:
    st.subheader("Video Controlling")
    control_page = ControlVideoPage()
    control_page.render()
    # test = st.sidebar.button("test")
    # parent_dir = os.path.dirname(os.path.abspath(__file__))
    # build_dir = os.path.join(parent_dir)
    # my_component = st.components.v1.declare_component("test", path=build_dir)
    # if test:
    #     my_component(ytb_cmd="0", key="1")
    # else:
    #     my_component(key="1")

    # HtmlFile = open("video_component.html", 'r', encoding='utf-8')
    # source_code = HtmlFile.read()
    # if test:
    #     print("test")
    #     source_code = source_code.replace("//my_func", "playVideo()")
    # my_component = st.components.v1.html(source_code, 640, 400)
    # result = my_component(my_args="Minh Anh")
    # print(result)
