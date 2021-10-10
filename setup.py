import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
build_exe_options = {"packages": ["os", "tkinter", "tinydb", "sklearn", "mediapipe", "cv2", "selenium"],
                     "include_files": ['database', 'media', 'models', 'driver', 'som', 'app_icon.icns']}

                     # "excludes": ["distutils"]}
# build_mac_options = {"include_resources": [('database', './database'), ('media', './media'), ('models', './models'), ('driver', './driver')],
build_mac_options = {"iconfile": "app_icon.icns",
                     "bundle_name": "YouHand",
                     "plist_items": [("NSCameraUsageDescription", "GesReg needs to access your camera"),
                                     ("CFBundleDisplayName", "YouHand"),
                                     ("NSHumanReadableCopyright", "Copyright © 2021, CS Zone, Nguyen Minh Anh. All Rights Reserved.")]}

base = None
setup(
    name = "YouHand",
    version = "1.0",
    description = "Hand Gesture Recognizer",
    options = {"bdist_mac": build_mac_options,
               "build_exe": build_exe_options},
    executables = [Executable("YouHand.py", base=base)]
)
