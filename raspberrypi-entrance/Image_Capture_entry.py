import time, sys, datetime, os, shutil
import pycurl
import threading
import json
import paho.mqtt.client as mqtt
import ALPR2
import cv2
import pytesseract as tess
import re
distance = 0;

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed
    # client.subscribe("$SYS/#")

    client.subscribe("smart_park/entry_dist")
    
def on_message(client, userdata, msg):
    #print(msg.topic+" "+str(msg.payload.decode("utf-8")))
    global distance
    distance = float(msg.payload.decode("utf-8"))
    print(distance)
def subscription():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("test.mosquitto.org", 1883, 60)
    client.loop_forever()
    
def image_getter( name, camera, rootpath='' ):
    broker_address="test.mosquitto.org"

    client = mqtt.Client()
    print('Starting getter for %s' % name)

    c = pycurl.Curl()
    c.setopt( c.URL, camera['url'] )

    if 'username' in camera and 'password' in camera:
        c.setopt(pycurl.USERPWD, "%s:%s" % (camera['username'], camera['password']))

    while running:
        global distance
        
        if(distance < 10):
            now = datetime.datetime.now()
            dst = 's' if now.timetuple().tm_isdst else '' # handle dst

            path = '/home/pi/repo/smart_park/raspberrypi-entrance/Temp_entry'

            imgfilename = '%s/Parking_%s_%s' % \
                ( path, now.strftime('%H:%M:%S'), camera['filetype'] )
                
            if not os.path.isdir( path ):
                os.makedirs( path )

            try:
                f = open( imgfilename, 'wb' )
                c.setopt( c.WRITEDATA, f )
                c.perform()
                f.close()
                
            except Exception as e:
                print(e)
            image = cv2.imread(imgfilename)
            start_time = time.time()
            if image.size != 0:
                plate_number, crp = ALPR2.processImage(image)
                plate_number = re.sub("[|().,;:]",'',plate_number)
                plate_number = plate_number.rstrip()
                if len(plate_number)>2:
                    if plate_number[0] == "[" or plate_number[0] == "]" or plate_number[0] == " ":
                        i = 0
                        while plate_number[i+1] != '':
                            plate_number[i] = plate_number[i+1]
                            
            else:
                plate_number = "Err, no img"
            print("--- %s seconds ---" % (time.time() - start_time))
            
            client.connect(broker_address, 1883, 60)
            client.loop_start()    #start the loop
            client.publish("smart_park/entry_plate",plate_number[2:], retain=False)
            client.disconnect()
            client.loop_stop()
            
            client.connect(broker_address, 1883, 60)
            client.loop_start()    #start the loop
            client.publish("smart_park/entry_plate",plate_number, retain=False)
            client.disconnect()
            client.loop_stop()
            crp_path = path + '/Crop'
            imgfilename_crp = '%s/Parking_%s_%s' % \
                ( crp_path, now.strftime('%H_%M_%S'), camera['filetype'] )
            imgfilename_crp = imgfilename_crp +".jpg"
            cv2.imwrite(imgfilename_crp, crp)
#             os.remove(imgfilename)
            print(plate_number)
            print(plate_number[1:])
            # sleep until time for next capture
            if 'every' in camera:
                delta = datetime.datetime.now() - now
                time.sleep( max(0.05,camera['every'] - delta.total_seconds()) )
                
    c.close()

def cleaner( name, camera, rootpath='' ):
    print('Starting cleaner for %s' % name )
    fullpath = '%s%s' % (rootpath,name)

    lastrun = datetime.datetime.now()

    while running:
        now = datetime.datetime.now()
        delta = now - lastrun

        if delta.total_seconds() >= 3600: #every hour
            if os.path.isdir(fullpath):
                for day in os.listdir( fullpath ):
                    try:
                        dirdate = datetime.datetime.strptime( day, '%Y%m%d%H' )
                        delta = now - dirdate
                        if delta.days > camera['keep']:
                            shutil.rmtree( '%s/%s' % (fullpath,day) )
                    except ValueError: # catch folders that aren't in date format
                        pass
        else:
            time.sleep(10)

    
def main():
    try:
        f = open( 'camera_entry.conf', 'r' )
        cameras = json.load(f)
        f.close()
    except FileNotFoundError as e:
        print(e)
        return 1

    if 'rootpath' not in cameras:
        cameras['rootpath'] = ''

    global running 
    running= True
    threads = []

    for name, camera in [ (i, j) for i, j in cameras.items() if type(j) is dict ]:
        if 'keep' not in camera:
            camera['keep'] = 31

        if 'filetype' not in camera:
            camera['filetype'] = 'jpg'

        t = threading.Thread( target=cleaner, args=(name, camera, cameras['rootpath']) )
        threads.append(t)
        t.start()

        t = threading.Thread( target=image_getter, args=(name, camera, cameras['rootpath']) )
        threads.append(t)
        t.start()

    t = threading.Thread( target=subscription )
    threads.append(t)
    t.start()
        #running = False

    for t in threads:
        print('OK')
        t.join()

if __name__ == '__main__':
    sys.exit(main())