# File: CageProxyServer.py
# Proxy server takes requests from client (browser) and forwards them
# to destination server. Gets data back from destination server
# and forwards them to the client (browser).
# Written by: Maisha Rumelia Rahman
# For: CS 330 Computer Networking Final Project

import socket
import _thread

MAX_RECV_SIZE = 4096  # global variable for maximum number of bytes that can be received (passed as argument to recv() function)


def main():
    """ Function: main()
        Main executable.
        Creates a listening server socket that accepts connection requests from clients
        and passes them into the cage_proxy_thread() function which 'does the proxying'
        (refer to cage_proxy_thread() docstring for further detail)
    """
    # Socket programming code referenced from: https://realpython.com/python-sockets/
    HOST = "127.0.0.1"  # default localhost/loopback interface address
    PORT = 12345  # Port that this server will listen on
    BACKLOG = 45  # No. of pending connections that can be in our server queue at any time

    # create socket using 'with' so that we don't have to call s.close()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # bind socket to specified host and port
        s.bind((HOST, PORT))

        # make socket listen
        s.listen(BACKLOG)
        print("Listening on port", PORT, "...")

        # get connections from client and handle multiple requests using threading
        while True:
            client_conn, client_addr = s.accept()
            _thread.start_new_thread(cage_proxy_thread, (client_conn, client_addr))


def cage_proxy_thread(conn, addr):
    """ Function: cage_proxy_thread()
        Invoked on thread created in main(). Gets the request that a client is trying to send.
        Extracts the destination host/server and port number from the request using the get_host_port() function.
        Creates a 'client socket' to connect to the server and forwards the request to the server.
        Then gets response from the server and forwards it to the client using the original 'server socket' connection
        that was created in main()

        :param conn - connection between browser (client) and this proxy server
        :param addr - address of browser (client)
        :return None
    """
    # get the request from the client
    request = conn.recv(MAX_RECV_SIZE)  # set receive buffer size to 4096 bytes
    print("Request received from", addr, ":", request)  # print the request

    # get the destination server and port number from the request (port # is 80 if not specified)
    (server, port) = get_host_port(request)
    print("Connect to HOST:", server.decode('utf-8'), "PORT:", port)

    # create new socket using 'with' so that we don't have to call s.close()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as new_s:
        # connect new socket to server and specified port number
        new_s.connect((server, port))

        # forward client request to server
        new_s.sendall(request)

        # receive data from the server
        while True:
            response_data = new_s.recv(MAX_RECV_SIZE)
            print("Receiving data from", server.decode('utf-8'))

            # if there is some data, send it back to client. Otherwise, break
            if len(response_data) > 0:
                conn.sendall(response_data)
            else:
                print("Error in response data received")
                break


def get_host_port(i_request):
    """ Function get_host_port()
        Takes in request made by browser (client), extracts the destination host
        name and port number from it and returns the two as a tuple.
        
        :param i_request: request made by browser (client)
        :return: (hostname, port) tuple
    """
    # parse host from request
    # extract everything after the word 'Host: '
    host_with_extra = i_request.split(b'Host: ')[1]
    
    # extract everything before the first \r
    host_with_port = host_with_extra.split(b'\r')[0]

    # if there is no port number specified, set port as 80
    # else, separate out the hostname and port number
    if host_with_port.find(b':') == -1:
        hostname = host_with_port
        port = 80
    else:
        hostname = host_with_port.split(b':')[0]
        port = int(host_with_port.split(b':')[1])

    # return (hostname, port) tuple
    return hostname, port


if __name__ == "__main__":
    main()
