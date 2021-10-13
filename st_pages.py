import streamlit as st
import os
import queue
import sys
import cv2
import numpy as np
import time
from urllib.parse import urlparse, parse_qs
from PIL import Image
from ai.recognizer import RecognizerController
from database.database import MappingDatabase
from webcam import MyWebCamRTC, ControlVideoProcessor, AITrainVideoProcessor
from streamlit_webrtc.config import VideoHTMLAttributes


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


class AITrainingPage:
    def __init__(self):
        self.train_key = 'my_training_state'
        self.new_gesture = ""
        self.register_state()

        self.webcam = MyWebCamRTC(AITrainVideoProcessor)

    def render(self):
        self.control_pannel()
        self.body()

    def register_state(self):
        # use for switching between use and stop webcam
        if self.train_key not in st.session_state:
            st.session_state[self.train_key] = False

    def control_pannel(self):
        self.new_gesture = st.sidebar.text_input("YouTube URL", "")
        if st.session_state[self.train_key]:
            st.sidebar.button("Stop Training",
                              on_click=self.disable_training)
        else:
            st.sidebar.button("Start Training",
                              on_click=self.enable_training)

    def body(self):
        self.webcam.render()

        if st.session_state[self.train_key]:
            self.start_training()
        else:
            self.stop_training()

    def enable_training(self):
        if self.new_gesture == "":
            st.sidebar.error("Please enter your gesture name before training.")
            return

        st.session_state[self.train_key] = True

    def disable_training(self):
        st.session_state[self.train_key] = False

    def start_training(self):
        print("training")

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

        # sending message to frontend
        self.latency_key = "control_latency"

        self.register_state()

        # self.webcam = MyWebCam(self.webcam_key, self.cap_key,
        #                        self.controller_key, self.frame_key)
        vid_config = VideoHTMLAttributes(
            autoPlay=True, controls=False, style={"width": "30%",
                                                  "height": "auto",
                                                  "text-align": "center",
                                                  "margin-left": "auto",
                                                  "margin-right": "auto"
                                                  }
        )
        self.webcam = MyWebCamRTC(ControlVideoProcessor, vid_config)
        self.static_db_path = os.path.join('database', 'static_command_db.json')
        self.static_db_path = find_data_file(self.static_db_path)

        self.command_db = MappingDatabase(self.static_db_path)
        self.commandHandler = CommandHandler(self.command_db, self)

    def register_state(self):
        if self.load_key not in st.session_state:
            st.session_state[self.load_key] = False
        if self.cmd_key not in st.session_state:
            st.session_state[self.cmd_key] = False

        if self.payload_key not in st.session_state:
            st.session_state[self.payload_key] = False
        if self.latency_key not in st.session_state:
            st.session_state[self.latency_key] = time.time()

    def render(self):
        self.control_pannel()
        self.body()
        webrtc_ctx = self.webcam.render()
        while True:
            processor = webrtc_ctx.video_processor
            if processor is not None:
                try:
                    result = processor.result_queue.get(timeout=0.3)
                    self.commandHandler.handle_prediction(result.preds, result.keypoints)
                except queue.Empty:
                    result = None

                if result is None:
                    break
            else:
                break

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
        if self.vid_id == "":
            st.sidebar.error("Please enter your gesture name before training.")
            return
        st.session_state[self.load_key] = True
        st.session_state[self.cmd_key] = False
        st.session_state[self.payload_key] = get_video_id(self.vid_url)

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