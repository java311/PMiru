import numpy as np
import cv2
import glob, os
import sys
import time
import re
import zwoasi as asi
from threading import Thread
from collections import deque

# Documentation
# https://github.com/stevemarple/python-zwoasi/blob/master/zwoasi/__init__.py
# https://github.com/OpenPHDGuiding/phd2/blob/master/cameras/ASICamera2.h

class asioCam():
    cam_id = 0    #camera libray ID
    camera = None #camera object
    timeout = -1  #infinite timeout
    exposure = None
    gain = None
    stop = False
    autoExp = False
    autoGain = False
    
    imgType = 8  #8 or 16 bits


    def __init__(self, deque_size=50 ):
        #object to que the frames
        self.deque = deque(maxlen=deque_size)

        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True

    def initCam(self, lib_path='/lib/arm-linux-gnueabihf/libASICamera2.so',  cam_model='ZWO ASI183MM', imgType=8):

        # Init ASIO static library 
        print (lib_path)
        asi.init(lib_path)

        num_cameras = asi.get_num_cameras()
        if num_cameras == 0:
            print('No cameras found')
            return False

        cameras_found = asi.list_cameras()  # Models names of the connected cameras

        # Search for ZWO camera 
        if num_cameras > 1:
            print('Found %d cameras' % num_cameras)
            for n in range(num_cameras):
                if (cameras_found[n] == cam_model):
                    self.cam_id = n
        print('Using #%d: %s' % (self.cam_id, cameras_found[self.cam_id]))

        self.camera = asi.Camera(self.cam_id)

        if imgType == 8:
            self.camera.set_image_type(asi.ASI_IMG_RAW8)
            self.imgType = 8
        else:
            self.camera.set_image_type(asi.ASI_IMG_RAW16)
            self.imgType = 16

        # self.enableVideoMode(self.imgType)
        try:
            # Force any single exposure to be halted
            self.camera.stop_exposure()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass
        print('Enabling video mode')
        self.camera.start_video_capture()        

        self.autoExposureGainCalib()  #calibrate gain and exposure values
        print ("Auto Gain value: " + str(self.gain))
        print ("Auto Exposure value: " + str(self.exposure))
        
        return True 

    # gets the max and min gain 
    def getMinMaxGain(self):
        controls = self.camera.get_controls()
        #value = self.camera.get_control_value(asi.ASI_AUTO_MAX_GAIN, controls['Gain'])
        # controls[asi.ASI_AUTO_MAX_GAIN]
        return [controls['AutoExpMaxGain']['MinValue'],controls['AutoExpMaxGain']['MaxValue']  ]

    # sets auto exposure and calulates the right settings for it 
    def setAutoExposure(self, value):
        controls = self.camera.get_controls()
        self.camera.set_control_value(asi.ASI_EXPOSURE,
                                controls['Exposure']['DefaultValue'],
                                auto=value)
        self.autoExp = value

    def setAutoGain(self, value):
        controls = self.camera.get_controls()
        self.camera.set_control_value(asi.ASI_GAIN,
                                controls['Gain']['DefaultValue'],
                                auto=value)
        self.autoGain = value
    
    # calculate the correct settings for auto/gain exposure
    def autoExposureGainCalib(self):
        controls = self.camera.get_controls()
        print('Use minium USB Bandwidth')
        self.camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, self.camera.get_controls()['BandWidth']['MinValue'])

        print('Enabling auto-exposure mode')
        self.camera.set_control_value(asi.ASI_EXPOSURE,
                                controls['Exposure']['DefaultValue'],
                                auto=True)

        print('Enabling automatic gain setting')
        self.camera.set_control_value(asi.ASI_GAIN,
                                controls['Gain']['DefaultValue'],
                                auto=True)

        # Keep max gain to the default but allow exposure to be increased to its maximum value if necessary
        self.camera.set_control_value(controls['AutoExpMaxExpMS']['ControlType'], controls['AutoExpMaxExpMS']['MaxValue'])

        print('Waiting for auto-exposure to compute correct settings ...')
        sleep_interval = 0.100
        df_last = None
        gain_last = None
        exposure_last = None
        matches = 0
        while True:
            time.sleep(sleep_interval)
            settings = self.camera.get_control_values()
            df = self.camera.get_dropped_frames()
            gain = settings['Gain']
            exposure = settings['Exposure']
            if df != df_last:
                print('   Gain {gain:d}  Exposure: {exposure:f} Dropped frames: {df:d}'
                    .format(gain=settings['Gain'],
                            exposure=settings['Exposure'],
                            df=df))
                if gain == gain_last and exposure == exposure_last:
                    matches += 1
                else:
                    matches = 0
                if matches >= 5:
                    break
                df_last = df
                gain_last = gain
                exposure_last = exposure
        self.gain = gain_last
        self.exposure = exposure_last
        self.autoExp = True
        self.autoGain = True

        return [self.exposure, self.gain]


    def setExposure(self, expValue, units='ms'):
        self.autoExp = False
        self.setAutoExposure(False)

        if (units == 'ms'):
            microsec_exp = int(expValue * 1000)

        self.camera.set_control_value(asi.ASI_EXPOSURE, microsec_exp)
        return 

    #Manually set the gain of the camera 
    def setGain(self, gainValue):
        self.autoGain = False
        self.setAutoGain(False)

        self.camera.set_control_value(asi.ASI_GAIN, int(gainValue))
        return

    # Starts the capture daemon
    def startCaptureLoop(self):
        self.stop = False
        if self.get_frame_thread.isAlive() == False:
            self.get_frame_thread.start()

    # Stops the thread 
    def stopCaptureLoop(self):
        self.stop = True
        self.deque.clear()

    # Main camera capture thread
    def get_frame(self):
        whbi = self.camera.get_roi_format()
        shape = [whbi[1],whbi[0]]
        while (True):
            if self.stop == False:
                raw = self.camera.get_video_data(timeout=self.timeout)
                if self.imgType == 8:
                    rawImg = np.frombuffer(raw, dtype=np.uint8)
                else:
                    rawImg = np.frombuffer(raw, dtype=np.uint16)
                rawImg = rawImg.reshape(shape)
    
                #show = cv2.resize(rawImg, (self.guiResX, self.guiResY))  #original 
                #show = cv2.cvtColor(show,cv2.COLOR_GRAY2RGB)             #original

                # cv2.imshow("show", show)  #OPENCV DEBUG
                # cv2.waitKey(1)            #OPENCV DEBUG
                self.deque.append(rawImg)


    # Gets current image type of the camera
    def getimageType(self):
        t = this.camera.get_image_type()
        if t == asi.ASI_IMG_RAW8:
            return 8
        else:
            return 16

    # Gets a single frame from the queue
    def get_video_frame(self):
        if len(self.deque) > 0 and self.stop == False:
            return self.deque[-1]
        else:
            return None

    # FAKE method to take still images from the video capture loop
    # bit indicates the image forta 8bit (jpeg) or 16bit (tiff) monochrome 
    def takeSingleShoot(self, path, filename):
        fullpath = path + os.path.sep + filename
        print ("Taking frame...")
        self.camera.capture_video_frame(filename=fullpath, timeout=self.timeout)
        print ("Saving frame as: " + str(fullpath))


    # Saves the control values of the camera in a txt file
    def saveControlValues(self, path, filename):
        settings = self.camera.get_control_values()

        fullpath = path + os.path.sep + filename
        with open(fullpath, 'w') as f:
            for k in sorted(settings.keys()):
                f.write('%s: %s\n' % (k, str(settings[k])))
        print('Camera settings saved to %s' % fullpath)