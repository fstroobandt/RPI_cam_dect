import os  # needed for pathing
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import RPi.GPIO as RPIO
import numpy as np
import paho.mqtt.client as mqtt

path = '/home/pi/Desktop/cascades/haarcascade_eye.xml'  # PATH OF THE CASCADE
objectName = 'EYE'  # OBJECT NAME TO DISPLAY
frameWidth = 640  # DISPLAY WIDTH
frameHeight = 480  # DISPLAY HEIGHT
colour = (255, 0, 255)

mqttUser="TOKEN"
mqttPW ="NULL"

font_colour = (255, 123, 40)
font_type = cv2.FONT_HERSHEY_SIMPLEX
font_size = 0.7
font_thickness = 2

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected success")
    else:
        print(f"Connected fail with code {rc}")

client = mqtt.Client("pi")
client.on_connect = on_connect
client.username_pw_set(mqttUser, password=mqttPW)
client.connect("localhost", 1883) #kan alleen als server lokaal gedraaid word!!
client.loop_start()

camera=PiCamera()
camera.resolution=(frameWidth,frameHeight)
camera.framerate=16

rawCapture=PiRGBArray(camera, size=camera.resolution)

def empty(a):
    pass

RPIO.setmode(RPIO.BCM)  # om met GPIOxx nummers te werken
RPIO.setwarnings(False)

LED = 26

RPIO.setup(LED, RPIO.OUT) #init LED
RPIO.output(LED, RPIO.HIGH) #test LED want helft is kapot
time.sleep(1)
RPIO.output(LED, RPIO.LOW)  #LED werkt

# CREATE TRACKBAR
cv2.namedWindow("Result")
cv2.resizeWindow("Result", frameWidth, frameHeight + 100)
cv2.createTrackbar("Scale", "Result", 400, 1000, empty)
cv2.createTrackbar("Neig", "Result", 8, 50, empty)
cv2.createTrackbar("Min Area", "Result", 0, 100000, empty)

# LOAD THE CLASSIFIERS DOWNLOADED
cascade = cv2.CascadeClassifier(path)

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    t0 = cv2.getTickCount()

    # GET CAMERA IMAGE AND CONVERT TO GRAYSCALE
    img = frame.array

    #DETECT THE OBJECT USING THE CASCADE
    scaleVal = 10 + (cv2.getTrackbarPos("Scale", "Result") / 1000)
    neig = cv2.getTrackbarPos("Neig", "Result")
    minArea = cv2.getTrackbarPos("Min Area", "Result")
    objects = cascade.detectMultiScale(img, scaleVal, neig)
    objcount = len(objects)
    # DISPLAY THE DETECTED OBJECTS
    for (x, y, w, h) in objects:
        area = w * h
        if area > minArea:
            cv2.rectangle(img, (x, y), (x + w, y + h), colour, 3)
            cv2.putText(img, objectName, (x, y - 5), font_type, 1, colour, 2)

    cv2.rectangle(img, (5, 10), (240, 80), colour, -1)
    cv2.putText(img, "Detected objects: " + str(objcount), (10, 60),
                font_type, font_size, font_colour,font_thickness)  #Detected object count display

    if objcount > 0: #als er objecten zijn, track het eerste object.
        RPIO.output(LED,RPIO.HIGH) #zet dit UIT bij een hoge Framerate anders epilepsie!!!
        # objects is een list van alle objecten, object 0 = eerst geziene object, dit is een list van meer data -> behandel als matrix
        x_obj_0 = objects[0][0]
        frame_center_x=frameWidth/2 # center van beel (x as)
        frame_x_margin=frameWidth/20 # 5% van beeldbreedte

        y_obj_0 = objects[0][1]
        frame_center_y=frameHeight/2 # center van beeld (y as)
        frame_y_margin=frameHeight/20 # 5% van beeldhoogte
        if x_obj_0 > round(frame_center_x+frame_x_margin): #centrum object +- 5% marge 
            client.publish("camera/move", payload="right",qos=0,retain=0)
        elif x_obj_0 < round(frame_center_x-frame_x_margin): #centrum object +- 5% marge
            client.publish("camera/move", payload="left",qos=0,retain=0)

        if y_obj_0 > round(frame_center_y+frame_y_margin): #centrum object +- 5% marge
            client.publish("camera/move", payload="down",qos=0,retain=0)
        elif y_obj_0 < round(frame_center_y-frame_y_margin): #centrum object +- 5% marge
            client.publish("camera/move", payload="up",qos=0,retain=0)
    else:
        RPIO.output(LED, RPIO.LOW)

    fps = cv2.getTickFrequency() / (cv2.getTickCount() - t0)  # float
    cv2.putText(img, "FPS:" + str(int(fps)), (10, 40), font_type, font_size, font_colour, font_thickness)  # FPS text
    cv2.imshow("Result", img)
    rawCapture.truncate(0) #om de frame te clearen voor een nieuw beeld
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        RPIO.cleanup()
        cv2.destroyAllWindows()
        client.loop_stop()
        client.disconnect()
        break