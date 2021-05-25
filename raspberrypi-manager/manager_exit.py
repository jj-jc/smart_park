import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    
    print("Connected with mqtt "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("smart_park/exit_plate")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # Read from the topic the recognized license plate
    license_plate = str(msg.payload.decode("utf-8"))
    print(license_plate)
    
    # First, read the file with the cars which are inside
    cars_inside = open("cars_inside.txt", "r")
    cars = cars_inside.readlines()
    cars_inside.close()
    
    # Rewrite the file removing the car which has left 
    cars_inside = open("cars_inside.txt", "w")
    permission = False
    for i in range(len(cars)):
        if cars[i][len(cars[i])-1] == '\n': # Eliminate the character '\n' in license plates
            cars[i]=cars[i][:-1] 
        if license_plate != cars[i]:
            permission = False
            cars_inside.write(cars[i])
        else:
            permission = True
    cars_inside.close()
    print(permission)
    # Send the permission to the topic
    if permission == False:
        print("There is no car inside of the parking with that license plate\n")
    else:
        print("The car can exit\n") # permission == True
    client.publish("smart_park/permission_exit", permission)

# Main programme

# Create the mqtt client
client = mqtt.Client()
client.on_connect = on_connect # When client is connected it does what is specified in on_conncect function
client.on_message = on_message # When client recieves a message it does what is specified in on_message function
client.connect("test.mosquitto.org", 1883, 60)
client.loop_forever() # The client is constantly reading the messages from the topic



