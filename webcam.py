import av
import cv2
import time
import queue
from typing import NamedTuple
import streamlit as st
from ai.recognizer import RecognizerController
from streamlit_webrtc import (
    RTCConfiguration,
    VideoProcessorBase,
    WebRtcMode,
    webrtc_streamer,
)
from streamlit_webrtc.config import VideoHTMLAttributes


class AITrainVideoProcessor(VideoProcessorBase):
    start_training: bool
    stop_training: bool
    is_training: bool
    new_gesture: str

    def __init__(self):
        self.controller = RecognizerController()
        self.start_training = False
        self.stop_training = False
        self.is_training = True
        self.new_gesture = "new_gesture"
        print("create")

    def recv(self, frame: av.VideoFrame):
        timer = cv2.getTickCount()
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)

        if self.start_training:
            print("start train")
            self.controller.new_gesture = self.new_gesture.lower()
            self.controller.isPredict = False
            self.controller.isUpdate = True
            self.start_training = False
            self.is_training = True

        if self.stop_training:
            self.stop_training = False
            self.is_training = False
            self.controller.isPredict = True
            message = self.controller.save_gesture()
            print("Mess", message)

        # controller = st.session_state[self.controller_key]
        img, data = self.controller.detect_keypoints(img)
        fps = int(cv2.getTickFrequency() / (cv2.getTickCount() - timer))
        cv2.putText(img, f"FPS: {fps}", (5, 30), cv2.FONT_HERSHEY_COMPLEX,
                    1, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


class Detection(NamedTuple):
    preds: list
    keypoints: list


class ControlVideoProcessor(VideoProcessorBase):
    result_queue: "queue.Queue[Detection]"

    def __init__(self):
        self.controller = RecognizerController()
        self.result_queue = queue.Queue()

    def recv(self, frame: av.VideoFrame):
        timer = cv2.getTickCount()
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)

        # controller = st.session_state[self.controller_key]
        img, data = self.controller.detect_keypoints(img)
        result = Detection(preds=data[0], keypoints=data[1])
        self.result_queue.put(result)

        fps = int(cv2.getTickFrequency() / (cv2.getTickCount() - timer))
        cv2.putText(img, f"FPS: {fps}", (5, 30), cv2.FONT_HERSHEY_COMPLEX,
                    1, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def enable_cmd(self):
        st.session_state[self.cmd_key] = True
        st.session_state[self.load_key] = False
        self.commandHandler.update_state()
        if time.time() - st.session_state[self.latency_key] > 0.3:
            st.session_state[self.latency_key] = time.time()
            st.experimental_rerun()

    def play(self):
        print("play")
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


class MyWebCamRTC:
    def __init__(self, processor, key, vid_config=None):
        self.config = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
        self.processor = processor
        self.key = key
        if vid_config:
            self.vid_config = vid_config
        else:
            self.vid_config = VideoHTMLAttributes(
                autoPlay=True, controls=False, style={"width": "100%"}
            )

    def render(self):
        return webrtc_streamer(
            key=self.key,
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=self.config,
            video_processor_factory=self.processor,
            async_processing=True,
            sendback_audio=False,
            video_html_attrs=self.vid_config
        )

