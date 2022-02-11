import socket
import threading

import redis

r = redis.Redis()

# Connection Data
host = "127.0.0.1"
port = 55555

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# Lists For Clients and Their Nicknames
clients = []
nicknames = []
client_nickname_mapping = {}

# def broadcast(message):
#     for client in clients:
#         client.send(message)


def broadcast(message):
    for nickname in nicknames:
        r.set(nickname, message)


def send(message):
    print("Sending")
    # nickname, message = message.split(":")
    client = client_nickname_mapping["amin"]
    client.send(message)


def handle(client):
    while True:
        try:
            # Broadcasting Messages
            message = client.recv(1024)
            # print("{} sent a message".format(client_nickname_mapping[client]))
            # if len(message) == 2:
            #     send(message[0],message[1])
            # else:
            #     broadcast(message)
            broadcast(message)
        except:
            # Removing And Closing Clients
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast("{} left!".format(nickname).encode("ascii"))
            nicknames.remove(nickname)
            break


def receive():
    while True:
        # Accept Connection
        try:
            client, address = server.accept()
            print("Connected with {}".format(str(address)))
        except:
            server.close()
            for client in clients:
                clients.remove(client)
                client.close()

        # Request And Store Nickname
        client.send("NICK".encode("ascii"))
        nickname = client.recv(1024).decode("ascii")
        nicknames.append(nickname)
        clients.append(client)

        # Print And Broadcast Nickname
        print("Nickname is {}".format(nickname))
        broadcast("{} joined!".format(nickname).encode("ascii"))
        client.send("Connected to server!".encode("ascii"))
        client_nickname_mapping[client] = nickname
        # Start Handling Thread For Client
        thread = threading.Thread(target=handle, args=(client,))
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    receive()
