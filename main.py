import tkinter
import yeelight.main
from customtkinter import *
from yeelight import Bulb
from functools import partial
from PIL import Image
from mss import mss
import numpy as np
import pickle
import threading

is_running = False
primary_color = "#DF282F"
dark_grey = "#252525"
disabled_color = "#505050"
text_color = "#ddd"


def toggle():
    global is_running

    ip = input_ip.get()
    brightness = slider_brightness.get()
    interval = slider_interval.get()
    transition_duration = slider_transition.get()

    if not is_running:
        try:
            bulb = Bulb(ip, duration=int(transition_duration))

            ip_err.set("")
            slider_transition.configure(
                state="disabled",
                progress_color=disabled_color,
                button_color=disabled_color
            )

            is_running = True
            pickle.dump({
                "ip": ip,
                "brightness": int(brightness),
                "interval": int(interval),
                "transition": int(transition_duration)
            }, open("data", "wb"))

            bulb.turn_on()
            bulb.set_brightness(int(brightness))
            bulb.start_music()

            btn_power.configure(fg_color="green")
            threading.Thread(target=run(bulb)).start()
        except yeelight.main.BulbException:
            ip_err.set("Failed to Connect (VPN?)")
            input_ip.focus()
    else:
        btn_power.configure(fg_color=primary_color)
        slider_transition.configure(
            state="normal",
            progress_color=primary_color,
            button_color=primary_color
        )

        is_running = False


def run(bulb):
    with mss() as sct:  # Prevents crash
        if is_running:
            if bulb.get_properties()["current_brightness"] != str(int(slider_brightness.get())):
                bulb.set_brightness(int(slider_brightness.get()))

            display = sct.monitors[1]
            screen = sct.grab(display)
            screen2d = np.asarray(screen).reshape(-1, 4)
            avg_pixel = list(map(int, np.average(screen2d, axis=-2)))  # BGRA

            bulb.set_rgb(avg_pixel[2], avg_pixel[1], avg_pixel[0])

            app.after(int(slider_interval.get()), partial(run, bulb))


app = CTk()
app.title("Ambeelight")
app.geometry("280x400")
app.configure(fg_color="#101010")
icon = tkinter.PhotoImage(file="res/icon.png")
app.wm_iconphoto(False, icon)
set_appearance_mode("dark")
app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(0, weight=1)

frame = CTkFrame(app, fg_color="transparent")
frame.grid(row=0, column=0, padx=14, pady=14, sticky="nwe")
frame.columnconfigure(0, weight=1)
frame.grid_rowconfigure(3, weight=1)

lbl_ip = CTkLabel(master=frame, text="Yeelight IP", text_color=text_color)
lbl_ip.grid(row=0, column=0, sticky="w")

ip_err = StringVar()
lbl_ip_err = CTkLabel(master=frame, text_color=primary_color, textvariable=ip_err)
lbl_ip_err.grid(row=0, column=1, sticky="e")


# Takes 3 arguments, but I don't know what x and y represent
def handle_err(x, y, mode):
    ip_err.set("")


ip_strvar = StringVar()
ip_strvar.trace_add("write", handle_err)

try:
    data = pickle.load(open("data", "rb"))
    ip_strvar.set(data["ip"])
except KeyError or FileNotFoundError:
    ip_strvar.set("")

input_ip = CTkEntry(frame, textvariable=ip_strvar, border_color=dark_grey, fg_color=dark_grey, text_color="#ccc")
input_ip.bind(command=handle_err)
input_ip.grid(row=1, column=0, sticky="ew", columnspan=2, pady=(0, 8))

brightness = StringVar()
interval = StringVar()
transition = StringVar()

try:
    data = pickle.load(open("data", "rb"))
    brightness.set(data["brightness"])
except KeyError or FileNotFoundError:
    brightness.set("40")

try:
    data = pickle.load(open("data", "rb"))
    interval.set(data["interval"])
except KeyError or FileNotFoundError:
    interval.set("200 ms")

try:
    data = pickle.load(open("data", "rb"))
    transition.set(data["transition"])
except KeyError or FileNotFoundError:
    transition.set("200 ms")


def handle_brightness(val):
    brightness.set(str(int(val)))


def handle_interval(val):
    interval.set(str(int(val)) + " ms")


def handle_transition(val):
    transition.set(str(int(val)) + " ms")


lbl_brightness = CTkLabel(frame, text="Brightness", text_color=text_color, fg_color="transparent")
lbl_brightness.grid(row=2, column=0, sticky="w")

slider_brightness = CTkSlider(frame, progress_color=primary_color, command=handle_brightness,
                              button_color=primary_color, hover=False, from_=1, to=100, fg_color=dark_grey,
                              number_of_steps=20)
slider_brightness.set(int(brightness.get()))
slider_brightness.grid(row=3, column=0, sticky="ew", columnspan=2, pady=(0, 8))

value_brightness = CTkLabel(frame, textvariable=brightness, width=26, text_color="#808080")
value_brightness.grid(row=2, column=1, sticky="e")

lbl_interval = CTkLabel(frame, text="Interval", text_color=text_color, fg_color="transparent")
lbl_interval.grid(row=4, column=0, sticky="w")

slider_interval = CTkSlider(frame, progress_color=primary_color, command=handle_interval, button_color=primary_color,
                            hover=False, from_=100,
                            to=1000, fg_color=dark_grey, number_of_steps=90)
slider_interval.set(int(interval.get()))
slider_interval.grid(row=5, column=0, sticky="ew", columnspan=2, pady=(0, 8))

value_interval = CTkLabel(frame, textvariable=interval, width=50, text_color="#808080")
value_interval.grid(row=4, column=1, sticky="e")
interval.set(interval.get() + " ms")

lbl_transition = CTkLabel(frame, text="Transition Duration", text_color=text_color, fg_color="transparent")
lbl_transition.grid(row=6, column=0, sticky="w")

slider_transition = CTkSlider(frame, progress_color=primary_color, command=handle_transition,
                              button_color=primary_color, hover=False, from_=100,
                              to=1000, fg_color=dark_grey, number_of_steps=90)
slider_transition.set(int(transition.get()))
slider_transition.grid(row=7, column=0, sticky="ew", columnspan=2)

value_transition = CTkLabel(frame, textvariable=transition, width=50, text_color="#808080")
value_transition.grid(row=6, column=1, sticky="e")
transition.set(transition.get() + " ms")

icon_power = CTkImage(Image.open("res/power.png"), size=(22, 22))

btn_power = CTkButton(app, text="", hover=False, corner_radius=0, fg_color=primary_color, height=35,
                      command=toggle, cursor="hand2", image=icon_power)
btn_power.grid(row=1, column=0, padx=0, pady=0, sticky="ews")

app.mainloop()
