import serial
import serial.tools.list_ports
import zmq
import time

# find the connected Arduino board (only works with 1 board, or well, it will take the first one)
ports = list(serial.tools.list_ports.grep('Arduino'))
arduino_port = ports[0].device if ports else None

if not arduino_port:
    raise Exception("No Arduino found")

# set up the serial line
ser = serial.Serial(arduino_port, 57600)
# ,
# parity=serial.PARITY_NONE,
# stopbits=serial.STOPBITS_ONE,
# bytesize=serial.EIGHTBITS,
# timeout=0)

# # set up zmq context and socket
# context = zmq.Context()
# # socket = context.socket(zmq.PUB) # PUB socket for publishing messages
# socket = context.socket(zmq.PUSH)
# socket.bind("tcp://localhost:5555") # replace with your desired address

context = zmq.Context()

# Socket to talk to server
print("Connecting to server...")
socket = context.socket(zmq.PUSH)
socket.connect("tcp://localhost:5555")

def map_range(value, from_range, to_range):
    (from_min, from_max) = from_range
    (to_min, to_max) = to_range
    return round(((value - from_min) / (from_max - from_min)) * (to_max - to_min) + to_min)

last_value = None

try:
    while True:
        # read a line from the serial port
        line = ser.readline().decode('utf-8').strip()
        
        # convert the line to an integer and map it to the new range
        value = int(line)
        mapped_value = map_range(value, (0, 255), (0, 3))
        # print(mapped_value)

        # send the mapped value over zmq
        if mapped_value != last_value:
            socket.send_string(str(mapped_value))
            print("sending a message: " + str(mapped_value))
            last_value = mapped_value

except KeyboardInterrupt:
    print("Program interrupted by user, closing...")

except Exception as e:
    print("Error: " + str(e))

finally:
    ser.close()
    print("Serial port closed.")
    context.term()
    print("zmq context terminated.")

