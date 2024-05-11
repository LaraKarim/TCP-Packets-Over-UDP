import socketserver
import random
import os
import webbrowser
from collections import deque

def printmessage(message):
    splitmessage = message.split(" ")
    print("------------------")
    print("SYNbit: " + splitmessage[0])
    print("ACKbit: " + splitmessage[1])
    print("SEQnum: " + splitmessage[2])
    print("ACKnum: " + splitmessage[3])
    print("FINbit: " + splitmessage[4])
    print("checksum: " + splitmessage[5])
    print("message: " + ' '.join(splitmessage[6:]))
    print("------------------")

class MyUDPHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.window_size = 3
        self.window = deque()
        self.base = 0
        self.next_seq_num = 0
        super().__init__(request, client_address, server)

    def simulate_network_behavior(self, data):
        if random.random() < 0.02:  # 10% packet loss
            print(f"Packet lost")
            return None
        else:
            data_list = list(data)
            if random.random() < 0.1:  # 10% packet corruption
                print(f"Packet corrupted")
                # Corrupt one random character in the message
                index = random.randint(0, len(data_list) - 1)
                data_list[index] = chr(random.randint(0, 255))
            return ''.join(data_list)

    def handle(self):
        global SEQnum
        global ACKnum
        global message
        global connection_established
        data = self.request[0].strip()
        socket = self.request[1]
        print("{} wrote:".format(self.client_address[0]))
        data = str(data, "utf-8")
        print(data)
        received = data.split(" ")
        
        receivedSYNbit = int(received[0])
        receivedACKbit = int(received[1])
        receivedSEQnum = int(received[2])
        recievedACKnum = int(received[3])
        receivedFINbit = int(received[4])
        if received[5] == "None":
            receivedMessage = None
            print(f"recevied synbit: {receivedSYNbit}")
            print(f"recevied ackbit: {receivedACKbit}")
            print(f"recevied seqnum: {receivedSEQnum}")
            print(f"recevied acknum: {recievedACKnum}")

        else:
            receivedchecksum = int(received[5])
            receivedMessage = ' '.join(received[6:])
            print("received message: ")
            printmessage(data)
           
        if receivedFINbit == 1:
            print("Received finbit, connection closed")
            ACKbit=1
            FINbit=0
            ACKnum=receivedSEQnum+1
            SEQnum=recievedACKnum
            message=None
            SYNbit=0
            data = f"{SYNbit} {ACKbit} {SEQnum} {ACKnum} {FINbit} 0 {message}"
            print("sending message to acknowledge finalize from client")
            printmessage(data)
            socket.sendto(bytes(data + "\n", "utf-8"), self.client_address)
            FINbit=1
            SEQnum=SEQnum+1
            ACKnum=ACKnum+1
            message=None
            ACKbit=0
            data = f"{SYNbit} {ACKbit} {SEQnum} {ACKnum} {FINbit} 0 {message}"
            print("closing connection from server side")
            printmessage(data)
            socket.sendto(bytes(data + "\n", "utf-8"), self.client_address)
            # receive a message from the client closing the connection
            received = str(socket.recv(1024), "utf-8")
            
            received = received.split(" ")
            receivedSYNbit = int(received[0])
            receivedACKbit = int(received[1])
            receivedSEQnum = int(received[2])
            recievedACKnum = int(received[3])
            receivedFINbit = int(received[4])
            if receivedACKbit == 1:
                print("Connection closed")
                exit(0)
        if receivedSYNbit == 1 and receivedACKbit == 0:
            SYNbit = 1
            ACKbit = 1
            SEQnum = 10
            ACKnum = receivedSEQnum + 1
            message = None
            FINbit=0
            data = f"{SYNbit} {ACKbit} {SEQnum} {ACKnum} {message}"
            print("sending message to acknowledge connection from client")
            print(f"SYNbit: {SYNbit}")
            print(f"ACKbit: {ACKbit}")
            print(f"SEQnum: {SEQnum}")
            print(f"ACKnum: {ACKnum}")
            print(f"message: {message}")
            socket.sendto(bytes(data + "\n", "utf-8"), self.client_address)
        
        if receivedSYNbit == 0 and receivedACKbit == 1 and receivedSEQnum == ACKnum and connection_established == False:
            connection_established = True
            print("Connection established")
            SEQnum = 11
            ACKnum = receivedSEQnum + 1
        
        if receivedSYNbit == 0 and receivedACKbit == 0 or (receivedACKbit==1 and connection_established==True) and receivedSEQnum == ACKnum:
            if message != None:
                print(f"length of message: {len(message)}")
                if recievedACKnum==SEQnum+len(message):
                    print("acknowledgement received from client")
          
            if receivedchecksum == sum(receivedMessage.encode('utf-8')):
                print("No error detected in checksum")
            else:
                print("Error detected in checksum")
                return
            ACKnum = receivedSEQnum + len(receivedMessage)
            SEQnum = recievedACKnum
            SYNbit = 0
            ACKbit = 1
            FINbit = 0
            receivedMessage = receivedMessage.split(" ")
            
            if receivedMessage[0].upper() != "GET" and receivedMessage[0].upper() != "POST":
                print("Invalid command echoing back to client, 400 Bad Request")
                message = "HTTP/1.0 400 Bad Request -> \r\n\r\n" + ' '.join(receivedMessage[0:]) + "\n"
                checksum = sum(message.encode('utf-8'))
                data = f"{SYNbit} {ACKbit} {SEQnum} {ACKnum} {FINbit} {checksum} {message}"
                socket.sendto(bytes(data + "\n", "utf-8"), self.client_address)
            else:
                if receivedMessage[0].upper() == "GET":
                    print("GET command received")
                    try:
                        if (".html") in receivedMessage[1]:
                            webbrowser.open('file://' + os.path.realpath(receivedMessage[1]))
                            message = f"HTTP/1.0 200 OK -> \r\n\r\n page opened"
                        else:
                            f = open(receivedMessage[1], "r")
                            print("File exists, sending file status code 200 OK")
                            message = f.read()
                            message="HTTP/1.0 200 OK -> \r\n\r\n" + message
                            f.close()
                        checksum = sum(message.encode('utf-8'))
                        print(f"checksum: {checksum}")
                        data = f"{SYNbit} {ACKbit} {SEQnum} {ACKnum} {FINbit} {checksum} {message}"
                        socket.sendto(bytes(data + "\n", "utf-8"), self.client_address)
                    except IOError:
                        print("File does not exist, sending 404 Not Found")
                        message = "HTTP/1.0 404 Not Found -> " + receivedMessage[1] + "\n"
                        checksum = sum(message.encode('utf-8'))
                        data = f"{SYNbit} {ACKbit} {SEQnum} {ACKnum} {FINbit} {checksum} {message}"
                        socket.sendto(bytes(data + "\n", "utf-8"), self.client_address)
                elif receivedMessage[0].upper() == "POST":
                    print("POST command received")
                    try:
                        f = open(receivedMessage[1], "w")
                        print("File exists, sending 200 OK")
                        message = ' '.join(receivedMessage[2:])
                        f.write(message)
                        message = "200 OK"
                        checksum = sum(message.encode('utf-8'))
                        data = f"{SYNbit} {ACKbit} {SEQnum} {ACKnum} {FINbit} {checksum} {message}"
                        socket.sendto(bytes(data + "\n", "utf-8"), self.client_address)
                    except IOError:
                        print("File does not exist")
                        message = "404 Not Found"
                        checksum = sum(message.encode('utf-8'))
                        data = f"{SYNbit} {ACKbit} {SEQnum} {ACKnum} {FINbit} {checksum} {message}"
                        socket.sendto(bytes(data + "\n", "utf-8"), self.client_address)

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    connection_established = False
    with socketserver.UDPServer((HOST, PORT), MyUDPHandler) as server:
        server.serve_forever()
