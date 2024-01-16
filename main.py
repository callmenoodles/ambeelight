import os.path
import time

import yeelight.main
import tkinter
from customtkinter import *
from yeelight import Bulb
from functools import partial
from PIL import Image
from mss import mss
from platform import system
import numpy as np
import pickle
import threading
from utils import to_file_name

primary_color = "#DF282F"
dark_grey = "#252525"
disabled_color = "#505050"
background_color = "#101010"
text_color = "#ddd"

data_path = ""

if system() == "Windows":
    data_path = os.path.join(os.getenv("APPDATA"), "Ambeelight")
elif system() == "Linux":
    data_path = os.path.expanduser(".ambeelight")
elif system() == "Darwin":
    data_path = os.path.expanduser(os.path.join("Library", "Application Support", "ambeelight"))

if not os.path.exists(data_path):
    os.makedirs(data_path)

is_running = False


def toggle_power():
    global is_running

    ip = app.input_frame.ip.get_value()
    brightness = app.input_frame.brightness.get_value()
    interval = app.input_frame.interval.get_value()
    transition_duration = app.input_frame.transition.get_value()

    if not is_running:
        try:
            bulb = Bulb(ip, duration=int(transition_duration), effect="smooth")
            is_running = True

            # FIXME: Names are hardcoded
            pickle.dump({
                "yeelight_ip": ip,
                "brightness": int(brightness),
                "interval": int(interval),
                "transition_duration": int(transition_duration)
            }, open(os.path.join(data_path, "prefs"), "wb"))

            bulb.turn_on()
            bulb.set_brightness(int(brightness))
            bulb.start_music()

            app.input_frame.ip.err.set("")
            app.input_frame.transition.set_disabled(True)
            app.btn_power.configure(fg_color="green")

            run(bulb)
        except yeelight.main.BulbException:
            app.input_frame.ip.err.set("Failed to Connect (VPN?)")
            app.input_frame.ip.input.focus()
    else:
        app.btn_power.configure(fg_color=primary_color)
        app.input_frame.transition.set_disabled(False)
        is_running = False


def run_thread(bulb):
    threading.Thread(target=partial(run, bulb)).start()


def run(bulb):
    with mss() as sct:  # Prevents crash
        if is_running:
            app.after(int(app.input_frame.interval.get_value()), partial(run_thread, bulb))

            if bulb.get_properties()["current_brightness"] != str(int(app.input_frame.brightness.get_value())):
                bulb.set_brightness(int(app.input_frame.brightness.get_value()))

            display = sct.monitors[1]
            screen = sct.grab(display)
            screen2d = np.asarray(screen)[:, :, :3].reshape(-1, 3)  # screen.pixels is slower

            b = int(screen2d[:, :1].mean())
            g = int(screen2d[:, 1:2].mean())
            r = int(screen2d[:, 2:3].mean())

            bulb.set_rgb(r, g, b)


class TextFrame(CTkFrame):
    def __init__(self, master, title):
        super().__init__(master)
        self.configure(fg_color="transparent")

        lbl_title = CTkLabel(self, text=title, text_color=text_color)
        lbl_title.grid(row=0, column=0, sticky="w")

        self.err = StringVar()
        lbl_err = CTkLabel(self, text_color=primary_color, textvariable=self.err)
        lbl_err.grid(row=0, column=1, sticky="e")

        def handle_err(x, y, mode):
            self.err.set("")

        self.value = StringVar()
        self.value.trace_add("write", handle_err)

        try:
            data = pickle.load(open(os.path.join(data_path, "prefs"), "rb"))
            self.value.set(data[to_file_name(title)])
        except (KeyError, TypeError, FileNotFoundError):
            self.value.set("")

        self.input = CTkEntry(
            self, textvariable=self.value, border_color=dark_grey, fg_color=dark_grey, text_color="#ccc")
        self.input.bind(command=handle_err)
        self.input.grid(row=1, column=0, sticky="ew", columnspan=2, pady=(0, 8))

    def get_value(self):
        return self.value.get()


class SliderFrame(CTkFrame):
    def __init__(self, master, title, minimum, maximum, default, steps, unit):
        super().__init__(master)

        self.configure(fg_color="transparent")
        self.value = StringVar()
        self.value.set(str(default) + " " + unit)

        try:
            data = pickle.load(open(os.path.join(data_path, "prefs"), "rb"))
            self.value.set(str(data[to_file_name(title)]) + " " + unit)
        except (KeyError, TypeError, FileNotFoundError):
            self.value.set(str(default) + " " + unit)

        def handle(val):
            self.value.set(str(int(val)) + " " + unit)

        lbl_title = CTkLabel(self, text=title, text_color=text_color, fg_color="transparent")
        lbl_title.grid(row=2, column=0, sticky="w")

        lbl_value = CTkLabel(self, textvariable=self.value, text="hello", width=26, text_color="#808080")
        lbl_value.grid(row=2, column=1, sticky="e")

        self.slider = CTkSlider(
            self, command=handle, progress_color=primary_color, fg_color=dark_grey, button_color=primary_color,
            hover=False, from_=minimum, to=maximum, number_of_steps=steps)
        self.slider.set(int(self.value.get().split()[0]))
        self.slider.grid(row=3, column=0, sticky="ew", columnspan=2, pady=(0, 8))

    def get_value(self):
        return int(self.value.get().split()[0])

    def set_disabled(self, disabled):
        if disabled:
            self.slider.configure(
                state="disabled",
                progress_color=disabled_color,
                button_color=disabled_color
            )
        else:
            self.slider.configure(
                state="normal",
                progress_color=primary_color,
                button_color=primary_color
            )


class InputFrame(CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.configure(fg_color="transparent")
        self.grid(row=0, column=0, padx=14, pady=14, sticky="nwe")
        self.columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.ip = TextFrame(self, "Yeelight IP")
        self.ip.columnconfigure(0, weight=1)
        self.ip.grid(row=0, column=0, sticky="ew")

        self.brightness = SliderFrame(
            self, "Brightness", 1, 100, 40, 20, "")
        self.brightness.columnconfigure(0, weight=1)
        self.brightness.grid(row=1, column=0, sticky="ew")

        self.interval = SliderFrame(
            self, "Interval", 50, 500, 100, 45, "ms")
        self.interval.columnconfigure(0, weight=1)
        self.interval.grid(row=2, column=0, sticky="ew")

        self.transition = SliderFrame(
            self, "Transition Duration", 0, 1000, 250, 100, "ms")
        self.transition.columnconfigure(0, weight=1)
        self.transition.grid(row=3, column=0, sticky="ew")


class App(CTk):
    def __init__(self):
        super().__init__()

        self.title("Ambeelight")
        self.geometry("280x400")
        self.resizable(False, False)
        self.configure(fg_color=background_color)
        set_appearance_mode("dark")

        icon = tkinter.PhotoImage(file=os.path.join("res", "icon.png"))
        self.wm_iconbitmap()
        self.wm_iconphoto(False, icon)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.input_frame = InputFrame(self)

        icon_power = CTkImage(Image.open("res/power.png"), size=(22, 22))
        self.btn_power = CTkButton(self, command=toggle_power, text="", hover=False, corner_radius=0,
                                   fg_color=primary_color, height=35, cursor="hand2", image=icon_power)
        self.btn_power.grid(row=1, column=0, padx=0, pady=0, sticky="ews")


app = App()
app.mainloop()
