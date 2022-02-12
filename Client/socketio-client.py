from http import client
import json
import threading
from time import sleep, time
import pika
import socketio

SERVER_URL = "http://localhost:5000"
RABBITMQ_SERVER = 'localhost'

socket_client = socketio.Client()

connection = pika.BlockingConnection(
    pika.ConnectionParameters(RABBITMQ_SERVER, heartbeat=600)
)
channel = connection.channel()


def connect_to_server():
    # Connects to the message server
    
    socket_client.connect(SERVER_URL)
    socket_client.wait()


@socket_client.event
def connect():
    # Gets triggered when connected to the server
    # Registers related user information 
    
    print("Server connection established")
    socket_client.emit(
        "join_chat", 
        {
            "room": client_name, 
            "name": client_name
        }
    )
    socket_client.emit(
        "set_client_info", 
        {
            "name": client_name
        }
    )
 
   
@socket_client.event
def disconnect():
    # Gets triggered when disconnected from the server
    print("disconnected from server")


def callback_for_received_message(ch, method, properties, body):
    # Gets triggered when a new message is consumed
    
    body = json.loads(body)
    sender = body['sender']
    message = body['message']

    if message == 'Session Ended':
        print("{} by {}\nMessage: ".format(message,sender),end="")
    else:
        print("{} sent: {}\nReply: ".format(sender,message),end="")
        
        
def consume_message(client_name):
    # Consumes new messages that get push to the queue
    
    channel.basic_consume(
        queue=client_name, 
        auto_ack=True, 
        on_message_callback=callback_for_received_message
    )
    channel.start_consuming()


def send_message(client_name):
    # Infinite loop for sending message that runs on a Thread
    
    while True:
        sleep(1)

        msg = input("Message: ")
        socket_client.emit(
            "message_handler",
            {
                "message": msg,
                "name": client_name,
                "room": client_name
            },
        )

        
def start_all_thread(client_name):
    # Starts server, message consumer and sender thread
    
    connect_prodcuer_thread = threading.Thread(target=connect_to_server, args=())
    connect_prodcuer_thread.start()

    consumer_thread = threading.Thread(target=consume_message, args=(client_name,))
    consumer_thread.start()

    send_message_thread = threading.Thread(target=send_message, args=(client_name,))
    send_message_thread.start()


if __name__ == "__main__":
    client_name = input("Client Name: ")
    
    channel.queue_declare(queue=client_name)
    
    start_all_thread(client_name)
    
    
