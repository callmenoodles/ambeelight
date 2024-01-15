import os.path
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

is_running = False
primary_color = "#DF282F"
dark_grey = "#252525"
disabled_color = "#505050"
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


def toggle_power():
    global is_running

    ip = app.input_frame.ip.get_value()
    brightness = app.input_frame.brightness.get_value()
    interval = app.input_frame.interval.get_value()
    transition_duration = app.input_frame.transition.get_value()

    if not is_running:
        try:
            bulb = Bulb(ip, duration=int(transition_duration))
            is_running = True

            pickle.dump({
                "ip": ip,
                "brightness": int(brightness),
                "interval": int(interval),
                "transition": int(transition_duration)
            }, open(os.path.join(data_path, "prefs"), "wb"))

            bulb.turn_on()
            bulb.set_brightness(int(brightness))
            bulb.start_music()

            app.input_frame.ip.ip_err.set("")

            app.input_frame.transition.slider.configure(
                state="disabled",
                progress_color=disabled_color,
                button_color=disabled_color
            )

            app.btn_power.configure(fg_color="green")
            threading.Thread(target=partial(run, bulb)).start()
        except yeelight.main.BulbException:
            app.input_frame.ip.ip_err.set("Failed to Connect (VPN?)")
            app.input_frame.ip.input_ip.focus()
    else:
        app.btn_power.configure(fg_color=primary_color)
        app.input_frame.transition.slider.configure(
            state="normal",
            progress_color=primary_color,
            button_color=primary_color
        )

        is_running = False


def run(bulb):
    with mss() as sct:  # Prevents crash
        if is_running:
            app.after(int(app.input_frame.interval.get_value()), partial(run, bulb))

            if bulb.get_properties()["current_brightness"] != str(int(app.input_frame.brightness.get_value())):
                bulb.set_brightness(int(app.input_frame.brightness.get_value()))

            display = sct.monitors[1]
            screen = sct.grab(display)
            screen2d = np.asarray(screen).reshape(-1, 4)
            avg_pixel = list(map(int, np.average(screen2d, axis=-2)))  # BGRA

            bulb.set_rgb(avg_pixel[2], avg_pixel[1], avg_pixel[0])


class TextFrame(CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.configure(fg_color="transparent")

        lbl_ip = CTkLabel(self, text="Yeelight IP", text_color=text_color)
        lbl_ip.grid(row=0, column=0, sticky="w")

        self.ip_err = StringVar()
        lbl_ip_err = CTkLabel(self, text_color=primary_color, textvariable=self.ip_err)
        lbl_ip_err.grid(row=0, column=1, sticky="e")

        def handle_err(x, y, mode):
            self.ip_err.set("")

        self.ip_strvar = StringVar()
        self.ip_strvar.trace_add("write", handle_err)

        try:
            data = pickle.load(open(os.path.join(data_path, "prefs"), "rb"))
            self.ip_strvar.set(data["ip"])
        except (TypeError, FileNotFoundError):
            self.ip_strvar.set("")

        self.input_ip = CTkEntry(self, textvariable=self.ip_strvar, border_color=dark_grey, fg_color=dark_grey,
                                 text_color="#ccc")
        self.input_ip.bind(command=handle_err)
        self.input_ip.grid(row=1, column=0, sticky="ew", columnspan=2, pady=(0, 8))

    def get_value(self):
        return self.ip_strvar.get()


class SliderFrame(CTkFrame):
    def __init__(self, master, title, minimum, maximum, default, steps, unit):
        super().__init__(master)
        self.configure(fg_color="transparent")

        self.sv = StringVar()
        self.sv.set(str(default) + " " + unit)

        try:
            data = pickle.load(open("data", "rb"))
            self.sv.set(str(data[title.strip().replace(" ", "_").lower()]) + " " + unit)
        except (KeyError, FileNotFoundError):
            self.sv.set(str(default) + " " + unit)

        def handle(val):
            self.sv.set(str(int(val)) + " " + unit)

        label = CTkLabel(self, text=title, text_color=text_color, fg_color="transparent")
        label.grid(row=2, column=0, sticky="w")

        self.slider = CTkSlider(self, progress_color=primary_color, command=handle,
                                button_color=primary_color, hover=False, from_=minimum, to=maximum, fg_color=dark_grey,
                                number_of_steps=steps)
        self.slider.set(int(self.sv.get().split()[0]))
        self.slider.grid(row=3, column=0, sticky="ew", columnspan=2, pady=(0, 8))

        value = CTkLabel(self, textvariable=self.sv, text="hello", width=26, text_color="#808080")
        value.grid(row=2, column=1, sticky="e")

    def get_value(self):
        return int(self.sv.get())


class InputFrame(CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.configure(fg_color="transparent")
        self.grid(row=0, column=0, padx=14, pady=14, sticky="nwe")
        self.columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.ip = TextFrame(self)
        self.ip.columnconfigure(0, weight=1)
        self.ip.grid(row=0, column=0, sticky="ew")

        self.brightness = SliderFrame(self, "Brightness", 1, 100, 40, 20, "")
        self.brightness.columnconfigure(0, weight=1)
        self.brightness.grid(row=1, column=0, sticky="ew")

        self.interval = SliderFrame(self, "Interval", 100, 1000, 200, 90, "ms")
        self.interval.columnconfigure(0, weight=1)
        self.interval.grid(row=2, column=0, sticky="ew")

        self.transition = SliderFrame(self, "Transition Duration", 100, 1000, 200, 90,"ms")
        self.transition.columnconfigure(0, weight=1)
        self.transition.grid(row=3, column=0, sticky="ew")


class App(CTk):
    def __init__(self):
        super().__init__()

        self.title("Ambeelight")
        self.geometry("280x400")
        self.resizable(False, False)
        self.configure(fg_color="#101010")
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