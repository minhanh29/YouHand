from selenium import webdriver
import sys
import os
import re
from selenium.webdriver.common.keys import Keys


def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)

    return os.path.join(datadir, filename)


class YoutubeController:
    add_chrome_to_path = False

    def __init__(self, videoUrl):
        # result = re.fullmatch("http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?", videoUrl)
        result = re.fullmatch("^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$", videoUrl)
        if result is None:
            raise ValueError("Expect a youtube url.")

        # add chrome_driver_path to PATH
        # my_path = os.path.join('driver', 'chromedriver')
        my_path = find_data_file('chromedriver')
        chrome_driver_path = os.path.abspath(my_path)
        # if not YoutubeController.add_chrome_to_path:
        if chrome_driver_path not in sys.path:
            print("add to path")
            sys.path.append(chrome_driver_path)
        # YoutubeController.add_chrome_to_path = True

        self.driver = webdriver.Chrome(chrome_driver_path)
        self.driver.get(videoUrl)
        self.elem = self.driver.find_element_by_id("movie_player")
        self.elem.send_keys(Keys.SPACE)

    def reset_elem(self):
        try:
            self.elem = self.driver.find_element_by_id("movie_player")
        except Exception:
            print('Cannot find player')

    def play(self):
        # check if the video has already played
        isPlaying = False
        try:
            items = self.driver.find_elements_by_class_name("playing-mode")
            for item in items:
                if item.id == self.elem.id:
                    isPlaying = True
                    break
        except Exception:
            print('No element found')

        if not isPlaying:
            try:
                self.elem.send_keys('k')
            except Exception:
                self.reset_elem()
                # self.elem.send_keys('k')
            # print('Start playing')

    def pause(self):
        # check if the video has already stopped
        isPaused = False
        try:
            items = self.driver.find_elements_by_class_name("paused-mode")
            for item in items:
                if item.id == self.elem.id:
                    isPaused = True
                    break
        except Exception:
            print('No element found')

        if not isPaused:
            try:
                self.elem.send_keys('k')
            except Exception:
                self.reset_elem()
                # self.elem.send_keys('k')
            # print('Start paused')

    def forward5s(self):
        try:
            self.elem.send_keys(Keys.ARROW_RIGHT)
        except Exception:
            self.reset_elem()
            # self.elem.send_keys(Keys.ARROW_RIGHT)

    def forward10s(self):
        try:
            self.elem.send_keys('l')
        except Exception:
            self.reset_elem()
            # self.elem.send_keys('l')

    def backward5s(self):
        try:
            self.elem.send_keys(Keys.ARROW_LEFT)
        except Exception:
            self.reset_elem()
            # self.elem.send_keys(Keys.ARROW_LEFT)

    def backward10s(self):
        try:
            self.elem.send_keys('j')
        except Exception:
            self.reset_elem()
            # self.elem.send_keys('j')

    def increaseVol(self, value=0.5):
        iterations = 2

        if value > 1:
            iterations = 4
        elif value > 1.2:
            iterations = 7
        elif value > 1.5:
            iterations = 10
        elif value > 2:
            iterations = 15
        for _ in range(iterations):
            try:
                self.elem.send_keys(Keys.ARROW_UP)
            except Exception:
                self.reset_elem()
                # self.elem.send_keys(Keys.ARROW_UP)

    def decreaseVol(self, value=0.5):
        iterations = 2

        if value > 1:
            iterations = 4
        elif value > 1.2:
            iterations = 7
        elif value > 1.5:
            iterations = 10
        elif value > 2:
            iterations = 15
        for _ in range(iterations):
            try:
                self.elem.send_keys(Keys.ARROW_DOWN)
            except Exception:
                self.reset_elem()
                # self.elem.send_keys(Keys.ARROW_DOWN)

    def fullscreen(self):
        try:
            self.elem.send_keys('f')
        except Exception:
            self.reset_elem()
            # self.elem.send_keys('f')

    def skip_ad(self):
        try:
            btn = self.driver.find_element_by_class_name("ytp-ad-skip-button")
            print(btn)
            btn.click()
            self.elem = self.driver.find_element_by_id("movie_player")
        except Exception:
            print("Did not find skip ad button")

    def close(self):
        if "driver" in dir(self) and self.driver is not None:
            try:
                self.driver.close()
                self.driver = None
            except Exception:
                print('Driver is already closed.')

    def __del__(self):
        if "driver" in dir(self) and self.driver is not None:
            try:
                self.driver.close()
                self.driver = None
            except Exception:
                print('Driver is already closed.')
