import socket
import zmq
import json

from datetime import datetime

# User port management
PORT_FILE = "ports.txt"

def read_port():
    with open(PORT_FILE, "r") as f:
        return int(f.read().strip())

def write_port(port):
    with open(PORT_FILE, "w") as f:
        f.write(str(port))

def register_user():
    port = read_port() + 1
    write_port(port)
    return port

# Message server communication
MESSAGE_SERVER_ADDRESS = "34.131.84.209"
MESSAGE_SERVER_PORT = 9000

# Group Server Communication
GROUP_SERVER_PORT = 9002

def connect_to_message_server(context):
    """
    Creates a DEALER socket and connects to the message server.
    """
    socket = context.socket(zmq.DEALER)
    socket.connect(f"tcp://{MESSAGE_SERVER_ADDRESS}:{MESSAGE_SERVER_PORT}")
    return socket

def connect_to_group_server(context, ip_addr):
    """
    Creates a DEALER socket and connects to the group server.
    """
    socket = context.socket(zmq.DEALER)
    socket.connect(f"tcp://{ip_addr}:{GROUP_SERVER_PORT}")
    return socket

def send_message(socket, message):
    """
    Sends a JSON message to the message server.
    """
    socket.send_json(message)

def receive_message(socket):
    """
    Receives a JSON message from the message server.
    """
    return socket.recv_json()

def get_available_groups(socket):
    """
    Sends a request to the message server to get a list of available groups.
    """
    message = {"type": "get_groups"}
    send_message(socket, message)
    return socket.recv_json()

def join_group(socket, user_id):
    """
    Sends a request to the message server to join a specific group.
    """
    message = {"type": "JOIN", "user_id": user_id}
    send_message(socket, message)
    return receive_message(socket)

def leave_group(socket, user_id):
    """
    Sends a request to the message server to join a specific group.
    """
    message = {"type": "LEAVE", "user_id": user_id}
    send_message(socket, message)
    return receive_message(socket)


def send_group_message(socket, message, user_id, timestamp=None):
    """
    Sends a message to a specific group.
    """
    message = {"type": "PUT", "message": message, "timestamp": timestamp, "user_id": user_id}
    send_message(socket, message)
    return receive_message(socket)

def fetch_messages(socket, user_id, timestamp=None):
    """
    Fetches all messages or messages after a specific timestamp from a group.
    """
    message = {"type": "GET", "timestamp": timestamp, "user_id": user_id}
    send_message(socket, message)
    return receive_message(socket)

# User interaction and functionalities
def main():
    port = register_user()
    user_id = f"User{port - 49151}"
    print(f"New User Created Successfully! {user_id}")

    # Create ZeroMQ context and socket
    context = zmq.Context()

    # User interaction loop
    while True:
        print("\nMenu:")
        print("1. Get available groups")
        print("2. Join group")
        print("3. Leave group")
        print("4. Send Message")
        print("5. Fetch Message")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            socket = connect_to_message_server(context)
            print(get_available_groups(socket))
        elif choice == "2":
            ip_addr = input("Enter IP Address: ")
            socket = connect_to_group_server(context, ip_addr)
            print(join_group(socket, user_id))
        elif choice == "3":
            ip_addr = input("Enter IP Address: ")
            socket = connect_to_group_server(context, ip_addr)
            print(leave_group(socket, user_id))
        elif choice == "4":
            ip_addr = input("Enter IP Address: ")
            socket = connect_to_group_server(context, ip_addr)
            message = input("Enter your Message: ")
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            print(send_group_message(socket, message, user_id, timestamp))
        elif choice == "5":
            ip_addr = input("Enter IP Address: ")
            socket = connect_to_group_server(context, ip_addr)
            timestamp = input("Enter Timestamp(Format-example: 2024-02-17T10:00:00Z): ")
            if timestamp == "":
                timestamp = None
            print(fetch_messages(socket, user_id, timestamp))
        elif choice == "6":
            break


    # Clean up resources
    socket.close()
    context.term()
   

if __name__ == "__main__":
    main()
