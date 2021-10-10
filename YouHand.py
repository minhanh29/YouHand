import tkinter as tk
from tkinter import simpledialog
import tkinter.messagebox
from PIL import ImageTk, Image
import numpy as np
import time
import cv2
import math
import os
import sys
from ai.recognizer import RecognizerController
from database.database import MappingDatabase
from widgets.dialog import UrlInputDialog, MyGestureMenuDialog
from widgets.custom_button import HandCustomButton


WIDTH = 854
HEIGHT = 480


def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)

    return os.path.join(datadir, filename)


class HandRecognizer:
    def __init__(self):
        # colors
        self.background_color = '#2b2a2b'
        self.foreground_color = '#f2f2f2'

        self.youtubeController = None
        # self.command_db = MappingDatabase('command_db.json')
        self.static_db_path = os.path.join('database', 'static_command_db.json')
        self.static_db_path = find_data_file(self.static_db_path)

        self.command_db = MappingDatabase(self.static_db_path)
        self.commandHandler = CommandHandler(self.command_db,
                                             self.youtubeController)
        self.startTime = 0
        self.isCountDown = False

        self.cap = None
        self.showCam = True
        self.main_window = tk.Tk()
        self.main_window.config(bg=self.background_color)
        self.main_window.title("YouHand | Hand Gesture Recognizer")
        # self.main_window.overrideredirect(True)
        self.main_window.geometry(f"{WIDTH+200}x{HEIGHT+20}+100+100")
        # self.main_window.iconbitmap("app_icon.icns")

        # self.title_bar = tk.Frame(self.main_window, bg='black', relief='raised', bd=2)
        # self.title_label = tk.Label(self.title_bar, text="Minh Anh")
        # self.title_label.pack()

        btn_width = 150
        btn_height = 60
        check_btn_size = (150, 25)
        self.image_factory = {
            "dashboard": ImageTk.PhotoImage(Image.open(find_data_file('media/modern_dashboard.png'))),
            "frozen": ImageTk.PhotoImage(Image.open(find_data_file('media/frozen.png'))),
            "activate": ImageTk.PhotoImage(Image.open(find_data_file("media/activate_btn.png")).resize((btn_width, btn_height))),
            "activate_hover": ImageTk.PhotoImage(Image.open(find_data_file("media/activate_btn_hover.png")).resize((btn_width, btn_height))),
            "deactivate": ImageTk.PhotoImage(Image.open(find_data_file("media/deactivate_btn.png")).resize((btn_width, btn_height))),
            "deactivate_hover": ImageTk.PhotoImage(Image.open(find_data_file("media/deactivate_btn_hover.png")).resize((btn_width, btn_height))),
            "open_youtube": ImageTk.PhotoImage(Image.open(find_data_file("media/open_youtube.png")).resize((btn_width, btn_height))),
            "open_youtube_hover": ImageTk.PhotoImage(Image.open(find_data_file("media/open_youtube_hover.png")).resize((btn_width, btn_height))),
            "close_youtube": ImageTk.PhotoImage(Image.open(find_data_file("media/close_youtube.png")).resize((btn_width, btn_height))),
            "close_youtube_hover": ImageTk.PhotoImage(Image.open(find_data_file("media/close_youtube_hover.png")).resize((btn_width, btn_height))),
            "manager": ImageTk.PhotoImage(Image.open(find_data_file("media/manager.png")).resize((btn_width, btn_height))),
            "manager_hover": ImageTk.PhotoImage(Image.open(find_data_file("media/manager_hover.png")).resize((btn_width, btn_height))),
            "done": ImageTk.PhotoImage(Image.open(find_data_file("media/done.png")).resize((btn_width, btn_height))),
            "done_hover": ImageTk.PhotoImage(Image.open(find_data_file("media/done_hover.png")).resize((btn_width, btn_height))),
            "keypoint_checked": ImageTk.PhotoImage(Image.open(find_data_file("media/keypoint_checked.png")).resize(check_btn_size)),
            "keypoint_unchecked": ImageTk.PhotoImage(Image.open(find_data_file("media/keypoint_unchecked.png")).resize(check_btn_size)),
            "camera_checked": ImageTk.PhotoImage(Image.open(find_data_file("media/camera_checked.png")).resize(check_btn_size)),
            "camera_unchecked": ImageTk.PhotoImage(Image.open(find_data_file("media/camera_unchecked.png")).resize(check_btn_size)),
            "num_hand": ImageTk.PhotoImage(Image.open(find_data_file("media/num_hand_label.png")).resize((132, 22))),
            "classifiers": ImageTk.PhotoImage(Image.open(find_data_file("media/classifier_label.png")).resize((69,  20))),
        }

        # main frames
        self.left_frame = tk.Frame(self.main_window)
        self.left_frame.config(bg=self.background_color)
        self.right_frame = tk.Frame(self.main_window)
        self.right_frame.config(bg=self.background_color)

        # input field
        self.canvas = tk.Canvas(self.left_frame, width=WIDTH, height=HEIGHT,
                                bg=self.background_color,
                                highlightbackground=self.background_color)
        self.image_on_canvas = self.canvas.create_image(10, 10,
                                                        anchor=tk.NW,
                                                        image=self.image_factory["dashboard"])
        self.canvas.pack()
        self.vid = None
        self.delay = 15
        self.stopVideo = False
        self.controller = RecognizerController()

        self.sliderLabel = tk.Label(self.right_frame,
                                    image=self.image_factory["num_hand"],
                                    bg=self.background_color)
        self.slider = tk.Scale(self.right_frame, from_=1, to=4,
                               tickinterval=1, orient=tk.HORIZONTAL,
                               command=self.update_slider_val,
                               bg=self.background_color,
                               fg=self.foreground_color,
                               highlightbackground=self.background_color,
                               bd=0)
        self.sliderLabel.pack()
        self.slider.pack()

        # radio buttons - classifier choice
        # classifier
        self.classifier_choice = tk.StringVar(self.right_frame, "Linear")
        self.classifiers = {
            "Linear": "linear",
            "Logistic": "logistic",
            "Euclidean": "euclidean",
            "Random Forest": "random_forest",
        }
        self.dropdown_frame = tk.Frame(self.right_frame)
        self.dropdown_frame.config(bg=self.background_color)
        self.dropdown_label = tk.Label(self.dropdown_frame,
                                       image=self.image_factory["classifiers"],
                                       bg=self.background_color)
        self.dropdown_menu = tk.OptionMenu(self.dropdown_frame,
                                           self.classifier_choice,
                                           *list(self.classifiers.keys()),
                                           command=self.change_classifier)
        self.dropdown_menu.config(fg=self.background_color, bd=0, bg=self.background_color)
        self.dropdown_label.pack(side='left')
        self.dropdown_menu.pack(side='left')
        self.dropdown_frame.pack(pady=15)

        # checkboxes
        self.checkbox_frame = tk.Frame(self.right_frame)
        self.checkbox_frame.config(bg=self.background_color)
        # self.predict_var = tk.IntVar(value=1)
        self.keypoint_var = tk.IntVar(value=1)
        self.hidecam_var = tk.IntVar(value=0)
        self.keypoint_checkbox = tk.Checkbutton(self.checkbox_frame,
                                                indicator=False,
                                                image=self.image_factory["keypoint_unchecked"],
                                                selectimage=self.image_factory["keypoint_checked"],
                                                variable=self.keypoint_var,
                                                onvalue=1, offvalue=0,
                                                command=self.keypoint_change,
                                                bg=self.background_color,
                                                fg=self.background_color,
                                                selectcolor=self.background_color,
                                                activebackground=self.background_color,
                                                bd=0,
                                                highlightbackground=self.background_color)
        self.showcam_checkbox = tk.Checkbutton(self.checkbox_frame,
                                               indicator=False,
                                               image=self.image_factory["camera_unchecked"],
                                               selectimage=self.image_factory["camera_checked"],
                                               variable=self.hidecam_var,
                                               onvalue=1, offvalue=0,
                                               command=self.hidecam_change,
                                               bd=0,
                                               selectcolor=self.background_color,
                                               activebackground=self.background_color,
                                               bg=self.background_color,
                                               fg=self.background_color,
                                               highlightbackground=self.background_color)
        # self.predict_checkbox.pack(pady=5)
        self.keypoint_checkbox.pack(pady=5, padx=5)
        self.showcam_checkbox.pack(pady=5, padx=5)
        self.checkbox_frame.pack(pady=0)

        # buttons
        self.videoCap_btn = HandCustomButton(master=self.right_frame,
                                             image=self.image_factory["activate"],
                                             image_hover=self.image_factory["activate_hover"],
                                             command=self.enable_video)
        self.youtube_btn = HandCustomButton(master=self.right_frame,
                                            image=self.image_factory["open_youtube"],
                                            image_hover=self.image_factory["open_youtube_hover"],
                                            command=self.connectYoutube)
        self.manager_btn = HandCustomButton(master=self.right_frame,
                                            image=self.image_factory["manager"],
                                            image_hover=self.image_factory["manager_hover"],
                                            command=self.show_gesture)
        self.videoCap_btn.pack(pady=5, padx=10)
        self.youtube_btn.pack(pady=5, padx=10)
        self.manager_btn.pack(pady=5, padx=10)

        # arrage the frames
        # self.title_bar.pack(expand=1, fill=tk.X)
        self.left_frame.pack(side='left')
        self.right_frame.pack(side='left', pady=10, padx=5)

        # enter the main loop
        self.main_window.mainloop()

    def update_slider_val(self, value):
        value = int(value)
        self.controller.set_max_hands(value)

    def change_classifier(self, choice):
        self.controller.change_classifer(self.classifiers[choice])

    # def predict_change(self):
    #     self.controller.isPredict = self.predict_var.get() == 1

    def keypoint_change(self):
        self.controller.show_keypoint = self.keypoint_var.get() == 1

    def hidecam_change(self):
        self.showCam = self.hidecam_var.get() == 0

    def show_gesture(self):
        MyGestureMenuDialog(self.main_window, 'Gesture Manager',
                            self.controller, self, self.command_db)

    def show_count_down(self, img):
        duration = time.time() - self.startTime
        if duration > 3:
            # self.manager_btn.custom_configure(image=self.image_factory["done"],
            #                                   image_hover=self.image_factory["done_hover"],
            #                                   command=self.finish_learning)
            # learn new gesture
            self.controller.isPredict = False
            # self.predict_var.set(0)
            if self.controller.mode == RecognizerController.DYNAMIC:
                self.controller.trainDynamic = True
            else:
                self.controller.isUpdate = True
            self.isCountDown = False
            return img

        currentSecond = str(3 - int(math.floor(duration)))
        x = int(img.shape[1]/2)
        y = int(img.shape[0]/2) + 10
        cv2.putText(img, currentSecond, (x, y), cv2.FONT_HERSHEY_COMPLEX, 4,
                    (0, 0, 255), 5)
        return img

    def add_gesture(self):
        if self.vid is None:
            tk.messagebox.showerror('Error',
                                    "Please turn ON Video Capture first.",
                                    icon="error")
            return False

        if self.youtubeController is not None:
            tk.messagebox.showerror('Error',
                                    "Please turn OFF Youtube Video.")
            return False

        new_gesture = simpledialog.askstring("Add Gesture",
                                             "Enter your gesture name:",
                                             parent=self.main_window)
        if new_gesture is not None:
            # start count down
            self.startTime = time.time()
            self.isCountDown = True
            self.controller.new_gesture = new_gesture.lower()
            self.manager_btn.custom_configure(image=self.image_factory["done"],
                                              image_hover=self.image_factory["done_hover"],
                                              command=self.finish_learning)
            return True
        return False

    def update_gesture(self, gesture):
        if self.vid is None:
            tk.messagebox.showerror('Error',
                                    "Please turn ON Video Capture first.")
            return False

        if self.youtubeController is not None:
            tk.messagebox.showerror('Error',
                                    "Please turn OFF Youtube Video.")
            return False

        # learn new gesture
        # start count down
        self.startTime = time.time()
        self.isCountDown = True
        self.controller.delete_gesture(gesture)
        self.controller.new_gesture = gesture.lower()
        return True

    def finish_learning(self):
        self.controller.isPredict = True
        # self.predict_var.set(1)
        message = self.controller.save_gesture()
        tk.messagebox.showinfo('Gesture saved', message)
        self.manager_btn.custom_configure(image=self.image_factory["manager"],
                                          image_hover=self.image_factory["manager_hover"],
                                          command=self.show_gesture)

    def connectYoutube(self):
        UrlInputDialog(self.main_window, 'Youtube URL', self)

    def change_youtube_btn(self):
        self.commandHandler.youtubeController = self.youtubeController
        self.youtube_btn.custom_configure(image=self.image_factory["close_youtube"],
                                          image_hover=self.image_factory["close_youtube_hover"],
                                          command=self.stop_youtube)
        # self.youtube_btn.configure(text="Close Youtube",
        #                            command=self.stop_youtube,
        #                            fg='red')

    def stop_youtube(self):
        self.youtubeController.close()
        self.youtubeController = None
        self.commandHandler.youtubeController = None
        self.youtube_btn.custom_configure(image=self.image_factory["open_youtube"],
                                          image_hover=self.image_factory["open_youtube_hover"],
                                          command=self.connectYoutube)
        # self.youtube_btn.configure(text="Connect Youtube",
        #                            command=self.connectYoutube,
        #                            fg='orange')

    def stop_vid(self):
        self.stopVideo = True
        self.canvas.itemconfig(self.image_on_canvas,
                               anchor=tk.NW,
                               image=self.image_factory["dashboard"])
        self.videoCap_btn.custom_configure(image=self.image_factory["activate"],
                                           image_hover=self.image_factory["activate_hover"],
                                           command=self.enable_video)

    def enable_video(self):
        if self.vid is None:
            self.vid = MyVideoCapture()
        self.stopVideo = False
        self.videoCap_btn.custom_configure(image=self.image_factory["deactivate"],
                                           image_hover=self.image_factory["deactivate_hover"],
                                           command=self.stop_vid)
        self.vid_update()

    def vid_update(self):
        if self.stopVideo:
            del self.vid
            self.vid = None
            return

        timer = cv2.getTickCount()
        ret, frame = self.vid.get_frame()
        if ret:
            frame, data = self.controller.detect_keypoints(frame)

            if self.showCam:
                fps = int(cv2.getTickFrequency() / (cv2.getTickCount() - timer))
                cv2.rectangle(frame, (0, 0), (200, 50),
                              (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, f"FPS: {fps}", (5, 40),
                            cv2.FONT_HERSHEY_COMPLEX,
                            1.5, (0, 0, 0), 2)

                if self.isCountDown:
                    frame = self.show_count_down(frame)

                imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                imgRGB = cv2.resize(imgRGB, (WIDTH, HEIGHT))
                self.new_img = ImageTk.PhotoImage(Image.fromarray(imgRGB))
            else:
                self.new_img = self.image_factory["frozen"]

            self.canvas.itemconfig(self.image_on_canvas,
                                   anchor=tk.NW,
                                   image=self.new_img)

            if self.youtubeController is not None:
                predictions, keypoints = data
                self.commandHandler.handle_prediction(predictions, keypoints)
        else:
            self.stop_vid()
            tk.messagebox.showerror('Error', "Cannot open camera. Please try again.")
        self.main_window.after(self.delay, self.vid_update)


class MyVideoCapture:
    def __init__(self):
        while True:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            if self.cap.isOpened():
                break

    def get_frame(self):
        if not self.cap.isOpened():
            return False, None

        success, frame = self.cap.read()
        if success:
            frame = cv2.flip(frame, 1)
            return success, frame

        return success, None

    def __del__(self):
        if self.cap.isOpened():
            self.cap.release()


class CommandHandler:
    def __init__(self, command_db, youtubeController):
        self.command_db = command_db
        self.youtubeController = youtubeController

        self.keypoints = None
        self.isSeeking = False
        self.isVol = False
        self.seekTimer = 0  # seeking needs some delys in between
        self.fullscreenTimer = 0
        self.isCommanding = False
        self.stopTimer = 0

    def handle_prediction(self, predictions, keypoints):
        if self.isCommanding and len(keypoints) == 0:
            if time.time() - self.stopTimer > 0.5:
                print('Stop command')
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
                print('Start command')
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

    def handle_seeking(self, seek_type):
        if self.keypoints is None:
            return

        # start seeking
        if not self.isSeeking:
            if time.time() - self.seekTimer < 0.7:  # still in delay
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
                if seek_type == '5s':
                    self.youtubeController.forward5s()
                elif seek_type == '10s':
                    self.youtubeController.forward10s()
            # go left
            else:
                if seek_type == '5s':
                    self.youtubeController.backward5s()
                elif seek_type == '10s':
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


HandRecognizer()
