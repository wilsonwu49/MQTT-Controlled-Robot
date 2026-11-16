import network
import time
import json
import machine
from machine import Pin
import neopixel
from Motor import Motor
from umqtt.simple import MQTTClient
import ssl
import secrets


# Wi-Fi credentials
SSID = secrets.SSID
PASSWORD = secrets.PWD

# MQTT settings
MQTT_BROKER = secrets.mqtt_url 
MQTT_PORT = secrets.port
#MQTT_USERNAME = secrets.mqtt_username 
#MQTT_PASSWORD = secrets.mqtt_password 
CLIENT_ID = "Wilany"
TOPIC_SUB_SPD = b"ME35/speed"
TOPIC_SUB_DIR = b"ME35/direction"
TOPIC_SUB_L0 = b"ME35/led/0"
TOPIC_SUB_L1 = b"ME35/led/1"

# listener setup
state = {"speed": 20, "direction": "stop"}
LEDS = [(0,0,0),(0,0,0)]

L_FWD = 1
R_FWD = 0

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.disconnect()
        wlan.connect(SSID, PASSWORD)
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
        
    if wlan.isconnected():
        print("WiFi Connected! IP:", wlan.ifconfig()[0])
        return True
    else:
        print("WiFi connection failed!")
        return False
    
def sub_cb(topic, msg):
    print("Received", topic, msg)
    try:
        if topic == TOPIC_SUB_SPD:
            state["speed"] = max(0, min(100, int(msg.decode())))
        if topic == TOPIC_SUB_DIR:
            state["direction"] = msg.decode()
        if topic == TOPIC_SUB_L0:
            d = json.loads(msg)
            LEDS[0] = [max(0, min(255, int(d[k]))) for k in "rgb"]
        if topic == TOPIC_SUB_L1:
            d = json.loads(msg)
            LEDS[1] = [max(0, min(255, int(d[k]))) for k in "rgb"]
        
        drive(state["speed"], state["direction"])
        write_leds()
        
    except Exception as e:
        print("bad message:", e)

def mqtt_connect():
    try:
        client = MQTTClient(
            client_id=CLIENT_ID,
            server=MQTT_BROKER,
            port=MQTT_PORT,
            #user=MQTT_USERNAME,
            #password=MQTT_PASSWORD,
            #ssl=True,  # Enable SSL
            ssl_params={'server_hostname': MQTT_BROKER}  # Important for certificate validation
        )
        client.set_callback(sub_cb)
        client.connect()
        client.subscribe(TOPIC_SUB_SPD)
        client.subscribe(TOPIC_SUB_DIR)
        client.subscribe(TOPIC_SUB_L0)
        client.subscribe(TOPIC_SUB_L1)
        print("MQTT Connected successfully!")
        return client
    except OSError as e:
        print(f"MQTT Connection failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def set_wheel(m, fwd, speed):
    if speed == 0:
        m.stop()
    elif speed > 0:
        m.start(fwd, speed)
    else:
        m.start(1 - fwd, -speed)
        
def drive(speed, direction):
    l = r = 0
    if direction == "forward":
        l = r = speed
    if direction == "backward":
        l = r = -speed
    if direction == "left":
        l = -speed
        r = speed
    if direction == "right":
        l = speed
        r = -speed
    if direction == "stop":
        l = r = 0
    
    print("left:",l,"right:",r)
    set_wheel(left, L_FWD, l)
    set_wheel(right, R_FWD, r)
        
def write_leds():
    lights[0] = LEDS[0]
    lights[1] = LEDS[1]
    lights.write()

# color sensor setup
left = Motor(12, 13, 39, 39)
right = Motor(14, 27, 39, 39)

# light color setup
lights = neopixel.NeoPixel(Pin(15), 2)
LEDS[0] = LEDS[1] = (20, 20, 0)
write_leds()

if connect_wifi():
    print("Connected")
    LEDS[0] = LEDS[1] = (0, 20, 20)
    write_leds()
    client = mqtt_connect()
    if client:
        LEDS[0] = LEDS[1] = (0, 0, 0)
        write_leds()
        try: 
            while True:
                client.check_msg()
                time.sleep_ms(20)
        except OSError as e:
            print("Lost connection:", e)
            
drive(0,"stop")
lights[0] = lights[1] = (60, 0, 0)
lights.write()
time.sleep_ms(500)
lights[0] = lights[1] = (0, 0, 0)
lights.write()
time.sleep_ms(500)
lights[0] = lights[1] = (60, 0, 0)
lights.write()
time.sleep_ms(500)
lights[0] = lights[1] = (0, 0, 0)
lights.write()