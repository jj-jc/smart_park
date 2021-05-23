import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt

broker_address="test.mosquitto.org"

client = mqtt.Client()

TRIG=21
ECHO=20
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)
GPIO.output(TRIG,False)
time.sleep(0.2)
try:
    while True:
        client.connect(broker_address, 1883, 60)
        client.loop_start()
        
        GPIO.output(TRIG,True)
        time.sleep(0.00001)
        GPIO.output(TRIG,False)
        pulse_security = time.time() #para evitar que se quede en los bucles while pillado
        while GPIO.input(ECHO)==0:
            pulse_start=time.time()
            if(pulse_start-pulse_security > 5):
                break
        while GPIO.input(ECHO)==1:
            pulse_end=time.time()
            if(pulse_end-pulse_security > 5):
                break
        pulse_duration=pulse_end-pulse_start
        distance=pulse_duration*17150
        distance=round(distance,2)
        #print(distance)
        client.publish("smart_park/entry_dist",distance)
        client.disconnect()
        client.loop_stop()
        time.sleep(1)
finally:
    print("Finish")
    GPIO.cleanup()
