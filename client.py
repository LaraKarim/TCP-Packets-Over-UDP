import socket
import sys
import random
from collections import deque

# Function to print the message details
def print_message(message):
    split_message = message.split(" ")
    print("------------------")
    print("SYNbit: " + split_message[0])
    print("ACKbit: " + split_message[1])
    print("SEQnum: " + split_message[2])
    print("ACKnum: " + split_message[3])
    print("FINbit: " + split_message[4])
    print("checksum: " + split_message[5])
    print("message: " + ' '.join(split_message[6:]))
    print("------------------")

# Constants
HOST, PORT = "localhost", 9999

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Establish a connection with a 3-way handshake
SYNbit = 1
ACKbit = 0
SEQnum = 5
ACKnum = 0
FINbit = 0
message = None
data = f"{SYNbit} {ACKbit} {SEQnum} {ACKnum} {FINbit} {message}"

# Function to simulate packet loss and corruption
def simulate_network_behavior(data):
    if random.random() < 0.02:  # Simulate 2% packet loss
        print(f"Packet lost")
        return None
    else:
        data_list = list(data)
        if random.random() < 0.1:  # Simulate 10% packet corruption
            print(f"Packet corrupted")
            # Corrupt one random character in the message
            index = random.randint(0, len(data_list) - 1)
            data_list[index] = chr(random.randint(0, 255))
        return ''.join(data_list)

data = simulate_network_behavior(data)
if data:
    sock.sendto(bytes(data + "\n", "utf-8"), (HOST, PORT))

# Print connection establishment details
print("Sent message to server to establish connection")
print("SYNbit:", SYNbit)
print("ACKbit:", ACKbit)
print("SEQnum:", SEQnum)
print("ACKnum:", ACKnum)
print("FINbit:", FINbit)
print("------------------")

# Receive acknowledgment from the server
received = str(sock.recv(1024), "utf-8")
received_fields = received.split(" ")

# Print received message details
print("Received message:")
for field, value in zip(["SYNbit", "ACKbit", "SEQnum", "ACKnum"], received_fields):
    print(f"{field}: {value}")
print("------------------")

# Check if the connection is established
if received_fields[0] == "1" and received_fields[1] == "1" and int(received_fields[3]) == SEQnum + 1:
    SEQnum += 1
    ACKnum = int(received_fields[2]) + 1
    SYNbit = 0
    ACKbit = 1
    FINbit = 0
    data = f"{SYNbit} {ACKbit} {SEQnum} {ACKnum} {FINbit} 0 {message}"
    sock.sendto(bytes(data + "\n", "utf-8"), (HOST, PORT))
    print("Sent message:")
    print_message(data)

print("Connection established")
SEQnum += 1
ACKbit = 0

# Sliding window parameters
window_size = 3
window = deque()
base = SEQnum
next_seq_num = SEQnum

# Message transfer phase
while True:
    SYNbit = 0
    print("------------------")
    message = input("Enter message: ")
    if message == "exit":
        FINbit = 1

    # Prepare data to be sent
    message_bits = message.encode('utf-8')
    checksum = sum(message_bits)
    data = f"{SYNbit} {ACKbit} {next_seq_num} {ACKnum} {FINbit} {checksum} {message}"
    
    # Simulate packet loss and corruption
    data = simulate_network_behavior(data)
    if data:
        # Send data if window is not full
        if len(window) < window_size:
            sock.sendto(bytes(data + "\n", "utf-8"), (HOST, PORT))
            print("Sent message:")
            print_message(data)
            window.append((data, next_seq_num))
            next_seq_num += 1
    
        # Print window size and buffer
        print(f"Window Size taken: {len(window)}, Window availability: {window_size - len(window)}")
    
        # Receive acknowledgment
        try:
            sock.settimeout(5)
            received = str(sock.recv(1024), "utf-8")
            print("Received message:")
            print_message(received)
            received_fields = received.split(" ")
            received_seq_num = int(received_fields[3])
        
            # Slide the window
            while window and window[0][1] < received_seq_num:
                window.popleft()
        
            # Handle FINbit
            received_finbit = int(received_fields[4])
            if received_finbit == 1:
                print("Received FINbit, connection closed")
                print_message(received)
                ACKbit = 1
                FINbit = 0
                ACKnum = int(received_fields[2]) + max(1, len(received_fields[6]) - 1)
                message = None
                data = f"{SYNbit} {ACKbit} {next_seq_num} {ACKnum} {FINbit} 0 {message}"
                print("Sent message in response to closing connection:")
                print_message(data)
                sock.sendto(bytes(data + "\n", "utf-8"), (HOST, PORT))
                break
        
        except socket.timeout:
            print("Timeout occurred. Resending unacknowledged packets.")
            for packet, seq_num in window:
                sock.sendto(bytes(packet + "\n", "utf-8"), (HOST, PORT))
                print("Resent message:")
                print_message(packet)
