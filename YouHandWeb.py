import streamlit as st
import cv2
import numpy as np
import tempfile
import time
from PIL import Image


class AITrainingPage:
    def __init__(self):
        self.webcamKey = 'my_webcam_btn'

    def render(self, st):
        # use for switching between use and stop webcam
        if self.webcamKey not in st.session_state:
            st.session_state[self.webcamKey] = False

        img = Image.open('./tohka.jpeg')
        FRAME = st.image(img)

        if st.session_state[self.webcamKey]:
            stopWebcam = st.sidebar.button('Stop Webcam')
            st.session_state[self.webcamKey] = False

            cap = cv2.VideoCapture(0)
            while cap.isOpened():
                timer = cv2.getTickCount()
                success, frame = cap.read()

                if not success:
                    continue

                frame = cv2.flip(frame, 1)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                fps = int(cv2.getTickFrequency() / (cv2.getTickCount() - timer))
                cv2.putText(frame, f"FPS: {fps}", (5, 30), cv2.FONT_HERSHEY_COMPLEX,
                            1, (0, 255, 0), 2)

                FRAME.image(frame)

            if stopWebcam:
                cap.release()
        else:
            useWebcam = st.sidebar.button('Use Webcam')
            st.session_state[self.webcamKey] = True


st.title('YouHand | Customizable Gesture Recognizer')
st.subheader("AI Training")

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

st.sidebar.title("YouHand")
st.sidebar.subheader('Control Pannel')

my_modes = ['Train AI', 'Control Video']

appMode = st.sidebar.selectbox('Choose the app mode',
                               my_modes)

trainingPage = AITrainingPage()

if appMode == my_modes[0]:
    trainingPage.render(st)
    # st.markdown(
    #     """
    #     <style>
    #     [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
    #         width: 350px
    #     }
    #     [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
    #         width: 350px
    #         margin-left: -350px
    #     }
    #     </style>
    #     """,
    #     unsafe_allow_html=True
    # )

    # st.video('https://youtu.be/FvRy0QdbvZs')
    st.markdown("This web app is just a demo version of YouHand. Please download desktop app version to get full features.")

elif appMode == my_modes[1]:

    # use for switching between use and stop webcam
    webcamKey = 'my_webcam_btn'
    if webcamKey not in st.session_state:
        st.session_state[webcamKey] = False

    img = Image.open('')
    FRAME = st.image(img)

    if st.session_state[webcamKey]:
        stopWebcam = st.sidebar.button('Stop Webcam')
        st.session_state[webcamKey] = False

        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            timer = cv2.getTickCount()
            success, frame = cap.read()

            if not success:
                continue

            frame = cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            fps = int(cv2.getTickFrequency() / (cv2.getTickCount() - timer))
            cv2.putText(frame, f"FPS: {fps}", (5, 30), cv2.FONT_HERSHEY_COMPLEX,
                        1, (0, 255, 0), 2)

            FRAME.image(frame)

        if stopWebcam:
            cap.release()
    else:
        useWebcam = st.sidebar.button('Use Webcam')
        st.session_state[webcamKey] = True

    # if webCamBtn:
        # we are gonna stop it

        # else:
        #     if cap is not None:
        #         cap.release()

