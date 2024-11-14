# GenFrame

This is the code to run the [GenFrame](https://airlab.itu.dk/genframe/). There are three scripts that run in parallel:

> [!WARNING]
> Files have been moved around in this repository, and it needs to be checked that the repository is updated on the GenFrame's Raspberry Pi. It is not necessary, but the paths of the files below might be incorrect.

To start up the GenFrame here are the three scripts to run **in parallel**, in three separate terminal tabs:
```
python /analogclient-zmq-exponential_smoothing.py
python /picture-frame-rpi4/zmq-server_dis2024.py
python /picture-frame-rpi4/tkinter-fullscreen-zmq.py --fullscreen
```

### 1. analogclient-zmq-exponential_smoothing.py
This script is in the path `/picture-frame-rpi4/analogclient-zmq-exponential_smoothing.py` (if the GenFrame's Raspberry Pi has the latest version from the Git, otherwise one folder up, so `/analogclient-zmq-exponential_smoothing.py`). The role of this script is to read the values from the interface (the knobs), and send the messages to the backend script.

### 2. zmq-server_dis2024.py
This script is in the path `/picture-frame-rpi4/zmq-server_dis2024.py`. It's the backend, that receives the messages from the analogclient interface script, and submits API requests to the server. The server currently is on the `http://res52.itu.dk:8022` route, this can be changed in the script. 

### tkinter-fullscreen-zmq.py
This script is in the path `/picture-frame-rpi4/tkinter-fullscreen-zmq.py`. This script receives the images from the API and shows them in a window or fullscreen (by running the script with the `--fullscreen` argument).

---

# Potential issues

### Wifi problems
The most common – the Raspberry Pi needs to have an active wifi connection to be able to access (https://res52.itu.dk)[https://res52.itu.dk]. 

### Analog electronics
The analogclient scripts' output tells if there are issues with wiring - has happened a few times. 
