
import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    
    print("Connected with mqtt "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("smart_park/entrance2")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # Read from the topic the recognized license plate
    license_plate = str(msg.payload.decode("utf-8"))
    print(license_plate)
    
    # Compare the recognized license plate with the database
    permission = False
    for i in range(len(license_plates)):
        if (license_plate == license_plates[i]):
            permission = True
            break
        else:
            permission = False
    print(permission)
    # Send the permission to the topic
    #client.publish("smart_park/permission_entrance", None)
    client.publish("smart_park/permission_entrance2", permission)
    
    # Open the file
    
    # Add the license plate of the car if permission is true
    if permission == True:
        cars_inside = open("cars_inside.txt", "w+")
        car_inside = license_plate + "\n"
        cars_inside.write(car_inside)
        cars_inside.close()

# Main programme

# Open database and read license plates
database = open("database.txt")
license_plates = database.readlines()
print(license_plates)
database.close()

# Eliminate the character '\n' in license plates
for i in range(len(license_plates)):
    if license_plates[i][len(license_plates[i])-1] == '\n':
        license_plates[i]=license_plates[i][:-1]

# Create the mqtt client
client = mqtt.Client()
client.on_connect = on_connect # When client is connected it does what is specified in on_conncect function
client.on_message = on_message # When client recieves a message it does what is specified in on_message function
client.connect("test.mosquitto.org", 1883, 60)
client.loop_forever() # The client is constantly reading the messages from the topic



