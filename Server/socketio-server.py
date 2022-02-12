import json
import eventlet
import pika
import socketio

RABBITMQ_HOST = 'rabbitmq'

sio = socketio.Server()
app = socketio.WSGIApp(
    sio, static_files={"/": {"content_type": "text/html", "filename": "index.html"}}
)

sid_name_mapping = {}
sid_list = []
round_robin_for_sid = {}
name_channel_map = {}
message_sessions = {}


def create_rabbitmq_connection(queue):
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel1 = connection.channel()
    channel1.queue_declare(queue=queue)
    return channel1


@sio.event
def join_chat(sid, message):
    # Emitted by client to join the chat
    
    print(message.get("name", sid) + " joined to {}".format(message["room"]))
    sio.enter_room(sid, message["room"])


@sio.event
def set_client_info(sid, data):
    # Emitted by client to set client information
    
    sid_name_mapping[sid] = data["name"]
    sid_name_mapping[data["name"]] = sid
    name_channel_map[data['name']] = create_rabbitmq_connection(data['name'])
    round_robin_for_sid[sid] = {"sid": -1, "name": data["name"]}


@sio.event
def connect(sid, environ):
    # Get triggered when a new client connects
    
    print("{} connected".format(sid))
    sid_list.append(sid)
    sio.emit("my_response", {"data": "Connected", "count": 0}, room=sid)


@sio.event
def exit_chat(sid, message):
    # Gets triggered when client exits chat
    
    sio.leave_room(sid, message["room"])
    sid_list.remove(sid)



@sio.event
def message_handler(sid, message):
    sender = sid_name_mapping[sid]

    if message["message"] == 'End Session':
        # Ends session between two client
        
        print('inside end session')
        receiver = message_sessions[sender]
        message_sessions.pop(sender)
        message_sessions.pop(receiver)
        message["message"] = 'Session Ended'

    elif sid_name_mapping[sid] not in message_sessions.keys():
        # New session starts
        
        idx = get_rr_number(sid)
        receiver = sid_name_mapping[sid_list[idx]]        
        message_sessions[sender] = receiver
        message_sessions[receiver] = sender
        
    else:
        # Previous session continues
        
        receiver = message_sessions[sender]
    
    message_payload = {
        "sid": sid,
        "message": message["message"],
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
    # Gets triggered when a client disconnects
    
    sid_list.remove(sid)
    client_name = sid_name_mapping[sid]
    name_channel_map.pop(client_name)
    sid_name_mapping.pop(client_name)
    sid_name_mapping.pop(sid)
    round_robin_for_sid.pop(sid)
    print("{} disconnected".format(client_name))

def get_rr_number(sid):
    # Returns the next receiver SID using Round Robin
    
    end = len(sid_list)
    start = (round_robin_for_sid[sid]["sid"] + 1) % end

    for idx in range(start, end):
        if sid_list[idx] != sid:
            round_robin_for_sid[sid]["sid"] = idx
            return idx


if __name__ == "__main__":
    eventlet.wsgi.server(eventlet.listen(("", 5000)), app)
