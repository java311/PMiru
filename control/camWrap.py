# Python imports
import subprocess
import cv2
import sys
import os
from sys import platform
from datetime import datetime
import tifffile

# Program imports
from control.asioCam import asioCam              #class to control the ZWO camera
from control.baumerCam import baumerCam          #class to control the Baumer camera

class camWrap():
    cam = None
    camType = 'zwo'
    rootPath = ""
    cubeIndex = 0
    cubePaths = None
    cubeFiles = None

    def __init__(self):
        #check OS 
        if platform == 'win32':  #If Windows select the camera type manually
            self.camType =  'zwo'
        else:     
            self.camType = self.checkCamType()

        if self.camType == 'zwo':
            asioCam()
            #global objects for ASIO camera control
            self.cam = asioCam()

            lib_path = "/lib/arm-linux-gnueabihf/libASICamera2.so"  #DEFAULT OS raspbian
            if platform == 'win32':
                lib_path = "C:\\pmiru\\software\\zwo\\ASI SDK\\lib\\x64\\ASICamera2.dll"
            if platform == 'ubuntu':
                lib_path = "/home/pi/Downloads/ASI_linux_mac_SDK_V1.16.3/lib/armv7/libASICamera2.so"
            
            if (self.cam.initCam(lib_path=lib_path) == True):
                self.cam.startCaptureLoop()
            else:
                print("ERROR: Failed camera init.")
                sys.exit()

            self.setRootPath()
        else:
            self.cam = baumerCam()
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
            return 'zwo'  #zwo found 

        # check if ZWO120MM (mini finder) is present
        out = subprocess.Popen(['lsusb', '-d', '03c3:120c'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        
        stdout = stdout.decode('utf-8')
        if stderr == None and stdout.find('03c3:120c') != -1:
            print ("ZWO120MM (mini finder) camera found.")
            return 'zwo'  #zwo found 
 
        # check if ZWO178 MM is present (medium size CCD)
        out = subprocess.Popen(['lsusb', '-d', '03c3:178c'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        
        stdout = stdout.decode('utf-8')
        if stderr == None and stdout.find('03c3:178c') != -1:
            print ("ZWO 178MM (medium size CCD) camera found.")
            return 'zwo'  #zwo found 

        #check if Baumer is present 
        out = subprocess.Popen(['lsusb', '-d', '2825:0157'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        
        stdout = stdout.decode('utf-8')
        if stderr == None and stdout.find('2825:0157') != -1:
            print ("Baumer camera found.")
            return 'baumer'  #baumer found


        print ("ERROR: No Baumer or ZWO cameras found")
        sys.exit()
        

    def get_video_frame(self):
        return self.cam.get_video_frame()

    def get_img_type(self):
        return self.cam.imgType
        
    def get_exposure(self):
        if self.camType == 'zwo':
            return self.cam.exposure
        else:
            return self.cam.get_exposure()

    def get_gain(self):
        if self.camType == 'zwo':
            return self.cam.gain
        else:
            r = self.cam.get_gain() #range [0,10]
            return int(r * 10)  #map to 0-100 % value
              
    def set_exposure(self, value):
        self.cam.setExposure(value)

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
        else:
            pass

    def takeSingleShoot(self, path, filename, drops):
        self.cam.takeSingleShoot(path=path, filename= filename, drops=drops )

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

    def listdir_fullpath(self, d):
        return [os.path.join(d, f) for f in os.listdir(d)]

    # get the hypercube folder list for the viewer 
    def getCubesList(self):
        folders = []
        for (root,dirs,files) in os.walk(self.rootPath, topdown=True):
            folders = dirs
            break
        
        flist = []
        for folder in folders:
            ff = []
            for item in self.listdir_fullpath(self.rootPath + os.path.sep + folder + os.path.sep):
                if os.path.isfile(item) and item.endswith('.jpg'):   #zwo (TODO this may be changed)
                    ff.append(item)
                if os.path.isfile(item) and item.endswith('.tiff'):  #baumer (saved with opencv)
                    ff.append(item)
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

    # If ZWO, then rotate the captured images 
    def rotateImageFiles(self, path): 
        if self.camType == 'zwo':
            print ('Rotating image FILES taken with ZWO cameras. This will be slow....')
            ff = []
            for item in self.listdir_fullpath(path):  #openf jpg and tiff
                if os.path.isfile(item) and item.endswith('.jpg'):   
                    ff.append(item)
                if os.path.isfile(item) and item.endswith('.tiff'):  
                    ff.append(item)

            for img_path in ff:
                print ("Rotating: " + img_path)
                img = cv2.imread(img_path)  #open image
                rotated_img = cv2.rotate(img, cv2.ROTATE_180)  #rotate
                cv2.imwrite(img_path, rotated_img)  #overwrite
        else:
            pass

    # Builds a TIFF stack for each of the LED color
    def buildTiffStacks(self, path, leds, prog_bar):
        print ('Building the TIFF stacked files by LED color. This will be slow....')
        ff = []
        for item in self.listdir_fullpath(path):  #open ONLY tiff files
            if os.path.isfile(item) and item.endswith('.tiff'):  
                ff.append(item)

        stackPath = path + os.path.sep 
        prog_bar.value = 0
        for color in range(0,leds.nColors): #For each LED color
            with tifffile.TiffWriter(stackPath + "stack_" + str(leds.getWavelenght(color)) + "nm_.tiff") as stack:
                for img_path in ff:
                    if "_c" + format(color, '02d') in img_path:
                        print ("Saving file in stack: " + img_path)
                        stack.save(tifffile.imread(img_path), photometric='minisblack', contiguous=True)

            progress = int((color * 100) / leds.nColors)
            prog_bar.value = progress
            print ("Tiff Stack saved: " + stackPath + "stack_" + str(leds.getWavelenght(color)) + "nm_.tiff") 

        
        

    
    

    

    




