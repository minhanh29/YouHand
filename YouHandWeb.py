import streamlit as st
from st_pages import AITrainingPage, ControlVideoPage
from PIL import Image


st.title('YouHand | Nguyen Minh Anh')

st.markdown(
    """
    <style>
    [data-testid="st"][aria-expanded="true"] > div:first-child {
        margin-top: 50px
    }
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

my_modes = ['AI Training', 'Video Controlling']

appMode = st.sidebar.selectbox('Choose the app mode',
                               my_modes, index=1)


if appMode == my_modes[0]:
    st.subheader("AI Training")
    st.markdown("**Turn on** the webcam below to start training.")
    trainingPage = AITrainingPage()
    trainingPage.render()

    st.markdown("This web app is just a demo version of YouHand. Please download desktop app version to get full features.")

elif appMode == my_modes[1]:
    st.subheader("Video Controlling")
    control_page = ControlVideoPage()
    control_page.render()
    st.markdown("If you **cannot connect** to another video, try **turning off** the webcam and **reloading** the page.")
    st.markdown("Note that **automatic fullscreen** is **limited** by JS to prevent hacking. If it does not work, please **manually interact** with the video and try again.")

    st.subheader("Default Gestures")
    st.markdown("Go to **AI Training** section to create your own gestures.")
    st.image(Image.open("media/built_in_gestures.png"))

