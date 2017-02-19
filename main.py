try:
    import usocket as socket
except:
    import socket
import ussl as ssl


CONTENT = b"""\
HTTP/1.0 200 OK

<html>
 <head>
  <title>Yellow Duck configuration</title>
 </head>
 <body>
  <form method="post">
   Enter SSID and password:</br>
   SSID:&nbsp;<input name="ssid" type="text"/></br>
   Password:&nbsp;<input name="pass" type="password"/></br>
   <input type="submit" value="Submit">
  </form>
 </body>
</html>
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
    print("Listening, connect your browser to https://192.168.4.1:8443/")

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
                req = client_s.readline().decode('utf-8')
                print(req)
                length = 0
                while True:
                    h = client_s.readline()
                    if h == b"" or h == b"\r\n":
                        break
                    header = h.decode('utf-8').lower()
                    if header.startswith('content-length'):
                        length = int(header.split(':')[1])
                    print(header)
                if req.startswith('POST') and length > 0:
                    data = client_s.read(length).decode('utf-8')
                    print('Data ' + data)
                    if data:
                        params = data.split('&')
                        ssid = None
                        password = None
                        for param in params:
                            if param.startswith('ssid='):
                                ssid = param.split('=')[1]
                            if param.startswith('pass='):
                                password = param.split('=')[1]
                        if ssid and password:
                            write_wifi_config(ssid, password)
                            # reset the board to try new ssid/password
                            import machine
                            machine.reset()
                # print html form
                if req:
                    client_s.write(CONTENT)
            except Exception as e:
                print("Exception serving request:", e)
        else:
            print(client_s.recv(4096))
            client_s.send(CONTENT)
        client_s.close()

def write_wifi_config(ssid, password):
    f = open('wifi.conf', 'w')
    f.write(ssid + '/' + password)
    f.close()

def start_access_point():
    import network
    ap = network.WLAN(network.AP_IF)
    ap.config(essid='yellow-duck', password='helloduck', authmode=network.AUTH_WPA2_PSK)
    ap.active(True)

def connect_to_wifi():
    import os
    if not 'wifi.conf' in os.listdir():
        return False
    f = open('wifi.conf')
    data = f.read()
    f.close()
    print('wifi.conf data: ' + data)
    parts = data.split('/')
    ssid = parts[0]
    password = parts[1]
    if not ssid or not password:
        return False
    import network
    import time
    # enable station interface and connect to WiFi access point
    print('connect to wifi: %s' % ssid)
    nic = network.WLAN(network.STA_IF)
    nic.active(True)
    nic.connect(ssid, password)
    attempt = 0
    while attempt < 10 and not nic.isconnected():
        print('connecting ...')
        time.sleep(1.0)
        attempt = attempt + 1

    if nic.isconnected():
        print('connected')
        return True
    else:
        print('connection failed')
        return False

if connect_to_wifi():
    print('connected to wifi, do something')
else:
    # if we couldn't connect to wifi, then start an access point and a web-server
    # to get a correct SSID and password
    start_access_point()
    start_local_server()
