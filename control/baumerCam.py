# Python imports
import neoapi
import cv2
import numpy as np
from threading import Thread
from collections import deque

class baumerCam():
    camera = None
    stop = False
    deque = None

    def __init__(self, deque_size=50 ):
        #object to que the frames
        self.deque = deque(maxlen=deque_size)

        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True


    def initCam(self):
        self.camera = neoapi.Cam()
        self.camera.Connect()
        self.set_exposure(10000)
        # self.setAutoExposure()
        self.startCaptureLoop()

    def set_exposure(self, value):
        self.camera.f.ExposureTime.Set(value)
    
    def setAutoExposure(self):
        ob = self.camera.f.ExposureMode.Get()
        print (ob)
        print (type(ob))
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

    # Main camera capture thread
    def get_frame(self):
        while (True):
            if self.stop == False:
                img = self.camera.GetImage().GetNPArray()
                if np.sum(img) == 0:
                    print ("empty")
                    continue
                # title = 'Press [ESC] to exit ..'
                # cv2.namedWindow(title, cv2.WINDOW_NORMAL)
                
                img = cv2.resize(img, (800,600))
                cv2.imshow('debugo', img)
                cv2.waitKey(1)                 

                self.deque.append(img)
        



