# File: CageProxyServer.py
# Proxy server takes requests from client (browser) and forwards them
# to destination server. Gets data back from destination server
# and forwards them to the client (browser).
# Written by: Maisha Rumelia Rahman
# For: CS 330 Computer Networking Final Project

import socket
import _thread

MAX_RECV_SIZE = 8192  # global variable for maximum number of bytes that can be received (passed as argument to recv() function)


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

    if get_request_verb(request) != b'GET' and get_request_verb(request) != b'POST':
        print("Cannot make this request")
    else:
        # get the destination server and port number from the request (port # is 80 if not specified)
        (server, port) = get_host_port(request)
        print("Connect to HOST:", server.decode('utf-8'), "PORT:", port)

        # create new socket using 'with' so that we don't have to call s.close()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as new_s:
            # connect new socket to server and specified port number
            new_s.connect((server, port))

            # if there is an encoding specified, modify the request and then forward it
            if request.find(b'Accept-Encoding: ') != -1:
                request = change_encoding_type(request)

            # forward request to server
            print("Request being forwarded to server:  ", request)
            new_s.sendall(request)

            print("Receiving data from", server.decode('utf-8'))
            total_data_received = recvall(new_s)
            print("Total data received: ", total_data_received)

            print("Sending received data to browser...")
            conn.sendall(total_data_received)


def recvall(the_socket):
    # variables to handle receive
    content_length = -1
    content = b''
    first_time = True

    # loop until you receive all the data and append it all to content
    while True:
        # if it is the very first recv call then separate
        # the content from the header (if there is any content)
        if first_time:
            first_time = False
            # get some new data using recv
            new_data = the_socket.recv(1000)
            print("New data: ", new_data)

            # if you find the Content Length header then
            # parse out the content length
            # else set content_length to -1
            if new_data.find(b'Content-Length: ') != -1:
                content_length = get_content_length(new_data)
                print("Content Length: ", content_length)

            # if there is some content, then separate it from headers
            if len(new_data.split(b'\r\n\r\n')[1]) > 0:
                first_part = new_data.split(b'\r\n\r\n', 1)[1]
                new_data = first_part
        # if it is not the first time, recv in smaller chunks
        # so the the recv function does not wait a long time
        # to return
        else:
            new_data = the_socket.recv(250)
            print("New data: ", new_data)

        # add new data to content
        content += new_data

        # handle packets with Content Length header
        # if the length of the total data received is greater than the
        # content length specified and we are sure that the packer did
        # have a content length header, then break
        if int(content_length) <= len(content) and content_length != -1:
            break

        # handle chunked encoded packets
        # if we reach the end sentinel substring for
        # chunked encoding \r\n0\r\n then break
        # DOES NOT WORK
        if content.find(b'\r\n0\r\n') != -1:
            break
    print("Inside the function, the total received: ", content)
    return content

def get_request_verb(request):
    request_verb = request.split(b' ')[0]
    return request_verb


def get_host_port(i_request):
    """ Function get_host_port()
        Takes in request made by browser (client), extracts the destination host
        name and port number from it and returns the two as a tuple.
        :param i_request: request made by browser (client). Type: bytes literal
        :return: (hostname, port) tuple
    """
    # parse host from request
    # try to extract everything after the word 'Host: '
    host_with_port = (i_request.split(b'Host: ')[1]).split(b'\r')[0]

    # if there is no port number specified, set port as 80
    # else, separate out the hostname and port number
    if host_with_port.find(b':') == -1:
        hostname = host_with_port
        port = 80
    else:
        hostname = host_with_port.split(b':')[0]
        port = int(host_with_port.split(b':')[1])

    # return (HOST, PORT) tuple
    return hostname, port


def change_encoding_type(request):
    # get everything after Content-Encoding:
    encoding = (request.split(b'Accept-Encoding: ')[1]).split(b'\r')[0]
    return request.replace(encoding, b'identity')


def get_content_length(response):
    content_length = (response.split(b'Content-Length: ')[1]).split(b'\r')[0]
    return content_length


if __name__ == "__main__":
    main()
