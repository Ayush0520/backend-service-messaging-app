import zmq
import json
import threading

from datetime import datetime

class Message:
    def __init__(self, username, message, timestamp=None):
        self.username = username
        self.message = message
        if timestamp is None:
            self.timestamp = datetime.now()
        else:
            self.timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")  # Assuming timestamp format

    def __str__(self):
        return f"[{self.timestamp}] {self.username}: {self.message}"

    def json_serialize(self):
        return {
            "username": self.username,
            "message": self.message,
            "timestamp": self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),  # Convert timestamp to string
        }

# Create ZeroMQ context and socket
context = zmq.Context()

# Message server communication
MESSAGE_SERVER_ADDRESS = "34.131.84.209"
MESSAGE_SERVER_PORT = 9001

# Socket for receiving user requests
user_request_socket = context.socket(zmq.ROUTER)
user_request_socket.bind("tcp://10.128.0.3:9002")

group_members = []
group_messages = []

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

def register_group(context, group_name, ip_addr):
    """
    Registers a new group with the message server.

    Args:
        context: ZeroMQ context
        group_name (str): The name of the group.
        ip_addr: IP Address of the Group's VM


    Returns:
        bool: True if registration was successful, False otherwise.
    """

    socket = context.socket(zmq.DEALER)
    socket.connect(f"tcp://{MESSAGE_SERVER_ADDRESS}:{MESSAGE_SERVER_PORT}")

    message = {"type": "REGISTER_GROUP", "name": group_name, "ip": ip_addr}
    send_message(socket, message)
    response = receive_message(socket)

    # Cleanup Resource
    socket.close()

    if response["success"] == True:
        print(f"Group '{group_name}' Registered Successfully!")
    else:
        print(f"Group Registration Failed: {response['message']}")
    
def join_group(username, identity):
    if username in group_members:
        print(f"User '{username}' already exists in the group.")
        response = json.dumps({"status":False, "message": "Already Registered"}).encode("utf-8")
    else:
        group_members.append(username)
        print(f"User '{username}' Registered Successfully!")
        response = json.dumps({"status":True, "message": "User Registered"}).encode("utf-8")

    user_request_socket.send_multipart([identity, response])
    
def leave_group(username, identity):
    if username not in group_members:
        print(f"User '{username}' is not a member of the group.")
        response = json.dumps({"status":False, "message": "User doesn't exist"}).encode("utf-8")
    else:
        print(f"User '{username}' left the group.")
        group_members.remove(username)
        response = json.dumps({"status":True, "message": "Group Left"}).encode("utf-8")

    user_request_socket.send_multipart([identity, response])

def fetch_messages(username, identity, timestamp):
    if username not in group_members:
        print(f"User '{username}' is not a member of the group.")
        response = json.dumps({"status":False, "message": "User doesn't exist"}).encode("utf-8")
    else:
        filtered_messages = []
        if timestamp is None:
            filtered_messages = group_messages[:]  # Make a copy to avoid modifying original list
        else:
            timestamp_obj = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
            filtered_messages = [message for message in group_messages if message.timestamp >= timestamp_obj]
        response = json.dumps({
        "status": True,
        "messages": [message.json_serialize() for message in filtered_messages],
        }).encode("utf-8")
    
    user_request_socket.send_multipart([identity, response])

def save_message(username, identity, message, timestamp=None):
    if username not in group_members:
        print(f"User '{username}' is not a member of the group.")
        response = json.dumps({"status":False, "message": "User doesn't exist"}).encode("utf-8")
    else:
        new_message = Message(username, message, timestamp)
        group_messages.append(new_message)
        response = json.dumps({"status":True, "message": "Message Received"}).encode("utf-8")
    user_request_socket.send_multipart([identity, response])
     

def main():
    print("Group Registration Intialized")
    group_name = input("Enter Group Name: ")
    ip_addr = input("Enter the IP Address: ")

    # Register Group
    register_group(context, group_name, ip_addr)

    while True:
        # Receives identity and message
        identity, message = user_request_socket.recv_multipart()
        message = json.loads(message)
        message_type = message["type"]
        user_id = message["user_id"]

        if message_type == "JOIN":
            print(f"JOIN Request Received from User: {user_id}")
            join_group(user_id, identity)
        elif message_type == "LEAVE":
            print(f"LEAVE Request Received from User: {user_id}")
            leave_group(user_id, identity)
        elif message_type == "GET":
            print(f"GET Message Request Received from User: {user_id}")
            timestamp = message["timestamp"]
            fetch_messages(user_id, identity, timestamp)
        elif message_type == "PUT":
            print(f"Message sent from USer: {user_id}")
            timestamp = message["timestamp"]
            user_message = message["message"]
            save_message(user_id, identity, user_message, timestamp)





if __name__ == "__main__":
    main()