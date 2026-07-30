import zmq



context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.bind('tcp://127.0.0.1:2000')


message = "This is a message from CS361"

socket.send_string(message)