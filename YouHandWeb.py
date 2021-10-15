import streamlit as st
from st_pages import AITrainingPage, ControlVideoPage


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
    st.markdown("If you **cannot connect** to another video, try **turning off** the webcam and **reload** the page.")

