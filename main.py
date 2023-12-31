from customtkinter import *
from yeelight import Bulb
from functools import partial
from mss import mss
import numpy as np
import time

is_running = False
primary_color = "#DF282F"
interval = 200


def toggle():
    global is_running
    global bulb
    global interval

    ip = input_ip.get()
    brightness = slider_brightness.get()
    interval = slider_interval.get()
    transition_duration = slider_transition.get()

    if not is_running:
        is_running = True
        bulb = Bulb(ip, duration=transition_duration)
        bulb.turn_on()
        bulb.set_brightness(brightness)
        bulb.start_music()

        btn_power.configure(fg_color="green")
        run(bulb)
    else:
        btn_power.configure(fg_color=primary_color)
        is_running = False


def run(bulb):
    with mss() as sct:  # Prevents crash
        if is_running:
            display = sct.monitors[1]

            screen = sct.grab(display)
            screen2d = np.asarray(screen).reshape(-1, 4)
            avg_pixel = list(map(int, np.average(screen2d, axis=-2)))  # BGRA

            bulb.set_rgb(avg_pixel[2], avg_pixel[1], avg_pixel[0])
            time.sleep(interval / 1000 - (time.monotonic()) % interval / 1000)

            app.after(interval, partial(run, bulb))


# TODO: https://customtkinter.tomschimansky.com/tutorial/frames#using-classes
app = CTk()
app.title("Ambeelight")
app.geometry("280x400")
app.configure(fg_color="#101010")
set_appearance_mode("dark")
app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(0, weight=1)

frame = CTkFrame(app, fg_color="transparent")
frame.grid(row=0, column=0, padx=14, pady=14, sticky="nwe")
frame.columnconfigure(0, weight=1)
frame.grid_rowconfigure(3, weight=1)

lbl_ip = CTkLabel(master=frame, text="Yeelight IP")
lbl_ip.grid(row=0, column=0, sticky="w")

input_ip = CTkEntry(frame, border_color="#353535")
input_ip.grid(row=1, column=0, sticky="ew", columnspan=2)

brightness = StringVar()
interval = StringVar()
transition = StringVar()

brightness.set("40")
interval.set("200 ms")
transition.set("200 ms")


def handle_brightness(val):
    brightness.set(str(int(val)))


def handle_interval(val):
    interval.set(str(int(val)) + " ms")


def handle_transition(val):
    transition.set(str(int(val)) + " ms")


lbl_brightness = CTkLabel(frame, text="Brightness", text_color="white", fg_color="transparent")
lbl_brightness.grid(row=2, column=0, sticky="w")

slider_brightness = CTkSlider(frame, progress_color=primary_color, command=handle_brightness,
                              button_color=primary_color, hover=False, from_=1, to=100)
slider_brightness.set(40)
slider_brightness.grid(row=3, column=0, sticky="ew", columnspan=2)

value_brightness = CTkLabel(frame, textvariable=brightness, width=36, text_color="#808080")
value_brightness.grid(row=2, column=1, sticky="e")

lbl_interval = CTkLabel(frame, text="Interval", text_color="white", fg_color="transparent")
lbl_interval.grid(row=4, column=0, sticky="w")

slider_interval = CTkSlider(frame, progress_color=primary_color, command=handle_interval, button_color=primary_color, hover=False, from_=100,
                            to=1000)
slider_interval.set(200)
slider_interval.grid(row=5, column=0, sticky="ew", columnspan=2)

value_interval = CTkLabel(frame, textvariable=interval, width=50, text_color="#808080")
value_interval.grid(row=4, column=1, sticky="e")

lbl_transition = CTkLabel(frame, text="Transition Duration", text_color="white", fg_color="transparent")
lbl_transition.grid(row=6, column=0, sticky="w")

slider_transition = CTkSlider(frame, progress_color=primary_color, command=handle_transition, button_color=primary_color, hover=False, from_=100,
                              to=1000)
slider_transition.set(200)
slider_transition.grid(row=7, column=0, sticky="ew", columnspan=2)

value_transition = CTkLabel(frame, textvariable=transition, width=50, text_color="#808080")
value_transition.grid(row=6, column=1, sticky="e")

btn_power = CTkButton(app, text="Power", hover=False, corner_radius=0, fg_color=primary_color, height=35,
                      command=toggle, cursor="hand2")
btn_power.grid(row=1, column=0, padx=0, pady=0, sticky="ews")

app.mainloop()
