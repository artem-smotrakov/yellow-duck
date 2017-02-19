try:
    import usocket as socket
except:
    import socket
import ussl as ssl

CONFIG_MODE_WARNING = "Warning: don't forget to turn off config mode after specifying ssid/password"
NO_WARNING = ""

FORM = b"""\
HTTP/1.0 200 OK

<html>
 <head>
  <title>Yellow Duck configuration</title>
 </head>
 <body>
  <p>%s</p>
  <form method="post">
   Enter SSID and password:</br>
   SSID:&nbsp;<input name="ssid" type="text"/></br>
   Password:&nbsp;<input name="pass" type="password"/></br>
   <input type="submit" value="Submit">
  </form>
 </body>
</html>
"""

BYE = b"""\
HTTP/1.0 200 OK

<html>
 <head>
  <title>Yellow Duck configuration</title>
 </head>
 <body>
  <p>%s</p>
  <p>The board is going to reboot, and try to connect to specified network.</p>
 </body>
</html>
"""

CONFIG = 'wifi.conf'
SERVER_PORT=443
INDENT = '    '
ACCESS_POINT_SSID='yellow-duck'
ACCESS_POINT_PASSWORD='helloduck'
WIFI_LED_PIN=13
CONFIG_MODE_PIN=5

# returns html response with a form
def get_form_html():
    if is_config_mode():
        return FORM % CONFIG_MODE_WARNING
    else:
        return FORM % NO_WARNING

# returns html response with a bye message
def get_bye_html():
    if is_config_mode():
        return BYE % CONFIG_MODE_WARNING
    else:
        return BYE % NO_WARNING

# reboot the board with a delay
def reboot():
    import time
    import machine
    print('rebooting ...')
    time.sleep(5.0)
    machine.reset()

# start a web server which asks for wifi ssid/password,
# and stores it to a config file
# based on https://github.com/micropython/micropython/blob/master/examples/network/http_server_ssl.py
def start_local_server(use_stream = True):
    s = socket.socket()

    # binding to all interfaces - server will be accessible to other hosts!
    ai = socket.getaddrinfo('0.0.0.0', SERVER_PORT)
    print('bind address info: ', ai)
    addr = ai[0][-1]

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print('server started on https://192.168.4.1:%d/' % SERVER_PORT)

    # main serer loop
    while True:
        print('waiting for connection ...')
        res = s.accept()

        client_s = res[0]
        client_addr = res[1]

        print("client address: ", client_addr)
        client_s = ssl.wrap_socket(client_s, server_side=True)
        print(client_s)
        print("client request:")
        if use_stream:
            # both CPython and MicroPython SSLSocket objects support read() and
            # write() methods
            #
            # browsers are prone to terminate SSL connection abruptly if they
            # see unknown certificate, etc. We must continue in such case -
            # next request they issue will likely be more well-behaving and
            # will succeed
            try:
                req = client_s.readline().decode('utf-8').strip()
                print(INDENT + req)

                # content lenght
                length = 0

                # read headers, and look for Content-Length header
                while True:
                    h = client_s.readline()
                    if h == b"" or h == b"\r\n":
                        break
                    header = h.decode('utf-8').strip().lower()
                    if header.startswith('content-length'):
                        length = int(header.split(':')[1])
                    print(INDENT + header)

                # process data from the web form
                if req.startswith('POST') and length > 0:
                    data = client_s.read(length).decode('utf-8')
                    if data:
                        params = data.split('&')
                        ssid = None
                        password = None
                        for param in params:
                            if param.startswith('ssid='):
                                ssid = param.split('=')[1]
                            if param.startswith('pass='):
                                password = param.split('=')[1]

                        # if ssid/password received, store them to a file
                        # and reset the board to try new ssid/password
                        if ssid and password:
                            write_wifi_config(ssid, password)
                            client_s.write(get_bye_html())
                            client_s.close()
                            reboot()
                # print out html form
                if req:
                    client_s.write(get_form_html())
            except Exception as e:
                print("exception: ", e)
        else:
            print(client_s.recv(4096))
            client_s.send(get_form_html())
        # close the connection
        client_s.close()

# store ssid/password to a file
def write_wifi_config(ssid, password):
    f = open(CONFIG, 'w')
    f.write(ssid + '/' + password)
    f.close()

# start wifi access point
def start_access_point():
    import network
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ACCESS_POINT_SSID, password=ACCESS_POINT_PASSWORD, authmode=network.AUTH_WPA2_PSK)
    ap.active(True)

# read ssid/password from a file, and try to connect
# returns true in case of successful connection
def connect_to_wifi():
    # read ssid/password from a config file
    import os
    if not CONFIG in os.listdir():
        print('cannot find ' + CONFIG)
        return False
    f = open(CONFIG)
    data = f.read()
    f.close()
    parts = data.split('/')
    ssid = parts[0]
    password = parts[1]
    if not ssid or not password:
        return False
    # try to connect
    import network
    import time
    print('connect to network: %s' % ssid)
    nic = network.WLAN(network.STA_IF)
    nic.active(True)
    nic.connect(ssid, password)
    # wait some time
    attempt = 0
    while attempt < 11 and not nic.isconnected():
        print('connecting ...')
        time.sleep(1.0)
        attempt = attempt + 1

    if nic.isconnected():
        print('connected')
        return True
    else:
        print('connection failed')
        return False

# turns on an LED that indicates wifi connection
def turn_on_wifi_led():
    from machine import Pin
    pin = Pin(WIFI_LED_PIN, Pin.OUT)
    pin.high()

# turns off an LED that indicates wifi connection
def turn_off_wifi_led():
    from machine import Pin
    pin = Pin(WIFI_LED_PIN, Pin.OUT)
    pin.low()

# returns true if config mode enabled
def is_config_mode():
    from machine import Pin
    pin = Pin(CONFIG_MODE_PIN, Pin.IN)
    return True if pin.value() == 1 else False

# entry point
turn_off_wifi_led()

# check if we're in configuration mode
if is_config_mode():
    print('enabled configuration mode')
    start_access_point()
    start_local_server()
    reboot()

if connect_to_wifi():
    turn_on_wifi_led()
    import time
    import dht
    import machine
    d = dht.DHT22(machine.Pin(14))
    while True:
        d.measure()
        print('temperature = %.2f' % d.temperature())
        print('humidity = %.2f' % d.humidity())
        time.sleep(5.0)
else:
    # if we couldn't connect to wifi, then start an access point and a web server
    # to get a correct SSID and password
    start_access_point()
    start_local_server()
