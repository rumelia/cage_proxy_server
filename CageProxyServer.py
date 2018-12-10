# File: CageProxyServer.py
# Proxy server takes requests from client (browser) and forwards them
# to destination server. Gets data back from destination server
# and forwards them to the client (browser).
# Written by: Maisha Rumelia Rahman
# For: CS 330 Computer Networking Final Project

import socket
import _thread
from bs4 import BeautifulSoup

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
    print("Request received from BROWSER", addr, ":", request)  # print the request

    if get_request_verb(request) != b'GET' and get_request_verb(request) != b'POST':
        print("Cannot make this request")
    else:
        # get the destination server and port number from the request (port # is 80 if not specified)
        (server, port) = get_host_port(request)
        print("Connect to SERVER:", server.decode('utf-8'), "PORT:", port)

        # create new socket using 'with' so that we don't have to call s.close()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as new_s:
            # connect new socket to server and specified port number
            new_s.connect((server, port))

            # if there is an encoding specified, modify the request and then forward it
            if request.find(b'Accept-Encoding: ') != -1:
                request = change_encoding_type(request)

            # forward client request to server
            print("Request being forwarded to server:  ", request)
            new_s.sendall(request)

            # receive data from the server
            response = recv_all(new_s)
            print("Response data received from server: ", response)

            # send response data to client/browser
            print("Forwarding response data to browser...")
            conn.sendall(response)


def get_request_verb(request):
    request_verb = request.split(b' ')[0]
    return request_verb


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


def change_encoding_type(request):
    # get everything after Content-Encoding:
    encoding = (request.split(b'Accept-Encoding: ')[1]).split(b'\r')[0]
    return request.replace(encoding, b'identity')


def get_content_length(response):
    content_length = (response.split(b'Content-Length: ')[1]).split(b'\r')[0]
    return content_length


def recv_all(input_socket):
    total_data = b''
    buffer = b''

    # receive about 1096 bytes
    buffer += input_socket.recv(1096)
    print("Data with headers: ", buffer)

    # get the headers from the buffer
    headers = buffer.split(b'\r\n\r\n', 1)[0]

    # take everything after first \r\n\r\n
    buffer = buffer.split(b'\r\n\r\n', 1)[1]

    if headers.find(b'Transfer-Encoding: chunked') != -1:
        print("Deal with it the chunked-encoding way!")

        chunk_no = 0
        while True:
            print("This is chunk no: {} \n".format(chunk_no))

            # get the chunk_size
            chunk_size_str = buffer.split(b'\r\n', 1)[0]
            chunk_size = int(chunk_size_str, 16)
            print("Chunk size: ", chunk_size)

            if chunk_size == 0:
                break
            else:
                # consume the chunk size and CRLF chars
                buffer = buffer.split(b'\r\n', 1)[1]

                chunk_data = b''
                # read until the specified chunk size
                for i in range(chunk_size):
                    # add data to chunk from buffer char by char
                    chunk_data += buffer[0:1]
                    print(chunk_data)
                    # consume each char from buffer after adding it to chunk_data
                    buffer = buffer[1:]

                    # recv a new small amount of data into buffer just in case its needed
                    buffer += input_socket.recv(100)

                print("Size of received chunk: {}".format(len(chunk_data)))
                print("Data received in this chunk :", chunk_data)

                # add chunk_data to total data
                total_data += chunk_data
                chunk_no = chunk_no + 1

    # search the buffer for header dealing with size
    # if Content-Length header is found, deal with it in a certain way.
    elif headers.find(b'Content-Length: ') != -1:
        # parse the content-length
        specified_length = int(get_content_length(headers))
        print('Specified content Length: ', specified_length)

        # while the length of the total data is not the specified length
        while len(total_data) < specified_length:
            # append all data from buffer to total data
            total_data += buffer
            print("Received {} bytes".format(len(total_data)))

            # clear buffer
            buffer = b''

            # add some new stuff to the buffer according to specified content length
            buffer += input_socket.recv(specified_length - len(total_data))

    # stitch the total_data back onto the headers with \r\n\r\r
    final_data =  headers + b'\r\n\r\n' + total_data

    return final_data



if __name__ == "__main__":
    main()
