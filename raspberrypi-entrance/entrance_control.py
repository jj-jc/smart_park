
import RPi.GPIO as GPIO # Import the GPIO library
import paho.mqtt.client as mqtt
import I2C_LCD_driver # Import the LCD library
import time 

current_time = 0
entry_time = 0
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    
    print("Connected with mqtt "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("smart_park/permission_entry")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # Read from the topic the recognized license plate
    permission = str(msg.payload.decode("utf-8"))
    global current_time
    global entry_time
    current_time = time.time()
    if current_time-entry_time > 10:
        if permission == "True":
            # Let the car to enter
            
            entry_time = time.time()
            access_granted()
            servo_control()
            welcome()
            
        else:
            # Dont let the car to enter
            access_denied()
            time.sleep(2)
            welcome()

# This function controls the servo
def servo_control():
    #Setup servoPin as PWM output of frequency 100Hz
    servoPin=12
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(servoPin,GPIO.OUT)
    pwm = GPIO.PWM(servoPin,100)
    
    # Setup servo parameters
    depart = 0
    arrive = 120
    DELAY = 0.1
    incStep = 10
    pos = depart
    
    # Raise the barrier
    pwm.start(AngleToDuty(pos))
    for pos in range(depart,arrive,incStep):
        duty=AngleToDuty(pos)
        pwm.ChangeDutyCycle(duty)
        time.sleep(DELAY)
        
    # Wait and lower the barrier
    time.sleep(5)
    for pos in range(arrive,depart,-incStep):
        duty=AngleToDuty(pos)
        pwm.ChangeDutyCycle(duty)
        time.sleep(DELAY)
    pwm.stop() # stop sending value to output

# This function compute the angle for the servo
def AngleToDuty(ang):
  return float(ang)/10.+5.

# LCD display and LEDs control functions
def leds_control(red, green):
    GPIO.output(RED_LED, red) 
    GPIO.output(GREEN_LED, green)

def welcome():
    mylcd.lcd_clear()
    mylcd.lcd_display_string("   Welcome to", 1)
    mylcd.lcd_display_string("    SS-Park ", 2)
    leds_control(True, False)

def access_granted():
    print("Access granted")
    # Show "Access granted" in LCD
    mylcd.lcd_clear()
    mylcd.lcd_display_string("Access granted!", 1)
    mylcd.lcd_display_String("LP: 2364APT", 2)
    # Turn on green led and turn off red led
    leds_control(False, True)

def access_denied():
    print("Access denied")
    # Show "Access denied!" if permission is not True
    mylcd.lcd_clear()
    mylcd.lcd_display_string("Access denied!", 1)
    mylcd.lcd_display_string("Unknown LP!", 2)
    # Turn on red led and turn off green led
    leds_control(True, False)

# Main programme

# Configure red led
RED_LED = 16
GPIO.setmode(GPIO.BCM) # GPIO numbering
GPIO.setup(RED_LED, GPIO.OUT) # Setup pin BCM 27 as output

# Configure green led
GREEN_LED = 19
GPIO.setmode(GPIO.BCM) # GPIO numbering
GPIO.setup(GREEN_LED, GPIO.OUT) # Setup pin BCM 18 as output

# Initialize the LCD display
mylcd = I2C_LCD_driver.lcd()
welcome()

# Create the mqtt client
client = mqtt.Client()
client.on_connect = on_connect # When client is connected it does what is specified in on_conncect function
client.on_message = on_message # When client recieves a message it does what is specified in on_message function
client.connect("test.mosquitto.org", 1883, 60)
client.loop_forever() # The client is constantly reading the messages from the topic
