import json
from os import PRIO_PGRP
import threading

import eventlet
import pika
import socketio

sio = socketio.Server(engineio_logger=True)
app = socketio.WSGIApp(
    sio, static_files={"/": {"content_type": "text/html", "filename": "index.html"}}
)

sid_name_mapping = {}
sid_list = []
connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()
channel.queue_declare(queue="hello")


@sio.event
def join_chat(sid, message):
    print(message.get("name", sid) + " joined to {}".format(message["room"]))
    sio.enter_room(sid, message["room"])


@sio.event
def exit_chat(sid, message):
    sio.leave_room(sid, message["room"])


@sio.event
def connect(sid, environ):

    print("{} connected".format(sid))
    sid_list.append(sid)
    sio.emit("my_response", {"data": "Connected", "count": 0}, room=sid)


@sio.event
def set_name(sid, data):
    sid_name_mapping[sid] = data["name"]
    sid_name_mapping[data["name"]] = sid


@sio.event
def disconnect(sid):
    print("Client disconnected")


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    body = json.loads(body)
    print(sid_name_mapping)
    print(body["receiver"], sid_name_mapping[body["receiver"]])
    try:
        sio.emit(
            "get_message",
            {
                "sid": body["sid"],
                "sender": body["sender"],
                "receiver": body["receiver"],
                "body": body["body"],
                "room": body["room"],
            },
            room=body["receiver"],
        )
    except Exception as e:
        print(e)
    print("after emit")


def consumer():
    channel.basic_consume(queue="hello", auto_ack=True, on_message_callback=callback)

    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


# print(' [*] Waiting for messages. To exit press CTRL+C')
# channel.start_consuming()

if __name__ == "__main__":
    # publisher.queue_declare(queue='broadcast')
    consumer_thread = threading.Thread(target=consumer, args=())
    consumer_thread.start()
    eventlet.wsgi.server(eventlet.listen(("", 5001)), app)
