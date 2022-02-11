import socket
import threading

import redis

r = redis.Redis()

# Choosing Nickname
nickname = input("Choose your nickname: ")

# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 55555))


def receive():
    while True:
        try:
            # Receive Message From Server
            # If 'NICK' Send Nickname
            message = client.recv(1024).decode("ascii")
            # if len(message) <= 0:
            #     client.close()
            #     break
            if message == "NICK":
                client.send(nickname.encode("ascii"))
            # else:
            if r.get(nickname):
                print(r.get(nickname))
        except:
            # Close Connection When Error
            print("An error occured!")
            client.close()
            break


def write():
    while True:
        try:
            message = "{}: {}".format(nickname, input(""))
            client.send(message.encode("ascii"))
        except:
            # Close Connection When Error
            print("An error occured!")
            client.close()
            break


# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target=receive)
# receive_thread.daemon = True
receive_thread.start()

write_thread = threading.Thread(target=write)
# write_thread.daemon = True
write_thread.start()
