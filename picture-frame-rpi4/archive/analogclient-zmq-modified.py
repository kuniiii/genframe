import time
from collections import deque
import zmq
import json
import automationhat
import signal
import sys

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    socket.close()
    context.term()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

time.sleep(0.1)  # short pause after ads1015 class creation recommended

context = zmq.Context()
socket = context.socket(zmq.PUB)
print("Connecting to server...")

# Attempt to connect to the server
try:
    socket.connect("tcp://localhost:55555")
except Exception as e:
    print("Failed to connect to server, exiting...", str(e))
    socket.close()
    context.term()
    sys.exit(1)

# Sampling rate and window size setup
sampling_rate_ads1015 = 330  # samples per second
sampling_interval_ms = (1 / sampling_rate_ads1015) * 1000  # converting to milliseconds
window_size = 100  # Number of samples for moving average

one_samples = deque(maxlen=window_size)
two_samples = deque(maxlen=window_size)
three_samples = deque(maxlen=window_size)

# Initialize other necessary variables
last_value = None
repetitions = 0
initial_change = False

while True:
    start_time = time.time()

    # Read analog values
    one_reading = automationhat.analog.one.read()
    two_reading = automationhat.analog.two.read()
    three_reading = automationhat.analog.three.read()
    button = automationhat.input.one.read()

    # Append to deques
    one_samples.append(one_reading)
    two_samples.append(two_reading)
    three_samples.append(three_reading)

    # Calculate moving averages if enough samples are available
    if len(one_samples) == window_size:
        one = round(sum(one_samples) / window_size, 2)
        two = round(sum(two_samples) / window_size, 2)
        three = round(sum(three_samples) / window_size, 2)

        selectorValueFloat1 = round(one / 0.454545)
        selectorValueFloat2 = round(two / 0.454545)
        selectorValueFloat3 = round(three / 0.454545)
        current_values = [selectorValueFloat1, selectorValueFloat2, selectorValueFloat3]
        print(current_values)

        if last_value is None:
            last_value = current_values

        elif last_value == current_values and initial_change:
            repetitions += 1
        elif last_value != current_values:
            last_value = current_values
            repetitions = 0
            initial_change = True
            print("change detected")

        if repetitions == 15:
            package = [one, selectorValueFloat1, selectorValueFloat2, selectorValueFloat3, button, "hello"]
            try:
                message = json.dumps(package)
                message = message.encode()
                print("sending message, waiting 15 seconds!")
                socket.send_multipart([b"client1", message])
            except Exception as e:
                print("Failed to send ZMQ message, retrying in 1 second")
                time.sleep(1)
                continue

            repetitions = 0
            last_value = None
            initial_change = False
            time.sleep(15)

    elapsed_time = time.time() - start_time
    sleep_time = max(0, (sampling_interval_ms / 1000) - elapsed_time)
    time.sleep(sleep_time)

socket.close()
context.term()
