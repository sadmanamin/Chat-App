import json
import threading
import time

import eventlet
import pika
import socketio

sio = socketio.Server()
app = socketio.WSGIApp(
    sio, static_files={"/": {"content_type": "text/html", "filename": "index.html"}}
)

sid_name_mapping = {}
sid_list = []
round_robin_for_sid = {}
name_channel_map = {}
message_sessions = {}

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

def create_rabbitmq_connection(queue):
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel1 = connection.channel()
    channel1.queue_declare(queue=queue)
    # print('New channel declared')
    return channel1


@sio.event
def join_chat(sid, message):
    print(message.get("name", sid) + " joined to {}".format(message["room"]))
    sio.enter_room(sid, message["room"])


@sio.event
def set_name(sid, data):
    sid_name_mapping[sid] = data["name"]
    sid_name_mapping[data["name"]] = sid
    name_channel_map[data['name']] = create_rabbitmq_connection(data['name'])
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
    sender = sid_name_mapping[sid]
    # print(message)
    if message["message"] == 'End Session':
        print('inside end session')
        prev_reciever = message_sessions[sender]
        message_sessions.pop(sender)
        message_sessions.pop(prev_reciever)
        receiver = prev_reciever
        message["message"] = 'Session Ended'

    elif sid_name_mapping[sid] not in message_sessions.keys():
        idx = get_rr_number(sid)
        receiver = sid_name_mapping[sid_list[idx]]
        
        message_sessions[sender] = receiver
        message_sessions[receiver] = sender
    else:
        receiver = message_sessions[sender]
    
    message_payload = {
        "sid": sid,
        "body": message["message"],
        "sender": sender,
        "receiver": receiver,
        "room": message["room"],
    }
    print("Sending Message ", message_payload)
    receiver_channel = name_channel_map[receiver]
    receiver_channel.basic_publish(
        exchange="", routing_key=receiver, body=json.dumps(message_payload)
    )


@sio.event
def disconnect(sid):
    sid_list.remove(sid)
    client_name = sid_name_mapping[sid]
    name_channel_map.pop(client_name)
    sid_name_mapping.pop(client_name)
    sid_name_mapping.pop(sid)
    round_robin_for_sid.pop(sid)
    print("{} disconnected".format(client_name))

def get_rr_number(sid):
    # print(sid_list)
    # print(round_robin_for_sid)
    end = len(sid_list)
    start = (round_robin_for_sid[sid]["sid"] + 1) % end
    # print("start, end", start, end)
    for idx in range(start, end):
        if sid_list[idx] != sid:
            round_robin_for_sid[sid]["sid"] = idx
            # print("found idx -", idx)
            return idx


if __name__ == "__main__":

    eventlet.wsgi.server(eventlet.listen(("", 5000)), app)
