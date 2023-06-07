import time
import zmq
import json
import automationhat

time.sleep(0.1)  # short pause after ads1015 class creation recommended

context = zmq.Context()

# Socket to talk to server
print("Connecting to server...")
socket = context.socket(zmq.PUB)
socket.connect("tcp://localhost:5555")

last_value = None
repetitions = 0
initial_change = False  # New flag for initial change

while True:
    one = automationhat.analog.one.read()
    two = automationhat.analog.two.read()
    three = automationhat.analog.three.read()
    button = automationhat.input.three.read()
    selectorValueFloat1 = 12 - round(one / (0.454545))
    selectorValueFloat2 = 12 - round(two / (0.454545))
    selectorValueFloat3 = 12 - round(three / (0.454545))

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

    if repetitions == 30:  # Send message after 3 seconds (30*0.1s) of no change
        package = [one, selectorValueFloat1, selectorValueFloat2, selectorValueFloat3, button, "hello"]
        message = json.dumps(package)
        message = message.encode()
        print("sending message, waiting 3 seconds!")
        socket.send_multipart([b"client1", message])
        repetitions = 0  # Reset repetitions
        last_value = None
        initial_change = False  # Reset the initial change flag
        time.sleep(3)

    time.sleep(0.1)

socket.close()
context.term()