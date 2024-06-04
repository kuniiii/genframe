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
    socket.connect("tcp://localhost:5555")
except Exception as e:
    print("Failed to connect to server, exiting...", str(e))
    socket.close()
    context.term()
    sys.exit(1)

# Sampling rate and window size setup
sampling_rate_ads1015 = 3300  # samples per second
sampling_interval_ms = (1 / sampling_rate_ads1015) * 1000  # converting to milliseconds
window_size = 30  # Number of samples for moving average

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

    # Print raw values for debugging
    # print(f"Raw Values - One: {one_reading}, Two: {two_reading}, Three: {three_reading}")

    # Append to deques
    one_samples.append(one_reading)
    two_samples.append(two_reading)
    three_samples.append(three_reading)

    # Calculate moving averages if enough samples are available
    if len(one_samples) == window_size:
        one = round(sum(one_samples) / window_size, 2)
        two = round(sum(two_samples) / window_size, 2)
        three = round(sum(three_samples) / window_size, 2)
        # print(f"Stable values - One: {one}, Two: {two}, Three: {three}")

        # Calculate and print selector values for debugging
        selectorValueFloat1 = round(one / (0.454545))
        selectorValueFloat2 = round(two / (0.454545))
        selectorValueFloat3 = round(three / (0.454545))
        # selectorValueFloat3 = 5
        # print(f"Selector Values - One: {selectorValueFloat1}, Two: {selectorValueFloat2}, Three: {selectorValueFloat3}")
        current_values = [selectorValueFloat1, selectorValueFloat2, selectorValueFloat3]
        print(current_values)

        # If it's the first iteration, we set the last_value to the current_values.
        # This serves as a baseline to compare with in the next iterations.
        if last_value is None:
            last_value = current_values

        # If the current_values are the same as the last_value and initial_change is True,
        # it means we have a repetition. We increment the repetitions count.
        # The condition initial_change is True ensures that we have encountered at least
        # one change in the values before we start counting repetitions.
        elif last_value == current_values and initial_change:
            repetitions += 1

        # If the current_values are different from the last_value, it means a change has occurred.
        # We set the last_value to the current_values to reflect this change and reset repetitions to 0.
        # We also set initial_change to True, signifying that we've encountered the first change in values.
        elif last_value != current_values:
            last_value = current_values
            repetitions = 0  # Reset repetitions
            initial_change = True  # Mark the initial change
            print("change detected")

        # IN CASE OF TRIGGERING IMAGE GENERATION BY A BUTTON
        # if buttonGenerate == 1:
        #    package = [one, selectorValueFloat1, selectorValueFloat2, selectorValueFloat3, button, "hello"]
        #    message = json.dumps(package)
        #    message = message.encode()
        #    print("sending message, waiting 15 seconds!")
        #    socket.send_multipart([b"client1", message])
        #    time.sleep(15)

        if repetitions == 15:  # Send message after 3 seconds (30*0.1s) of no change
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

            repetitions = 0  # Reset repetitions
            last_value = None
            initial_change = False  # Reset the initial change flag
            time.sleep(15)

        # Sleep to maintain the desired sampling rate
        elapsed_time = time.time() - start_time
        sleep_time = max(0, (sampling_interval_ms / 1000) - elapsed_time)
        time.sleep(sleep_time)

socket.close()
context.term()