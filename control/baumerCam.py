# NeoApi Baumer python wrapper is in:
# /home/pi/.local/lib/python3.7/site-packages/neoapi.py

# Python imports
import neoapi
import cv2
import time
import os
import numpy as np
from threading import Thread
from collections import deque

# NEOAPI Baumer camera class control
class baumerCam():
    camera = None
    stop = False
    deque = None
    imgType = 8
    guiResX = 800
    guiResY = 600

    def __init__(self, deque_size=50 ):
        #object to que the frames
        self.deque = deque(maxlen=deque_size)

        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True

    def initCam(self):
        self.camera = neoapi.Cam()
        self.camera.Connect()
        self.setAutoExposure(True)
        self.setAutoGain(True)
        # self.get_minmax_gain()
        self.camera.SetSynchronFeatureMode(True)
        self.startCaptureLoop()

    def setExposure(self, value):
        self.setAutoExposure(False)  #auto exposure needs to be disabled
        value = value * 1000 #convert from ms to microsec
        self.camera.f.ExposureTime.Set(value)

    def setGain(self, value):
        self.setAutoGain(False) #auto gain disabled for manual value
        self.camera.f.Gain.Set(value)

    def set_min_exposure(self):
        self.camera.f.ExposureTime.Set(self.camera.f.ExposureTime.GetMin())
    
    def set_max_exposure(self):  #this may never end DO NOT USE
        self.camera.f.ExposureTime.Set(self.camera.f.ExposureTime.GetMax())

    def get_exposure(self):
        return self.camera.f.ExposureTime.Get()

    def get_gain(self):
        return self.camera.f.Gain.Get()

    def get_minmax_gain(self):
        r = [ self.camera.f.GainAutoMinValue.Get(),  self.camera.f.GainAutoMaxValue.Get() ]
        return r 
    
    def setAutoExposure(self, value ):
        # 0 = Auto, 1 = Manual
        if value == True:
            self.camera.f.ExposureAuto.Set(0)  #Auto
        else:
            self.camera.f.ExposureAuto.Set(1)  #Manual

    def setAutoGain(self, value):
        if value == True:
            self.camera.f.GainAuto.Set(0)  #Auto
        else:
            self.camera.f.GainAuto.Set(1)  #Manual

    # Starts the capture daemon
    def startCaptureLoop(self):
        self.stop = False
        if self.get_frame_thread.isAlive() == False:
            self.get_frame_thread.start()

    # Stops the thread 
    def stopCaptureLoop(self):
        self.stop = True
        self.deque.clear()

    # Gets a single frame from the queue
    def get_video_frame(self):
        if len(self.deque) > 0 and self.stop == False:
            return self.deque[-1]
        else:
            return None

    #saves a single taken frame in a file FAKE method 
    #only takes a single frame from the video stream
    def takeSingleShoot(self, path, filename):
        fullpath = path + os.path.sep + filename
        print ("Taking frame...")
        buf = self.camera.GetImage(timeout=10000)
        while buf.GetSize() == 0:
            print ('ERROR: empty buffer')
            buf = self.camera.GetImage(timeout=10000)

        img = buf.GetNPArray()
        while np.sum(img) == 0:   # OPENCV DEBUG (check if it is not black)
            print ('ERROR: black image')
            buf = self.camera.GetImage(timeout=10000)
            img = buf.GetNPArray()

        cv2.imwrite(fullpath, img)
        print ("Saving frame as: " + str(fullpath))    

    #changes the resolution of the captured image
    def setGuiResolution(self, resX, resY):
        self.stopCaptureLoop() #Stops the capture loop
        time.sleep(2)  #wait for a second for the GUI to cosume the dequeue
        self.guiResX = resX
        self.guiResY = resY
        self.startCaptureLoop()

    # Main camera capture thread
    def get_frame(self):
        try:
            while (True):
                if self.stop == False:
                    buf = self.camera.GetImage(timeout=10000)  #buff class neoapi.neoapi.Image
                    if buf.GetSize() == 0:
                        continue

                    img = buf.GetNPArray() 
                    # if np.sum(img) == 0:   # OPENCV DEBUG
                    #     continue
                    show = cv2.resize(img,(self.guiResX,self.guiResY))
                    show = cv2.cvtColor(show,cv2.COLOR_GRAY2RGB)                  
                    # cv2.imshow('debugo', show)          #OPENCV DEBUG
                    # cv2.waitKey(1)                     #OPENCV DEBUG

                    self.deque.append(show)

        except (neoapi.NeoException, Exception) as exc:
            print('ERROR: ', exc.GetDescription())
            



