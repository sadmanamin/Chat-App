from http import client
import json
import threading
from time import sleep, time
import pika

import socketio

socket_producer = socketio.Client()
socket_consumer = socketio.Client()

PRODUCER_URL = "http://localhost:5000"
CONSUMER_URL = "http://localhost:5001"

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()



class Client:
    def __init__(self, client_name, room_name="default"):
        self.client_name = client_name
        self.room_name = room_name


@socket_producer.event
def connect():
    print("Server connection established")
    socket_producer.emit(
        "join_chat", {"room": client_name, "name": client_name}
    )
    socket_producer.emit("set_name", {"name": client_name})


@socket_consumer.event
def connect():
    print("Consumer connection established")
    socket_consumer.emit(
        "join_chat", {"room": client_name, "name": client_name}
    )
    socket_consumer.emit("set_name", {"name": client_name})

def callback(ch, method, properties, body):
    # print(" [x] Received %r" % body)
    body = json.loads(body)
    sender = body['sender']
    message = body['body']

    if message == 'Session Ended':
        print("{} by {}\nMessage: ".format(message,sender),end="")
    else:
        print("{} sent: {}\nReply: ".format(sender,message),end="")


def consumer():
    channel.basic_consume(queue=client_name, auto_ack=True, on_message_callback=callback)

    # print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


@socket_consumer.event
def get_message(message):
    print("Inside get message")
    if client_name == message["from"]:
        print("You : " + message["message"])
    else:
        msg_ending = "\nmessage : "
        if message["status"] == "sending":
            message_status = "sending"
            msg_ending = "\nreply : "
        elif message["status"] == "replying":
            message_status = "replying"
        else:
            message_status = None
        print("\n" + message["from"] + " : " + message["message"] + msg_ending)


@socket_producer.event
def disconnect():
    print("disconnected from producer")


@socket_consumer.event
def disconnect():
    print("disconnected from consumer")



def connect_to_producer():
    socket_producer.connect(PRODUCER_URL)
    socket_producer.wait()


def send_message():
    global client_name
    while True:
        sleep(0.05)


        msg = input("Message: ")
        socket_producer.emit(
            "send_chat_room",
            {
                "message": msg,
                "name": client_name,
                "room": client_name
            },
        )


if __name__ == "__main__":
    client_name = input("Client Name: ")
    channel.queue_declare(queue=client_name)
    # room_name = 'default'
    message_status = None
    connect_prodcuer_thread = threading.Thread(target=connect_to_producer, args=())
    connect_prodcuer_thread.start()

    consumer_thread = threading.Thread(target=consumer, args=())
    consumer_thread.start()

    print("Going to send message")
    send_message_thread = threading.Thread(target=send_message, args=())
    send_message_thread.start()

    # client = Client(client_name=client_name)
    # send_message_thread = threading.Thread(target=client.send_message, args=())
    # send_message_thread.start()
