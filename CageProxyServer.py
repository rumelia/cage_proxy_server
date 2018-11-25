# File: CageProxyServer.py
# "Proxy server" that simply prints out the requests
# from a web browser. (Will be developed into an
# actual proxy server later).
# Written by: Maisha Rumelia Rahman
# For: CS 330 Computer Networking Final Project

import socket
import _thread


# function to get requests from client and print them out
def cage_proxy_thread(i_conn, i_addr):
    # get the request from the client
    request = i_conn.recv(4096) # set receive buffer size to 4096 bytes
    print("Request received from", i_addr, ":", request) # print the request


# Socket programming code referenced from: https://realpython.com/python-sockets/
HOST = "127.0.0.1" # default localhost/loopback interface address
PORT = 12345 # Port that this server will listen on
BACKLOG = 45 # No. of pending connections that can be in our server queue at any time

# create socket using 'with' so that we don't have to call s.close()
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # bind socket to specified host and port
    s.bind((HOST, PORT))

    # make socket listen
    s.listen(BACKLOG)
    print("Listening on port", PORT, "...")

    # get connections from client and handle multiple requests using threading
    while True:
        conn, addr = s.accept()
        _thread.start_new_thread(cage_proxy_thread, (conn, addr))
