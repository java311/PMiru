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
from PIL import Image

# NEOAPI Baumer camera class control
class baumerCam():
    camera = None
    stop = False
    deque = None
    imgType = 8

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

    def get_image_resolution(self):
        r = [ self.camera.f.Height.Get(),  self.camera.f.Width.Get() ]
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
    def takeSingleShoot(self, path, filename, drops=3):
        # New "optimized" version
        fullpath = path + os.path.sep + filename
        print ("Taking frame...")

        # Drop several frames before taking the GOOD one
        for i in range(drops):
            buf = self.camera.GetImage(timeout=10000)
            while buf.GetSize() == 0:
                print ('ERROR: empty buffer')
                buf = self.camera.GetImage(timeout=10000)

        # this block takes the final GOOD frame 
        buf = self.camera.GetImage(timeout=10000)
        img = buf.GetNPArray()
        shape = self.get_image_resolution()
        while np.sum(img) == 0:   # OPENCV DEBUG (check if it is not black)
            print ('ERROR: black image')
            buf = self.camera.GetImage(timeout=10000)
            img = buf.GetNPArray()

        # Image byte format and reshape
        if self.imgType == 8:
            img = np.frombuffer(img, dtype=np.uint8)
        else:
            img = np.frombuffer(img, dtype=np.uint16)
        img = img.reshape(shape)

        # Save the tiff file
        mode = None
        if self.imgType == 16:
            mode = 'I;16'
        img = Image.fromarray(img, mode=mode)
        img.save(fullpath)
        print ("Saving frame as: " + str(fullpath))


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
                    # show = cv2.resize(img,(self.guiResX,self.guiResY)) original 
                    # show = cv2.cvtColor(show,cv2.COLOR_GRAY2RGB)       original   
                    # cv2.imshow('debugo', show)          #OPENCV DEBUG
                    # cv2.waitKey(1)                     #OPENCV DEBUG

                    self.deque.append(img)

        except (neoapi.NeoException, Exception) as exc:
            print('ERROR: ', exc.GetDescription())


    def getMedianRawShoot(self, drops, avgs):
        print ("Taking raw Median frame...")

        # Drop several frames before taking the GOOD one
        # for i in range(drops):
        #     self.camera.get_video_data(timeout=self.timeout)
        #     print ("Median Frame droped")
        # Drop several frames before taking the GOOD one
        for i in range(drops):
            buf = self.camera.GetImage(timeout=10000)
            print ("Median Frame droped")
            while buf.GetSize() == 0:
                print ('ERROR: black image')
                buf = self.camera.GetImage(timeout=10000)

        if avgs <= 0:
            return 0 

        # this is the GOOD one
        buf = self.camera.GetImage(timeout=10000)
        img = buf.GetNPArray()
        median = 0
        for i in range(avgs):
            while np.sum(img) == 0:   # OPENCV DEBUG (check if it is not black)
                print ('ERROR: black image')
                buf = self.camera.GetImage(timeout=10000)
                img = buf.GetNPArray()
            median = median + np.median(img)
            print ("median " + str(median))
        median = median / avgs

        return median


    # Baumer method to calibrate the settings for auto/gain exposure using LED lights 
    def autoExposureGainCalib(self, wait, drops, good_frames, min_median, max_median ):
        # Turn On Auto exposure and gain
        self.setAutoExposure(True)
        self.setAutoGain(True)


        print('Waiting for auto-exposure to compute correct settings ...')
        
        sleep_interval = wait  #0.100 original value
        df_last = 0
        gain_last = 0
        exposure_last = 0
        m_threshold = 5
        median_last = 0
        # min_median = 15
        # max_median = 200
        matches = 0
        while True:
            time.sleep(sleep_interval)
            # settings = self.camera.get_control_values()
            # df = self.camera.get_dropped_frames()
            self.getMedianRawShoot(drops,0)   #drop some frames before taking real values

            gain = self.get_gain()
            exposure = self.get_exposure()
            median = 0
            
            # Here was the drop frames IF
            median = self.getMedianRawShoot(0,1)
            print('   Gain {gain:f}  Exposure: {exposure:f} Median: {median:f} Dropped frames: {df:f}'
            .format(gain=gain,
                    exposure=exposure,
                    median=median,
                    df=df_last))
            if abs(median - median_last) < m_threshold and median > min_median and median < max_median:
                matches += 1
            else:
                matches = 0
            if matches >= good_frames: 
                break
    
            df_last = drops   #df_last = df
            gain_last = gain
            median_last = median
            exposure_last = exposure

        self.gain = gain_last
        self.exposure = exposure_last
        self.autoExp = True
        self.autoGain = True
        self.median = median_last

        return [self.exposure, self.gain, self.median]
            



