import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5556")  # Connect to the new port

socket.setsockopt(zmq.SUBSCRIBE, b"client1")

while True:
    message = socket.recv_multipart()
    topic, data = message
    print(message)
    print("Message received")
    # Process the received message as needed
