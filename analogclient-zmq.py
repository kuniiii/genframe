import time
import zmq
import json
import automationhat
time.sleep(0.1) # short pause after ads1015 class creation recommended

context = zmq.Context()

# Socket to talk to server
print("Connecting to server...")
# socket = context.socket(zmq.REQ)
socket = context.socket(zmq.PUSH)
socket.connect("tcp://localhost:5555")

while True:
    one = automationhat.analog.one.read()
    two = automationhat.analog.two.read()
    three = automationhat.analog.three.read()
    button = automationhat.input.three.read()
    selectorValueFloat1 = round(one / (0.416666))
    selectorValueFloat2 = round(two / (0.416666))
    selectorValueFloat3 = round(three / (0.416666))
    package = [one, selectorValueFloat1, selectorValueFloat2, selectorValueFloat3, button, "hello"]
    # print("Sending push message")

    message = json.dumps(package)
    # need to encode it, otherwise zmq will not send it due to type error
    message = message.encode()
    socket.send_multipart([b"client1", message])
    # socket.send(b(message))

    time.sleep(0.1)
socket.close()
context.term()