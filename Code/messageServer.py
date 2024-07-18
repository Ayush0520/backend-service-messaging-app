import zmq
import json
import threading

context = zmq.Context()

# Socket for receiving user requests
user_request_socket = context.socket(zmq.ROUTER)
user_request_socket.bind("tcp://10.190.0.2:9000")

# Socket for group registration requests
group_registration_socket = context.socket(zmq.ROUTER)
group_registration_socket.bind("tcp://10.190.0.2:9001")

# Dictionary to store registered group information (name as key, IP as value)
registered_groups = {} 

def handle_user_requests():
    while True:
        # Receives identity and message
        identity, message = user_request_socket.recv_multipart()
        print(f"Group List Request From {identity}")

        # Extract group names and IPs
        group_info = []
        for name, ip in registered_groups.items():
            group_info.append({"name": name, "ip": ip})

        response = json.dumps({"groups": group_info}).encode("utf-8")
        # send_multipart method in ZeroMQ expects all frames to be bytes-like objects encode("utf-8") encodes the string as bytes, making it compatible with ZeroMQ
        # Send to the same user
        user_request_socket.send_multipart([identity, response])

def handle_group_registration_requests():
    while True:
        identity, message = group_registration_socket.recv_multipart()  # Receive identity and message
        group_data = json.loads(message)

        group_name = group_data["name"]
        group_ip = group_data["ip"]

        print(f"Join request from Group Name:{group_name} IP:{group_ip}")

        if group_name in registered_groups:
            response = {"success": False, "message": "Group already exists"}
            print("Registration Status: Already Registered")
        else:
            registered_groups[group_name] = group_ip  # Add to dictionary
            response = {"success": True, "message": "Group registered successfully"}
            print("Registration Status: Success")

        group_registration_socket.send_multipart([identity, json.dumps(response).encode("utf-8")])  # Send response to group server

# Creating threads for handling requests
user_request_thread = threading.Thread(target=handle_user_requests)
user_request_thread.start()

group_registration_thread = threading.Thread(target=handle_group_registration_requests)
group_registration_thread.start()

# Keeping the main thread running to prevent the server from exiting
while True:
    pass
