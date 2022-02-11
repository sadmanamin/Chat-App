import json
import threading
import time

import eventlet
import pika
import socketio

sio = socketio.Server(engineio_logger=True)
app = socketio.WSGIApp(
    sio, static_files={"/": {"content_type": "text/html", "filename": "index.html"}}
)

sid_name_mapping = {}
sid_list = []
round_robin_for_sid = {}

# class RabbitMQ():
#     def __init__(self,host='localhost'):
#         self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
#         self.channel = self.connection.channel()

#     def queue_declare(self, queue='default'):
#         self.channel.queue_declare(queue=queue)

#     def basic_publish(self, exchange='',routing_key='',body=''):
#         self.channel.basic_publish(
#             exchange=exchange,
#             routing_key=routing_key,
#             body=json.dumps(body)
#         )

# publisher = RabbitMQ()

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel1 = connection.channel()
channel1.queue_declare(queue="hello")


@sio.event
def join_chat(sid, message):
    print(message.get("name", sid) + " joined to {}".format(message["room"]))
    sio.enter_room(sid, message["room"])


@sio.event
def set_name(sid, data):
    sid_name_mapping[sid] = data["name"]
    sid_name_mapping[data["name"]] = sid

    round_robin_for_sid[sid] = {"sid": -1, "name": data["name"]}


@sio.event
def connect(sid, environ):
    print("{} connected".format(sid))
    sid_list.append(sid)
    sio.emit("my_response", {"data": "Connected", "count": 0}, room=sid)


@sio.event
def exit_chat(sid, message):
    sio.leave_room(sid, message["room"])
    sid_list.remove(sid)



@sio.event
def send_chat_room(sid, message):
    idx = get_rr_number(sid)
    message_payload = {
        "sid": sid,
        "body": message["message"],
        "sender": message["name"],
        "receiver": sid_name_mapping[sid_list[idx]],
        "room": message["room"],
    }
    print("Sending Message ", message_payload)
    channel1.basic_publish(
        exchange="", routing_key="hello", body=json.dumps(message_payload)
    )


@sio.event
def disconnect(sid):
    print("Client disconnected")


def get_rr_number(sid):
    print(sid_list)
    print(round_robin_for_sid)
    end = len(sid_list)
    start = (round_robin_for_sid[sid]["sid"] + 1) % end
    print("start, end", start, end)
    for idx in range(start, end):
        if sid_list[idx] != sid:
            round_robin_for_sid[sid]["sid"] = idx
            print("found idx -", idx)
            return idx


if __name__ == "__main__":

    eventlet.wsgi.server(eventlet.listen(("", 5000)), app)
