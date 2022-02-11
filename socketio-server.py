import eventlet
import socketio

sio = socketio.Server()
app = socketio.WSGIApp(
    sio, static_files={"/": {"content_type": "text/html", "filename": "index.html"}}
)

sid_list = []
round_robin_for_sid = {}
from_to_mapping = {}


@sio.event
def join_chat(sid, message):
    print(message.get("name", sid) + " joined to {}".format(message["room"]))
    sio.enter_room(sid, message["room"])


@sio.event
def connect(sid, environ):
    sid_list.append(sid)
    round_robin_for_sid[sid] = {"sid": -1, "name": None}

    sio.emit("my_response", {"data": "Connected", "count": 0}, room=sid)


@sio.event
def exit_chat(sid, message):
    sio.leave_room(sid, message["room"])


@sio.event
def send_chat_room(sid, message):
    # round_robin_for_sid[sid]['name'] = message['name']

    # if message['status'] == 'sending':
    #     print('Inside sending - ',sid)
    #     idx = get_rr_number(sid)
    #     print(sid_list)
    #     from_to_mapping[sid_list[idx]] = sid
    #     sio.emit(
    #         'get_message',
    #         {
    #             'message': message['message'],
    #             'from': message['name'],
    #             'room':message['room'],
    #             'status': message['status']
    #         },
    #         room=sid_list[idx]
    #     )
    # elif message['status'] == 'replying':
    #     print('Inside replying - ',sid)
    #     print('from to ',sid,from_to_mapping[sid])
    #     sio.emit(
    #         'get_message',
    #         {
    #             'message': message['message'],
    #             'from': message['name'],
    #             'room': message['room'],
    #             'status': message['status']
    #         },
    #         room=from_to_mapping[sid]
    #     )
    # else:
    #     print('Inside default - ',sid)
    #     sio.emit(
    #         'get_message',
    #         {
    #             'message': message['message'],
    #             'from': message['name'],
    #             'room': message['room']
    #         },
    #         room=message['room']
    #     )
    message_payload = {"sid": sid, "body": message["message"], "from": message["name"]}


@sio.event
def disconnect(sid):
    print("Client disconnected")
    sid_list.remove(sid)


def get_rr_number(sid):
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
