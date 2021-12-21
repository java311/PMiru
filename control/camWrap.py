# Python imports
import subprocess
import cv2
import sys
import os
from sys import platform
from datetime import datetime
import tifffile
from PIL import Image, ImageOps

# Program imports
from control.asioCam import asioCam              #class to control the ZWO camera
from control.baumerCam import baumerCam          #class to control the Baumer camera
from control.elpCam import elpCam                #class to contorl the ELP cameras

class camWrap():

    def __init__(self):
        self.cam = None
        self.camType = 'zwo'
        self.zwoMini = False
        self.rootPath = ""
        self.cubeIndex = 0
        self.cubePaths = None
        self.cubeFiles = None

        #check OS 
        if platform == 'win32':  #If Windows select the camera type manually
            self.camType =  'zwo'
        else:   
            ct = self.checkCamType() 
            self.camType = ct[0]
            self.zwoMini = ct[1]

        if self.camType == 'zwo':
            #global objects for ASIO camera control
            self.cam = asioCam()

            lib_path = "/lib/arm-linux-gnueabihf/libASICamera2.so"  #DEFAULT OS raspbian
            if platform == 'win32':
                lib_path = "C:\\pmiru\\software\\zwo\\ASI SDK\\lib\\x64\\ASICamera2.dll"
            elif os.uname()[4] == 'armv7l':  # for raspberry B4
                # lib_path = "/home/pi/Downloads/ASI_linux_mac_SDK_V1.20.3/lib/armv7/libASICamera2.so" # NEW LIBS TEST (DEBUG)
                lib_path = "/lib/arm-linux-gnueabihf/libASICamera2.so"
            elif os.uname()[4] == 'aarch64':  # jetson 
                lib_path = "/usr/lib/aarch64-linux-gnu/libASICamera2.so"
            
            if (self.cam.initCam(lib_path=lib_path, imgType=8) == True):  # default imgType 8bit 
                self.cam.startCaptureLoop()
            else:
                print("ERROR: Failed camera init.")
                sys.exit()

            self.setRootPath()
        elif self.camType == 'baumer':
            self.cam = baumerCam()
            self.cam.initCam(imgType=8)

            self.setRootPath()
        elif self.camType == 'elp':
            self.cam = elpCam()
            self.cam.initCam()

            self.setRootPath()
        

    # TODO this only works for Linux
    def checkCamType(self):
        # check if ZWO is present
        out = subprocess.Popen(['lsusb', '-d', '03c3:183a'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        
        stdout = stdout.decode('utf-8')
        if stderr == None and stdout.find('03c3:183a') != -1:
            print ("ZWO camera found.")
            return ['zwo',False]  #zwo found 

        # check if ZWO120MM (mini finder) is present
        out = subprocess.Popen(['lsusb', '-d', '03c3:120c'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        
        stdout = stdout.decode('utf-8')
        if stderr == None and stdout.find('03c3:120c') != -1:
            print ("ZWO120MM (mini finder) camera found.")
            return ['zwo',True]  #if zwo MINI also return True 
 
        # check if ZWO178 MM is present (medium size CCD)
        out = subprocess.Popen(['lsusb', '-d', '03c3:178c'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        
        stdout = stdout.decode('utf-8')
        if stderr == None and stdout.find('03c3:178c') != -1:
            print ("ZWO 178MM (medium size CCD) camera found.")
            return ['zwo',False]  #zwo found 

        #check if Baumer is present 
        out = subprocess.Popen(['lsusb', '-d', '2825:0157'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        
        stdout = stdout.decode('utf-8')
        if stderr == None and stdout.find('2825:0157') != -1:
            print ("Baumer camera found.")
            return ['baumer',False]  #baumer found

        #check if ELP monochrome camera is present
        out = subprocess.Popen(['lsusb', '-d', '32e4:0144'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        
        stdout = stdout.decode('utf-8')
        if stderr == None and stdout.find('32e4:0144') != -1:
            print ("ELP camera found.")
            return ['elp',False]  #elp camera found

        print ("ERROR: No Baumer, ZWO or ELP cameras were found.")
        sys.exit()

    def get_video_frame(self):
        return self.cam.get_video_frame()

    # Gets the median from the camera video feed. 
    # First drops some frames (for stability) and then returns the averaged median value
    def get_median(self, drops, avgs):
        self.cam.clearQueue() #Clear any previous captured frames

        # Drop some frames before taking any measurements
        i=0
        while(i <= drops):
            frame = self.cam.get_video_frame()
            if frame is None:
                # print("no video frame")
                continue
            i = i + 1

        # Average the median
        median = 0
        i = 0
        while(i <= avgs):
            m = self.cam.get_median_frame()
            if m is None:
                #print("no median frame")
                continue
            median = median + m # Average medians frames
            i = i + 1
        
        median = median / avgs
        return median

    def get_median_singleShoot(self, filepath, drops, avgs):
        if self.camType == 'zwo':
            return self.cam.getMedianSingleShoot(filepath, drops, avgs)
        else:
            pass

    def auto_exp_gain_calib(self, with_median, wait, drops, good_frames):
        if self.camType == 'zwo':
            return self.cam.autoExposureGainCalib(with_median, wait, drops, good_frames, min_median = 15, max_median = 200)
        else:
            return self.cam.autoExposureGainCalib(wait, drops=10, good_frames=good_frames, min_median = 10, max_median = 200)


    def get_img_type(self):
        return self.cam.imgType

    # changes the camera bitrate, but first stops all captures
    def changeImgType(self, imgType):
        try:
            self.cam.stopExposure()
            self.cam.stopVideoMode()
        except (KeyboardInterrupt, SystemExit):
            print ("ERROR: camera capture could be stopped.")
            raise
        except:
            print ("ERROR: camera capture could be stopped.")
            pass

        self.cam.changeImgType(imgType)
            
    # returns the camera exposure in ms (used only to update the inteface)
    def get_exposure(self):
        if self.camType == 'zwo':
            if self.zwoMini:
                # return int(self.cam.getExposure())
                exp_ms = int(self.cam.getExposure()/1000000)  #convert to ms
                if exp_ms <= 0:
                    exp_ms = 1
                return exp_ms
            else:
                return int(self.cam.getExposure()/1000.0)  
        else:
            return self.cam.get_exposure()

    def get_gain(self):
        if self.camType == 'zwo':
            return self.cam.getGain()
        else:
            r = self.cam.get_gain() #range [0,10]
            return int(r * 10)  #map to 0-100 % value
              
    # Exposure must be given in milliseconds
    def set_exposure(self, value):
        if self.camType == 'zwo':
            self.cam.setExposure(value, 'ns')
        else:
            self.cam.setExposure(value)
        
    # Gain must be given in a range between 0 to 100 (auto converts for Baumer)
    def set_gain(self, value):
        if self.camType == 'baumer':
            value = value / 10.0  #map value to baumer range [0,10]   
        self.cam.setGain(value)

    def setAutoExposure(self, value):
        self.cam.setAutoExposure(value)

    def setAutoGain(self, value):
        self.cam.setAutoGain(value)

    def getMinMaxGain(self):
        return self.cam.getMinMaxGain()

    def captureLoop(self, value):        
        if value == False:
            self.cam.stopCaptureLoop()
        else:
            self.cam.startCaptureLoop()

    def saveControlValues(self, path, filename):
        if self.camType == 'zwo':
            self.cam.saveControlValues(path=path, filename=filename)
        elif self.camType == 'elp':
            self.cam.saveControlValues(path=path, filename=filename)
        else:
            pass  #TODO implement this function for Baumer

    def takeSingleShoot(self, path, filename, drops, rot):
        self.cam.takeSingleShoot(path=path, filename=filename, drops=drops, rot=rot )

    def stopVideoMode(self):
        if self.camType == 'zwo':
            self.cam.stopVideoMode()
        else:
            pass

    def startVideoMode(self):
        if self.camType == 'zwo':
            self.cam.startVideoMode()
        else:
            pass

    def stopExposure(self):
        if self.camType == 'zwo':
            self.cam.stopExposure()
        else:
            pass

    # get the folder path wher to save the hypercube one folder per hypercube 
    def getNewFolder(self, prefix="cube_"):
        now = datetime.now()
        today = now.strftime("%Y%m%d")
        hour = now.strftime("%H%M")

        newFolder = self.rootPath + os.path.sep + prefix + today + "_" + hour + "_"
        counter = 1
        retVal = ""
        while True:
            retVal = newFolder + format(counter, '02d') 
            if os.path.isdir(retVal) == False:
                os.mkdir(retVal)
                break
            else:
                counter = counter + 1
        return retVal 

    # list files in a directory sorted by name
    def listdir_fullpath(self, d):
        return [os.path.join(d, f) for f in os.listdir(d)]

    # get the hypercube folder list for the viewer 
    def getHypercubesList(self):
        folders = []
        for (root,dirs,files) in os.walk(self.rootPath, topdown=True, followlinks=False):
            for folder in dirs:
                if len(os.listdir(self.rootPath + os.path.sep + folder)) > 0:
                    folders.append(folder)
            break
        
        # order the folders by creation date 
        folders.sort(key=lambda x: os.path.getmtime(self.rootPath + os.path.sep + x), reverse=True) 

        flist = []
        for folder in folders:
            ff = []
            for item in self.listdir_fullpath(self.rootPath + os.path.sep + folder + os.path.sep):
                if os.path.isfile(item) and item.endswith('.tiff') and os.path.getsize(item) < 30000000 : #Only TIFF file < 50 Mb will be listed
                    if os.path.splitext(os.path.basename(item))[0] != 'mask':  # Do not add selection mask to the list
                        ff.append(item)

            ff.sort(key=lambda x: os.path.getmtime(x), reverse=True)  #sort files by creation date
            flist.append(ff)

        return folders, flist

    # sets the default path and gets the number of the lats pic 
    def setRootPath(self, path=""):
        if path == "":
            self.rootPath = os.getcwd() + os.path.sep + "captures" # default is current dictory + captures
            if os.path.isdir(self.rootPath) == False:
                os.mkdir(self.rootPath) #create folder if do not exists
        else:
            self.rootPath = rootPath

    # Builds a TIFF stack for each of the LED color
    def buildTiffStacks(self, path, leds, prog_bar, exit_event):
        print ('Building the TIFF stacked files by LED color. This will be slow....')
        ff = []
        for item in self.listdir_fullpath(path):  #open ONLY tiff files
            if os.path.isfile(item) and item.endswith('.tiff'):  
                ff.append(item)

        stackPath = path + os.path.sep 
        prog_bar.value = 0
        img_indx = 0
        n = len(ff)
        print (len(ff))
        for color in range(0,leds.nColors): #For each LED color
            with tifffile.TiffWriter(stackPath + "stack_" + str(leds.getWavelenght(color)) + "nm_.tiff") as stack:
                for img_path in ff:
                    if exit_event.is_set():
                        print ("Stack creation killed...")
                        return
                    
                    if "_c" + str(leds.getWavelenght(color)) in img_path:
                        img_indx = img_indx + 1
                        prog_bar.value = int((img_indx * 100) / n)
                        print ("Saving file in stack: " + img_path + " " + str( int((img_indx * 100) / n) ) + " %" )
                        stack.save(tifffile.imread(img_path), photometric='minisblack', contiguous=True)

            print ("Tiff Stack saved: " + stackPath + "stack_" + str(leds.getWavelenght(color)) + "nm_.tiff") 

        
        

    
    

    

    




