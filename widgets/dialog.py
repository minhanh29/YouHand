import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox
import os
from driver.youtube_controller import YoutubeController


class MyDeleteDialog(tk.simpledialog.Dialog):
    def __init__(self, parent, title, controller):
        self.controller = controller
        super().__init__(parent, title)

    def body(self, frame):
        self.label = tk.Label(frame,
                              text="Choose gestures to delete")
        self.label.pack(pady=5)

        self.checkbox_frame = tk.Frame(frame)
        self.names = self.controller.get_gesture_names()
        self.var_list = []
        for name in self.names:
            var = tk.IntVar(value=0)
            self.var_list.append(var)
            checkbox = tk.Checkbutton(self.checkbox_frame,
                                      text=name,
                                      variable=var,
                                      onvalue=1, offvalue=0)
            checkbox.pack(pady=5)
        self.checkbox_frame.pack(pady=5)

        return frame

    def ok_pressed(self):
        count = 0
        for var, name in zip(self.var_list, self.names):
            value = var.get()
            if value == 1:
                self.controller.delete_gesture(name)
                count += 1
        tk.messagebox.showinfo('Gesture Delete',
                               f"Deleted {count} gestures.")
        self.destroy()

    def cancel_pressed(self):
        self.destroy()

    def buttonbox(self):
        self.btn_frame = tk.Frame(self)
        self.ok_button = tk.Button(self.btn_frame, width=15, text='OK',
                                   command=self.ok_pressed)
        self.cancel_button = tk.Button(self.btn_frame, width=15, text='Cancel',
                                       command=self.cancel_pressed)
        self.ok_button.pack(side="left")
        self.cancel_button.pack(side="right")
        self.btn_frame.pack(pady=10, padx=10)
        self.bind("<Return>", lambda event: self.ok_pressed())
        self.bind("<Escape>", lambda event: self.cancel_pressed())


class MyGestureListDialog(tk.simpledialog.Dialog):
    def __init__(self, parent, title, gestures):
        self.gestures = gestures
        super().__init__(parent, title)

    def body(self, frame):
        count = len(self.gestures)
        self.label = tk.Label(frame,
                              text=f"You have trained {count} gestures:")
        self.label.pack(pady=10)

        for gesture in self.gestures:
            item = tk.Label(frame, text=gesture)
            item.pack(pady=5)

        return frame

    def cancel_pressed(self):
        self.destroy()

    def buttonbox(self):
        self.cancel_button = tk.Button(self, width=20, text='Exit',
                                       command=self.cancel_pressed)
        self.cancel_button.pack(pady=10, padx=10)
        self.bind("<Escape>", lambda event: self.cancel_pressed())


class UrlInputDialog(tk.simpledialog.Dialog):
    def __init__(self, parent, title, app_parent):
        self.app_parent = app_parent
        super().__init__(parent, title)

    def body(self, frame):
        self.label = tk.Label(frame, text='Enter your YouTube Video URL:')
        self.inforLabel = tk.Label(frame, text='')
        self.entry = tk.Entry(frame, width=50)
        self.label.pack()
        self.inforLabel.pack()
        self.entry.pack()

    def buttonbox(self):
        self.btn_frame = tk.Frame(self)
        self.submit_btn = tk.Button(self.btn_frame, width=10, text='Connect',
                                    command=self.submit, fg='blue')
        self.cancel_button = tk.Button(self.btn_frame, width=10, text='Exit',
                                       command=self.cancel_pressed, fg='red')
        self.submit_btn.pack(side='left', padx=10)
        self.cancel_button.pack(side='left', padx=10)
        self.btn_frame.pack(pady=10)
        self.bind("<Escape>", lambda event: self.cancel_pressed())
        self.bind("<Return>", lambda event: self.submit())

    def cancel_pressed(self):
        self.destroy()

    def submit(self):
        try:
            youtubeController = YoutubeController(self.entry.get().strip())
            self.app_parent.youtubeController = youtubeController
            self.app_parent.change_youtube_btn()
            self.destroy()
        except ValueError:
            self.inforLabel.configure(text="Invalid Youtube URL", fg='red')


class MyGestureMenuDialog(tk.simpledialog.Dialog):
    def __init__(self, parent, title, controller, handler, command_db):
        self.controller = controller
        self.handler = handler
        self.command_db = command_db
        super().__init__(parent, title)

    def body(self, frame):
        gestures = self.controller.get_gesture_names()
        count = len(gestures)

        # list box
        self.listFrame = tk.Frame(frame)
        self.label = tk.Label(self.listFrame,
                              text=f"You have created {count} gesture(s):")

        self.listbox = tk.Listbox(self.listFrame, width=20, height=16,
                                  selectmode=tk.MULTIPLE)

        for i, name in enumerate(gestures):
            self.listbox.insert(i, f" {i+1}.  {name}")

        self.label.pack(pady=5)
        self.listbox.pack(pady=10)
        self.listFrame.pack(side='left', padx=10)

        # gesture mapping
        data = self.command_db.all()
        self.var_list = []
        self.command_list = []
        self.map_gesture = []
        self.outer_right_frame = tk.Frame(frame)
        self.mapLabel = tk.Label(self.outer_right_frame,
                                 text="Command - Gesture mapping")
        self.right_frame = tk.Frame(self.outer_right_frame,
                                    highlightbackground='black',
                                    highlightthickness=1)
        self.map_frame = tk.Frame(self.right_frame)
        self.dropdown = []
        self.not_chosen_opt = 'not chosen'
        gestures.append(self.not_chosen_opt)
        for i, row in enumerate(data):
            command = row['command']
            gesture = row['gesture']
            self.command_list.append(command)
            self.map_gesture.append(gesture)

            # command
            commandLabel = tk.Label(self.map_frame, text=f"{command}: ", width=10)
            # commandLabel.pack(side='left', padx=10)
            commandLabel.grid(row=i, column=0, ipadx=5, ipady=2)

            # gesture list
            choice = tk.StringVar(self.map_frame, gesture)
            self.var_list.append(choice)
            if len(gestures) == 0:
                dropdown_list = tk.OptionMenu(self.map_frame, choice,

                                              self.not_chosen_opt)
            else:
                dropdown_list = tk.OptionMenu(self.map_frame, choice,
                                              *gestures)
            # dropdown_list.pack(side='left', padx=5)
            dropdown_list.grid(row=i, column=1, ipadx=10, ipady=2)
            self.dropdown.append(dropdown_list)

        self.apply_btn = tk.Button(self.right_frame, text='Apply',
                                   command=self.apply_mapping)

        self.mapLabel.pack(pady=5)
        self.map_frame.pack(pady=5, side='top')
        self.apply_btn.pack(side='right', pady=5)
        self.right_frame.pack(pady=10)
        self.outer_right_frame.pack(side='left', padx=10)

        return frame

    def apply_mapping(self):
        # check duplicate mapping
        visited = set()
        for i, item in enumerate(self.var_list):
            gesture = item.get()
            if gesture in visited and gesture != self.not_chosen_opt:
                tk.messagebox.showerror('Mapping Error',
                                        "Cannot assign the same gesture to 2 commands.")
                # reset to old option
                item.set(self.map_gesture[i])
                return
            visited.add(gesture)

        # update the mapping
        self.map_gesture = []
        for command, item in zip(self.command_list, self.var_list):
            # get the gesture
            gesture = item.get()
            # update the database
            self.command_db.update(command, gesture)
            self.map_gesture.append(gesture)

    def update_dropdown(self):
        gestures = self.controller.get_gesture_names()
        self.map_gesture = []
        data = self.command_db.all()
        for i, row in enumerate(data):
            command = row['command']
            gesture = row['gesture']
            # gesture just got deleted
            if gesture not in gestures:
                gesture = self.not_chosen_opt
                self.command_db.update(command, gesture)
            self.map_gesture.append(gesture)

            # gesture list
            # choice = self.var_list[i]
            # choice.set(gesture)

        data = self.command_db.all()
        self.var_list = []
        self.command_list = []
        self.map_gesture = []
        self.right_frame.destroy()
        self.right_frame = tk.Frame(self.outer_right_frame,
                                    highlightbackground='black',
                                    highlightthickness=1)
        self.map_frame = tk.Frame(self.right_frame)
        self.dropdown = []
        for i, row in enumerate(data):
            command = row['command']
            gesture = row['gesture']
            self.command_list.append(command)
            self.map_gesture.append(gesture)

            # command
            commandLabel = tk.Label(self.map_frame, text=f"{command}: ", width=10)
            # commandLabel.pack(side='left', padx=10)
            commandLabel.grid(row=i, column=0, ipadx=5, ipady=2)

            # gesture list
            choice = tk.StringVar(self.map_frame, gesture)
            self.var_list.append(choice)
            if len(gestures) == 0:
                dropdown_list = tk.OptionMenu(self.map_frame, choice,
                                              self.not_chosen_opt)
            else:
                dropdown_list = tk.OptionMenu(self.map_frame, choice,
                                              *gestures)
            # dropdown_list.pack(side='left', padx=5)
            dropdown_list.grid(row=i, column=1, ipadx=10, ipady=2)
            self.dropdown.append(dropdown_list)

        self.apply_btn = tk.Button(self.right_frame, text='Apply',
                                   command=self.apply_mapping)

        self.mapLabel.pack(pady=5)
        self.map_frame.pack(pady=5, side='top')
        self.apply_btn.pack(side='right', pady=5)
        self.right_frame.pack(pady=10)

    def load_pressed(self):
        my_filetypes = [('JSON', '.json')]
        path = filedialog.askopenfilename(parent=self.main_window,
                                          initialdir=os.getcwd(),
                                          title='Please select your gesture file',
                                          filetypes=my_filetypes)
        if os.path.isfile(path):
            self.controller.change_db(path)
            count = self.controller.get_gesture_num()
            tk.messagebox.showinfo('Gesture Loaded',
                                   f"Found {count} gestures.")
        self.update_listbox()
        self.update_dropdown()

    def add_pressed(self):
        sucess = self.handler.add_gesture()
        if sucess:
            self.destroy()

    def update_pressed(self):
        # get the selected lines
        selected_lines = self.listbox.curselection()

        # check number of selected items
        if len(selected_lines) == 0:
            tk.messagebox.showerror('Rename Failed',
                                    "Please choose a gesture to rename.")
            return

        if len(selected_lines) > 1:
            tk.messagebox.showerror('Rename Failed',
                                    "Only 1 gesture can be renamed at a time.")
            return

        gestures = self.controller.get_gesture_names()
        gesture = gestures[selected_lines[0]]
        sucess = self.handler.update_gesture(gesture)
        if sucess:
            self.destroy()

    def rename_pressed(self):
        # get the selected lines
        selected_lines = self.listbox.curselection()

        # check number of selected items
        if len(selected_lines) == 0:
            tk.messagebox.showerror('Rename Failed',
                                    "Please choose a gesture to rename.")
            return

        if len(selected_lines) > 1:
            tk.messagebox.showerror('Rename Failed',
                                    "Only 1 gesture can be renamed at a time.")
            return

        # get new_gesture name
        new_name = tk.simpledialog.askstring("Rename Gesture",
                                             "Enter new gesture name:",
                                             parent=self)
        if new_name is None:
            return

        # get the name of the gesture
        gestures = self.controller.get_gesture_names()
        old_name = gestures[selected_lines[0]]
        success = self.controller.rename_gesture(old_name, new_name)

        if not success:
            tk.messagebox.showerror('Rename Failed',
                                    "An error occur when processing your request.")
            return

        # update the list box
        self.update_listbox()
        self.update_dropdown()

    def delete_pressed(self):
        # get the selected lines
        selected_lines = self.listbox.curselection()

        # check number of selected items
        if len(selected_lines) == 0:
            tk.messagebox.showerror('Delete Failed',
                                    "Please choose a gesture to delete.")
            return

        # get the name of the gesture
        gestures = self.controller.get_gesture_names()
        for index in selected_lines:
            name = gestures[index]
            success = self.controller.delete_gesture(name)

            if not success:
                tk.messagebox.showerror('Delete Failed',
                                        "An error occur when processing your request.")
                return

        # update the list box
        self.update_listbox()
        self.update_dropdown()
        tk.messagebox.showinfo('Gesture Delete',
                               f"Deleted {len(selected_lines)} gesture(s).")

    def cancel_pressed(self):
        self.destroy()

    def update_listbox(self):
        # clear the box
        self.listbox.delete(0, tk.END)

        # sync with the database
        gestures = self.controller.get_gesture_names()
        count = len(gestures)
        self.label.configure(text=f"You have created {count} gestures:")
        for i, name in enumerate(gestures):
            self.listbox.insert(i, f" {i+1}.  {name}")

    def buttonbox(self):
        self.btn_frame = tk.Frame(self)
        self.add_btn = tk.Button(self.btn_frame, width=10, text='New Gesture',
                                 command=self.add_pressed)
        # self.update_btn = tk.Button(self.btn_frame, width=10, text='Update',
        #                             command=self.update_pressed)
        self.rename_btn = tk.Button(self.btn_frame, width=10, text='Rename',
                                    command=self.rename_pressed)
        self.delete_btn = tk.Button(self.btn_frame, width=10, text='Delete',
                                    command=self.delete_pressed)
        self.cancel_button = tk.Button(self.btn_frame, width=10, text='Cancel',
                                       command=self.cancel_pressed, fg='red')
        # self.update_btn.grid(row=0, column=1)
        self.add_btn.grid(row=0, column=0, padx=5)
        self.rename_btn.grid(row=0, column=1, padx=5)
        self.delete_btn.grid(row=1, column=0, padx=5)
        self.cancel_button.grid(row=1, column=1, padx=5)
        # self.btn_frame.grid(row=1, column=2)
        self.btn_frame.pack(pady=10, padx=20)

        # self.load_btn.pack(side='left', padx=5)
        # self.add_btn.pack(side='left', padx=5)
        # self.rename_btn.pack(side='left', padx=5)
        # self.delete_btn.pack(side='left', padx=5)
        # self.cancel_button.pack(side='left', padx=5)
        # self.btn_frame.pack(pady=10, padx=10)

        self.bind("<Escape>", lambda event: self.cancel_pressed())
