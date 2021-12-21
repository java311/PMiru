# Elp camera SDK is very old and it is only available in C. 
# then to write a python SDK wrapper will be a waste of time. 
# Instead to control the camera parameters from python v4l2-ctl is used.
# And OpenCV is used to collect the camera output

# Python imports
import cv2
import os
import time
import json
import subprocess
import numpy as np
from threading import Thread
from collections import deque

#            ELP CAMERA PROPERTIES LABELS AND VALUES
#                      brightness 0x00980900 (int)    : min=-64 max=64 step=1 default=4 value=4
#                        contrast 0x00980901 (int)    : min=0 max=95 step=1 default=20 value=20
#                      saturation 0x00980902 (int)    : min=0 max=100 step=1 default=0 value=0
#                             hue 0x00980903 (int)    : min=-2000 max=2000 step=1 default=0 value=0
#  white_balance_temperature_auto 0x0098090c (bool)   : default=1 value=1
#                           gamma 0x00980910 (int)    : min=100 max=300 step=1 default=100 value=100
#                            gain 0x00980913 (int)    : min=16 max=255 step=1 default=32 value=32
#            power_line_frequency 0x00980918 (menu)   : min=0 max=2 default=1 value=1
#       white_balance_temperature 0x0098091a (int)    : min=2800 max=6500 step=1 default=4600 value=4600 flags=inactive
#                       sharpness 0x0098091b (int)    : min=0 max=7 step=1 default=0 value=0
#          backlight_compensation 0x0098091c (int)    : min=28 max=201 step=1 default=112 value=112
#                   exposure_auto 0x009a0901 (menu)   : min=0 max=3 default=3 value=3
#               exposure_absolute 0x009a0902 (int)    : min=1 max=8188 step=1 default=156 value=500 flags=inactive

# ELP camera control class
class elpCam():

    def __init__(self, deque_size=50 ):
        self.camera = None
        self.stop = False
        self.deque = None
        self.imgType = 8 
        self.resX = 1280
        self.resY = 720
        self.id = None

        #object to que the frames
        self.deque = deque(maxlen=deque_size)

        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True

    # self imgType is ignored, because the imgType cannot be selected
    # inits the ELP video camera
    def initCam(self, imgType=8):
        # self.set_image_resolution(1280, 720, 'YUYV')  # Set the biggest image resolution 1280x720 in YUYV format
        self.id = 0  # TODO Make a function that returns the camera OpenCV id
        self.camera = cv2.VideoCapture(self.id)
        self.set_image_resolution(1280, 720) # Max resolution for ELP camera in YUY2 format (v4l2-ctl -d /dev/video0 --list-formats-ext)
        
        self.initDefaultValues()
        self.startCaptureLoop()

    def initDefaultValues(self):
        self.setAutoExposure(True)
        self.setValue('brightness', 4)
        self.setValue('contrast', 20)
        self.setValue('gamma', 100)
        self.setValue('gain', 32)
        self.setValue('backlight_compensation', 112)

    def getValue(self, prop):
        out = subprocess.Popen(['v4l2-ctl', '--device', '/dev/video0', '-C', prop], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        
        stdout = stdout.decode('utf-8')
        # print (stdout)   # DEBUG
        split_stdout = stdout.split(': ')
        return int(split_stdout[1])


    def setValue(self, prop, value):
        out = subprocess.Popen(['v4l2-ctl', '--device', '/dev/video0', '-c', prop+"="+str(value) ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        
        stdout = stdout.decode('utf-8')
        # print (stdout)   # DEBUG
        return stdout
    
    # sets the Exposure to the given value
    def setExposure(self, value):
        # self.setValue('exposure_auto', 3)  # set manual exposure
        self.setValue('exposure_auto', 1)  # set manual exposure
        self.setValue('exposure_absolute', int(value))   #set exposure value

    def setGain(self, value):
        self.setValue('exposure_auto', 1)  # set manual exposure
        self.setValue('gain', int(value))  # set manual exposure

    def set_min_exposure(self):
        self.setExposure(1)
    
    def set_max_exposure(self):  
        self.setExposure(8188)

    def get_exposure(self):
        return self.getValue('exposure_absolute')

    def get_gain(self):
        return self.getValue('gain')

    def get_minmax_gain(self):
        return [16, 255] 

    # changes the ELP camera resolution 
    def set_image_resolution(self, resX=1280, resY=720):
        # Resolution can only be changed using OpenCV (v4l2-ctl is useless here)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, int(resX))
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, int(resY))
        self.resX = resX;  self.resY = resY

    def get_image_resolution(self):
        return [self.resX, self.resY] 
    
    def setAutoExposure(self, value):
        if value == True:
            self.setValue('exposure_auto', 3)  # set exposure to auto
        else:
            self.setValue('exposure_auto', 1)  # set exposure to manual

    # gain cannot be set automatically in ELP cameras 
    def setAutoGain(self, value):
        pass

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
    #camera imgType is ignored here. Captures are taken with the given imgType
    def takeSingleShoot(self, path, filename, drops=3, rot=False):
        fullpath = path + os.path.sep + filename
        # print ("Taking frame...")

        # Drop several frames before taking the GOOD one
        for i in range(drops*10):
            # print ("Dropping frame ... " + str(i))
            ret, img = self.camera.read()

        # this is the GOOD one
        ret, img = self.camera.read()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # THIS MAYBE IS SLOW
        cv2.imwrite(fullpath, img)
        print ("Saving frame as: " + str(fullpath))


    # Main camera capture thread
    def get_frame(self):
        while (True):   
            if self.stop == False:
                ret, buf = self.camera.read()  # get new frame
                # Transform frame from YUYV format to Grayscale
                buf = cv2.cvtColor(buf, cv2.COLOR_BGR2GRAY) # THIS MAYBE IS SLOW
                self.deque.append(buf)

    def getMedianRawShoot(self, drops):
        #Drop some frames first
        for i in range(drops):
            ret, img = self.camera.read()

        ret, img = self.camera.read()
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # THIS MAYBE IS SLOW
        median = np.median(img)
        # cv2.imshow("debugo", img)  #OPENCV DEBUG
        # cv2.waitKey(1)             #OPENCV DEBUG
        return median

    # ELP method to calibration is totally different from baumer and zwo 
    # because the auto exposure of the camera do not give us back the exposure value 
    # Altough the camera is faster, so it faster to compare frame medians
    def autoExposureGainCalib(self, wait, drops, good_frames, min_median, max_median ):
        # set AutoExposure ON
        self.setAutoExposure(True)
        print ("calculating a new color") 

        time.sleep(wait)  # wait for the image to stabilize 
        auto_exp_median = self.getMedianRawShoot(drops) # get the auto exposure median value

        # Get the exposure value by increasing the exposure and getting the median 
        median = 0
        exp_steps = 200
        exp = 1
        gain_steps = 5
        gain = 1
        self.setAutoExposure(False)  # turning OFF auto exposure
        self.setExposure(exp)
        self.setValue('gain', gain)
        for i in range(100):
            ret, img = self.camera.read()
    
        while ((median < auto_exp_median) and (exp < 8188)):
            self.setExposure(exp)
            self.setValue('gain', gain)
            median = self.getMedianRawShoot(drops)
            exp = exp + exp_steps
            gain = gain + gain_steps
            # print ("median: " + str(median))
            # print ("exp: " + str(exp))
            # print ("gain: " + str(gain))

        self.exposure =  exp 
        self.gain = gain
        self.median = auto_exp_median 

        return [self.exposure, self.gain, self.median]

    # Saves the control values of the camera in a txt file
    def saveControlValues(self, path, filename):
        data = {}
        # data['camera'] = []
        # settings = self.camera.get_control_values()
        # data['camera'].append( { str(k) : str(settings[k]) for k in sorted(settings.keys())   } )
    
        data['lights'] = []
        data['angles'] = []
        data['colors'] = []
        with open('config.json') as cfile:
            start = 0; stop =0; step =0
            cfg = json.load(cfile)
            for c in cfg['config']:
                start = c['start_angle']
                stop = c["stop_angle"]
                step = c["step_angle"] 
            
            data['angles'].append ({ "start" : start, 'stop': stop, 'step': step })  
            data['colors'].append([ c['wavelenght'] for c in cfg['lights']  ] )
            # data['motor_angles'].append([ r for i,r in enumerate(range ( start , stop , step ))  ] )  
            # data['file_angles'].append([ r for i,r in enumerate(range (90, 90 + (stop-start), step  )) ]  ) 
            # data['real_angles'].append( [r for i,r in enumerate(range(0, stop-start, step )) ] )  
            data['lights'] = cfg['lights']
             

        fullpath = os.path.join(path, filename)
        with open(fullpath, 'w') as f:
            json.dump(data, f, indent=1)

        print('Camera, motor and color settings saved to %s' % fullpath)

