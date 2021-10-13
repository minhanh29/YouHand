import streamlit as st
from st_pages import AITrainingPage, ControlVideoPage


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
