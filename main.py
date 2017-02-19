try:
    import usocket as socket
except:
    import socket
import ussl as ssl


CONTENT = b"""\
HTTP/1.0 200 OK

Hello #%d from MicroPython!
"""

# base on https://github.com/micropython/micropython/blob/master/examples/network/http_server_ssl.py
def start_local_server(use_stream=True):
    s = socket.socket()

    # Binding to all interfaces - server will be accessible to other hosts!
    ai = socket.getaddrinfo("0.0.0.0", 8443)
    print("Bind address info:", ai)
    addr = ai[0][-1]

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print("Listening, connect your browser to https://<this_host>:8443/")

    counter = 0
    while True:
        res = s.accept()
        client_s = res[0]
        client_addr = res[1]
        print("Client address:", client_addr)
        print("Client socket:", client_s)
        client_s = ssl.wrap_socket(client_s, server_side=True)
        print(client_s)
        print("Request:")
        if use_stream:
            # Both CPython and MicroPython SSLSocket objects support read() and
            # write() methods.
            # Browsers are prone to terminate SSL connection abruptly if they
            # see unknown certificate, etc. We must continue in such case -
            # next request they issue will likely be more well-behaving and
            # will succeed.
            try:
                req = client_s.readline()
                print(req)
                while True:
                    h = client_s.readline()
                    if h == b"" or h == b"\r\n":
                        break
                    print(h)
                if req:
                    client_s.write(CONTENT % counter)
            except Exception as e:
                print("Exception serving request:", e)
        else:
            print(client_s.recv(4096))
            client_s.send(CONTENT % counter)
        client_s.close()
        counter += 1
        print()

def start_access_point():
    import network
    ap = network.WLAN(network.AP_IF)
    ap.config(essid='yellow-duck', password='helloduck', authmode=network.AUTH_WPA2_PSK)
    ap.active(True)

def connect_to_wifi():
    print('not implemented yet')
    return False

if connect_to_wifi():
    print('connected to wifi, do something')
else:
    # if we couldn't connect to wifi, then start an access point and a web-server
    # to get a correct SSID and password
    start_access_point()
    start_local_server()
