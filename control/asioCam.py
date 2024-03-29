import numpy as np
import cv2
import glob, os
import sys
import json
import time
import re
import zwoasi as asi
from threading import Thread
from collections import deque
from PIL import Image, ImageOps


# Documentation
# https://github.com/stevemarple/python-zwoasi/blob/master/zwoasi/__init__.py
# https://github.com/OpenPHDGuiding/phd2/blob/master/cameras/ASICamera2.h

class asioCam():
    def __init__(self, deque_size=50 ):
        self.cam_id = 0    #camera libray ID
        self.camera = None #camera object
        self.timeout = -1  #infinite timeout
        self.exposure = None
        self.gain = None
        self.median = None
        self.stop = False
        self.autoExp = False
        self.autoGain = False
        
        self.imgType = 16  #8 or 16 bits


        #object to que the frames
        # self.deque = deque(maxlen=deque_size)
        self.deque = []
        self.deque_indx = -1
        self.MAX_LEN = deque_size
        self.first = True

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

        # Restore all controls to default values 
        controls = self.camera.get_controls()
        for c in controls:
            if controls[c]['ControlType'] == asi.ASI_BANDWIDTHOVERLOAD:
                continue
            self.camera.set_control_value(controls[c]['ControlType'], controls[c]['DefaultValue'])

        self.camera.set_control_value(controls['AutoExpMaxExpMS']['ControlType'], 2000000)  # Set MAX exposure time to 2 seconds

        if imgType == 8:
            print ("Setting camera to 8 bits....")
            self.camera.set_image_type(asi.ASI_IMG_RAW8)
            self.imgType = 8
        else:
            print ("Setting camera to 16 bits....")
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

        self.autoExposureGainCalib(with_median=False, wait=0.500, drops=0, good_frames=5, min_median = 15, max_median = 200)  #calibrate gain and exposure values
        print ("Auto Gain value: " + str(self.gain))
        print ("Auto Exposure value: " + str(self.exposure))
        
        return True 

    # changes camera bitrate
    def changeImgType(self, imgType):
        if imgType == 8:
            self.camera.set_image_type(asi.ASI_IMG_RAW8)
            self.imgType = imgType
        if imgType == 16:
            self.camera.set_image_type(asi.ASI_IMG_RAW16)
            self.imgType = imgType

    # gets the max and min gain 
    def getMinMaxGain(self):
        controls = self.camera.get_controls()
        #value = self.camera.get_control_value(asi.ASI_AUTO_MAX_GAIN, controls['Gain'])
        # controls[asi.ASI_AUTO_MAX_GAIN]
        return [controls['AutoExpMaxGain']['MinValue'],controls['AutoExpMaxGain']['MaxValue']  ]

    # gets the exposure value from the camera API
    def getExposure(self):
        settings = self.camera.get_control_values()
        print ("Exposure is " + str(settings['Exposure']))
        return settings['Exposure']
        
    # gets the exposure value from the camera API
    def getGain(self):
        settings = self.camera.get_control_values()
        print ("Gain is " + str(settings['Gain']))
        return settings['Gain']

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
    def autoExposureGainCalib(self, with_median, wait, drops, good_frames, min_median, max_median ):
        controls = self.camera.get_controls()

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
        # self.camera.set_control_value(controls['AutoExpMaxExpMS']['ControlType'], 2000000)  # Set MAX exposure time to 2 seconds

        print('Waiting for auto-exposure to compute correct settings ...')
        sleep_interval = wait  #0.100 original value
        df_last = None
        gain_last = None
        exposure_last = None
        m_threshold = 5
        median_last = 0
        # min_median = 8
        # max_median = 200
        matches = 0
        self.getMedianRawShoot(drops,0)   #drop some frames before taking real values
        while True:
            time.sleep(sleep_interval)
            settings = self.camera.get_control_values()
            df = self.camera.get_dropped_frames()
            gain = settings['Gain']
            exposure = settings['Exposure']
            median = 0
            if df != df_last:
                if with_median == True: #Hack added to calibrate the camera with median instead of exposure/gain
                    median = self.getMedianRawShoot(0,1)
                    print('   Gain {gain:d}  Exposure: {exposure:d} Median: {median:f} Dropped frames: {df:d}'
                    .format(gain=settings['Gain'],
                            exposure=settings['Exposure'],
                            median=median,
                            df=df))
                    if abs(median - median_last) < m_threshold:  # and median > min_median and median < max_median:
                        matches += 1
                    else:
                        matches = 0
                    if matches >= good_frames: #5 original value
                        break
                else:
                    print('   Gain {gain:d}  Exposure: {exposure:d} Median: {median:f} Dropped frames: {df:d}'
                    .format(gain=settings['Gain'],
                            exposure=settings['Exposure'],
                            median=median,
                            df=df))
                    if gain == gain_last and exposure == exposure_last:
                        matches += 1
                    else:
                        matches = 0
                    if matches >= good_frames: #5 original value
                        break
    
                df_last = df
                gain_last = gain
                median_last = median
                exposure_last = exposure
        self.gain = gain_last
        self.exposure = exposure_last
        self.autoExp = True
        self.autoGain = True
        self.median = median_last

        # print('Use maximum USB Bandwidth')
        # self.camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, self.camera.get_controls()['BandWidth']['MaxValue'])
        return [self.exposure, self.gain, self.median]  # return in ms, %, raw median

    # Set the manual exposure value 
    def setExposure(self, expValue, units='ns'):
        # Disable auto exposure
        self.autoExp = False
        self.setAutoExposure(False)

        if units == 'ns':
            expValue = expValue * 1000000 #convert ms to nanoseconds

        print ("Set exposure to: " + str(int(expValue)))
        self.camera.set_control_value(asi.ASI_EXPOSURE, int(expValue))  #this value MUST be integer (bugfix)

    #Manually set the gain of the camera 
    def setGain(self, gainValue):
        self.autoGain = False
        self.setAutoGain(False)

        print ("Set gain to: " + str(int(gainValue)))
        self.camera.set_control_value(asi.ASI_GAIN, int(gainValue))

    # Starts the capture daemon
    def startCaptureLoop(self):
        self.stop = False
        if self.get_frame_thread.isAlive() == False:
            self.get_frame_thread.start()

    # Stops the thread 
    def stopCaptureLoop(self):
        self.stop = True
        # self.deque.clear()
        self.deque_indx = 0

    # Only clear the frame queue
    def clearQueue(self):
        # self.deque.clear()
        self.deque_indx = 0

    # Main camera capture thread
    def get_frame(self):
        whbi = self.camera.get_roi_format()
        shape = [whbi[1],whbi[0]]
        while (True):
            now = round(time.time() * 1000)
            if self.stop == False:
                raw = self.camera.get_video_data(timeout=self.timeout)
                if self.imgType == 8 or self.imgType == 12:
                    rawImg = np.frombuffer(raw, dtype=np.uint8)
                else:
                    rawImg = np.frombuffer(raw, dtype=np.uint16)
                rawImg = rawImg.reshape(shape)
                # show = cv2.resize(rawImg, (800, 600))  # OPENCV DEBUG
                # show = cv2.cvtColor(show,cv2.COLOR_GRAY2RGB)             #OPENCV DEBUG

                # cv2.imshow("show", show)  #OPENCV DEBUG
                # cv2.waitKey(1)            #OPENCV DEBUG
                # self.deque.append(rawImg)
                if self.first:
                    self.deque.append(rawImg)
                else:
                    self.deque[self.deque_indx] = rawImg

                self.deque_indx = self.deque_indx + 1
                if self.deque_indx >= self.MAX_LEN:
                    self.deque_indx = 0
                    self.first = False
            time_len = round(time.time() * 1000) - now
            # print(time_len)


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
            # return self.deque[-1
            return self.deque[self.deque_indx]
        else:
            return None

     # Gets the mdian of the frame and drop it
    def get_median_frame(self):
        if len(self.deque) > 0 and self.stop == False:
            # frame = self.deque[-1]
            frame = self.deque[self.deque_indx]
            median = np.median(frame)
            return median
        else:
            return None

    def stopVideoMode(self):
        self.camera.stop_video_capture()

    def stopExposure(self):
        self.camera.stop_exposure()

    def startVideoMode(self):
        self.camera.start_video_capture()
        
    def getMedianRawShoot(self, drops, avgs):
        print ("Taking Median raw frame...")

        # Drop several frames before taking the GOOD one
        for i in range(drops):
            self.camera.get_video_data(timeout=self.timeout)
            print ("Median frame droped")

        if avgs <= 0:
            return 0 

        # this is the GOOD one
        median = 0
        for i in range(avgs):
            raw = self.camera.get_video_data(timeout=self.timeout)
            time.sleep(1)  #wait 1 sec
            median = np.median(raw)  #take median from raw data
        median = median / avgs

        return median

    # FAKE method to take still images from the video capture loop
    # bit indicates the image forta 8bit (jpeg) or 16bit (tiff) monochrome 
    def takeSingleShoot(self, path, filename, drops=3, rot=True):
        fullpath = path + os.path.sep + filename
        print ("Taking frame...")

        # Drop several frames before taking the GOOD one
        for i in range(drops):
            print ("Dropping frame ... " + str(i))
            self.camera.get_video_data(timeout=self.timeout)

        # this is the GOOD one
        self.camera.capture_video_frame(filename=fullpath, timeout=self.timeout)
        if rot:  #If rotation flag is on, rotate images with OpenCV
            img = cv2.imread(fullpath, -1)
            img = cv2.flip(img, -1)
            cv2.imwrite(fullpath, img)
            print ("Flipping image....")

        print ("Saving frame as: " + str(fullpath))

    # Saves the control values of the camera in a txt file
    def saveControlValues(self, path, filename):
        data = {}
        data['camera'] = []
        settings = self.camera.get_control_values()
        settings['type'] = 'zwo'
        data['camera'].append( { str(k) : str(settings[k]) for k in sorted(settings.keys())   } )
    
        data['lights'] = []
        data['angles'] = []
        # data['motor_angles'] = []
        # data['file_angles'] = []
        # data['real_angles'] =[]
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