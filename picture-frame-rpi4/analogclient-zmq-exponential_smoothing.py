import time
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
    socket.connect("tcp://localhost:5555")
except Exception as e:
    print("Failed to connect to server, exiting...", str(e))
    socket.close()
    context.term()
    sys.exit(1)

# Sampling rate and window size setup
sampling_rate_ads1015 = 3300  # samples per second
sampling_interval_ms = (1 / sampling_rate_ads1015) * 1000  # converting to milliseconds
alpha = 0.4  # Smoothing factor for exponential smoothing

# Initialize necessary variables for EMA
one_ema = None
two_ema = None
three_ema = None

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

    # Calculate exponential moving averages
    if one_ema is None:
        one_ema = one_reading
    else:
        one_ema = alpha * one_reading + (1 - alpha) * one_ema

    if two_ema is None:
        two_ema = two_reading
    else:
        two_ema = alpha * two_reading + (1 - alpha) * two_ema

    if three_ema is None:
        three_ema = three_reading
    else:
        three_ema = alpha * three_reading + (1 - alpha) * three_ema

    one = round(one_ema, 1)
    two = round(two_ema, 1)
    three = round(three_ema, 1)
    # values_test = [one, two, three]
    # print(values_test)
    
    # Calculate and print selector values for debugging
    selectorValueFloat1 = round(one / (0.454545))
    selectorValueFloat2 = round(two / (0.454545))
    selectorValueFloat3 = round(three / (0.454545))
    current_values = [selectorValueFloat1, selectorValueFloat2, selectorValueFloat3]
    # print(selectorValueFloat1)
    print(current_values)

    # If it's the first iteration, we set the last_value to the current_values.
    if last_value is None:
        last_value = current_values

    # Check for repetitions or changes
    elif last_value == current_values and initial_change:
        repetitions += 1
    elif last_value != current_values:
        last_value = current_values
        repetitions = 0
        initial_change = True
        # print("change detected")

    # Send message if there are 15 repetitions
    if repetitions == 30:
        package = [one, selectorValueFloat1, selectorValueFloat2, selectorValueFloat3, button, "hello"]
        try:
            message = json.dumps(package)
            message = message.encode()
            print("sending message, waiting 25 seconds!")
            socket.send_multipart([b"client1", message])
        except Exception as e:
            print("Failed to send ZMQ message, retrying in 1 second")
            time.sleep(1)
            continue

        repetitions = 0
        last_value = None
        initial_change = False
        time.sleep(25)

    # Sleep to maintain the desired sampling rate
    elapsed_time = time.time() - start_time
    # print("elapsed time: ", elapsed_time)
    sleep_time = max(0, (sampling_interval_ms / 1000) - elapsed_time)
    # print("sleep time: ", sleep_time)
    time.sleep(sleep_time)

socket.close()
context.term()
