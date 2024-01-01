# Ambeelight
Ambeelight is a cross-platform (Windows, Linux, macOS) ambient light solution for Yeelight. It will update Yeelight devices to display average color of your primary display, creating a nice atmosphere when watching videos or gaming.

## Create Installation
Manually put 'res' folder in the output folder with the `.exe`
```commandline
pyinstaller main.py -n ambeelight -w -D --hidden-import='PIL._tkinter_finder' -i "res/icon.ico"
```

## Troubleshooting
### Failed to Connect (VPN?)
This error message occurs when Ambeelight cannot connect to a bulb on the specified IP address. 
- Check whether you entered the correct IP address 
- Ambeelight could have issues when you have a VPN running, either turn it off or try split tunneling