import json
import eventlet
import pika
import socketio

RABBITMQ_HOST = 'rabbitmq'

sio = socketio.Server()
app = socketio.WSGIApp(
    sio, static_files={"/": {"content_type": "text/html", "filename": "index.html"}}
)

sid_name_mapping, round_robin_for_sid, name_channel_map, message_sessions = {},{},{},{}
sid_list = []


def create_rabbitmq_connection(queue):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(RABBITMQ_HOST, heartbeat=600)
        )
        channel1 = connection.channel()
        channel1.queue_declare(queue=queue)
        return channel1
    
    except Exception as e:
        print(e)

def publish_to_queue(client_name, payload):
    try:
        receiver_channel = name_channel_map.get(client_name)
        receiver_channel.basic_publish(
            exchange="", 
            routing_key=client_name, 
            body=json.dumps(payload)
        )
    except Exception as e:
        print(e)


@sio.event
def join_chat(sid, message):
    # Emitted by client to join the chat
    
    print(message.get("name", sid) + " joined to {}".format(message["room"]))
    sio.enter_room(sid, message["room"])


@sio.event
def set_client_info(sid, data):
    # Emitted by client to set client information
    
    current_users = '\n'.join(name_channel_map.keys())
    
    try:
        sid_name_mapping[sid] = data["name"]
        sid_name_mapping[data["name"]] = sid
        name_channel_map[data['name']] = create_rabbitmq_connection(data['name'])
        round_robin_for_sid[sid] = {"sid": -1, "name": data["name"]}
        
        payload = {
            "users" : current_users
        }
        
        publish_to_queue(
            client_name=data['name'],
            payload=payload
        )
        
    except Exception as e:
        print(e)


@sio.event
def connect(sid, environ):
    # Get triggered when a new client connects
    
    print("{} connected".format(sid))
    sid_list.append(sid)


@sio.event
def exit_chat(sid, message):
    # Gets triggered when client exits chat
    
    sio.leave_room(sid, message["room"])
    sid_list.remove(sid)


@sio.event
def message_handler(sid, message):
    sender = sid_name_mapping.get(sid)

    if message["message"] == 'End Session':
        # Ends session between two client

        receiver = message_sessions.get(sender)
        message_sessions.pop(sender)
        message_sessions.pop(receiver)
        message["message"] = 'Session Ended'

    elif sender not in message_sessions.keys():
        # New session starts
        
        idx = get_rr_number(sid)
        receiver = sid_name_mapping.get(sid_list.get(idx))     
        message_sessions[sender] = receiver
        message_sessions[receiver] = sender
        
    else:
        # Previous session continues
        
        receiver = message_sessions.get(sender)
    
    message_payload = {
        "sid": sid,
        "message": message.get("message"),
        "sender": sender,
        "receiver": receiver,
        "room": message.get("room"),
    }

    publish_to_queue(client_name=receiver,payload=message_payload)


@sio.event
def disconnect(sid):
    # Gets triggered when a client disconnects
    
    try:
        sid_list.remove(sid)
        client_name = sid_name_mapping.get(sid)
        name_channel_map.pop(client_name)
        sid_name_mapping.pop(client_name)
        sid_name_mapping.pop(sid)
        round_robin_for_sid.pop(sid)
        print("{} disconnected".format(client_name))
        
    except Exception as e:
        print(e)


def get_rr_number(sid):
    # Returns the next receiver SID using Round Robin
    try:
        end = len(sid_list)
        start = (round_robin_for_sid[sid]["sid"] + 1) % end

        for idx in range(start, end):
            if sid_list[idx] != sid:
                round_robin_for_sid[sid]["sid"] = idx
                return idx
            
    except Exception as e:
        print(e)


if __name__ == "__main__":
    eventlet.wsgi.server(eventlet.listen(("", 5000)), app)
