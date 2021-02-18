# NeoApi Baumer python wrapper is in:
# /home/pi/.local/lib/python3.7/site-packages/neoapi.py

# Python imports
import neoapi
import cv2
import time
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
        self.set_exposure(10000)
        self.setAutoExposure()
        self.startCaptureLoop()

    def set_exposure(self, value):
        self.camera.f.ExposureTime.Set(value)
    
    def setAutoExposure(self):
        ob = self.camera.f.ExposureMode.Get()
        self.camera.f.ExposureMode.Set(1)

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
            



