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

# Socket to talk to server
print("Connecting to server...")
socket = context.socket(zmq.PUB)

# Connect to server with retries
while True:
    try:
        socket.connect("tcp://localhost:5555")
        break
    except Exception as e:
        print("Failed to connect to server, retrying in 5 seconds...", str(e))
        time.sleep(5)

last_value = None
repetitions = 0
initial_change = False  # New flag for initial change

while True:
    try:
        one = automationhat.analog.one.read()
        two = automationhat.analog.two.read()
        three = automationhat.analog.three.read()
        button = automationhat.input.one.read()
        # buttonGenerate = automationhat.input.two.read()
    except Exception as e:
        print("Failed to read from automationhat, retrying in 1 second")
        time.sleep(1)
        continue

    selectorValueFloat1 = round(one / (0.454545))
    selectorValueFloat2 = round(two / (0.454545))
    selectorValueFloat3 = round(three / (0.454545))

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

    time.sleep(0.1)

socket.close()
context.term()