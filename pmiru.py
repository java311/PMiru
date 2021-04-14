# Python imports 
import time
import cv2
import sys
import os
import argparse
import threading
import json

# Global variables 
cam = None   #ZWO,Baumer camera control
camType = 'baumer' 
wheel = None  #ZWO wheel control
leds = None #LED control object
motor = None #Motor control object
cubeIndex = 0    # cube index for the viewer
layerIndex = 0   # layer index for the viewer
cubeFolders = None  # folder list for the viewer
cubeFiles = None    # file list for the viewer
wSizeX = 320
wSizeY = 240
sm = None #Kivy ScreenManager
cubeThread = None # thread object to run capture process
calibThread = None # thread object to run the calibration capture 

# PROGRAM CONTROL FLAGS
# These flags are populated with config.json file
enableWheel = None  # Enables the use of the wheel (deprecated)
maximizeStart = None # Starts kivy maximized or not 
stackedTiffs = None # Created stacked tiff files by LED color
rotateImages = None # Rotates images after capture

# Kivy imports
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.image import CoreImage
from kivy.graphics.texture import Texture
from kivy.core.image import Image 
from kivy.core.window import Window

# Program python classes 
if enableWheel:
    from control.wheel_control import WheelControl   #class to control the wheel
from control.camWrap import camWrap              #class to wrap ZWO and Baumer API cameras
from control.ledControl import ledControl 
from control.motorControl import Motor

class FirstScreen(Screen):
    def __init__(self, **kwargs):
        super(FirstScreen, self).__init__(**kwargs)

class CameraScreen(Screen):

    def __init__(self, **kwargs):
        super(CameraScreen, self).__init__(**kwargs)

        self.refreshByFile = False
        self.image_path = ""
        self.image_name = ""
        self._lock = threading.Lock()
        self.lightON = False

    #clock to refresh the camera live feed
    def cameraRefreshCallback(self, dt=0):
        if self.refreshByFile: 
            with self._lock:
                fullpath = self.image_path + os.path.sep + self.image_name
                if os.path.exists(fullpath):
                    self.ids.cam_img.source = fullpath
        else:
            frame = camWrap.get_video_frame()
            if frame is not None:   #3648, 5472
                #reshape the frame to the windows size 
                frame = cv2.resize(frame,(wSizeX,wSizeY))
                image_texture = Texture.create(size=(wSizeX,wSizeY), colorfmt='luminance')
                
                #create texture buffer for to show the image 
                if camWrap.get_img_type() == 8:
                    image_texture.blit_buffer(frame.tostring(), colorfmt='luminance', bufferfmt='ubyte')
                    self.ids.cam_img.texture = image_texture
                else:  #if the image is 16 bit, do nothing (cause Kivy's texture do not support this format
                    image_texture.blit_buffer(frame.tostring(), colorfmt='luminance', bufferfmt='ushort')
                    self.ids.cam_img.texture = image_texture

            else:
                # print ("ERROR: No image...")  
                pass

    def shoot_release(self):
        global cubeThread

        cubeThread = threading.Thread(target=takeHyperCube)
        cubeThread.start()

    def screen_change(self, screen):
        if (screen == 'viewer'):
            global cubeFolders
            global cubeFiles
            cubeFolders, cubeFiles = camWrap.getCubesList()
            sm.get_screen("viewer").imageChange(cubeIndex, 0)

        self.manager.current = screen

    def exit_press(self):
        sys.exit(0)

    def rotate_press(self):
        motor.moveToNextAngle()

    def lighton_press(self):
        leds.rotateLight()

    def hide_progress_bar(self, dohide=True):
        wid = self.ids.prog_bar
        if hasattr(wid, 'saved_attrs'):
            if not dohide:
                wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs
                del wid.saved_attrs
        elif dohide:
            wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, True

############  VIEWER GUI CONTROL CLASS ####################
class ViewerScreen(Screen):
        
    def imageChange(self, cube_index, layer_index):
        maxCubes = len(cubeFolders)
        if maxCubes == 0: 
            self.ids.cube_txt.text = "No Captures"
            self.ids.viewer_img.source = 'img_not_found.jpg'
            return 

        self.ids.cube_txt.text = str(cube_index) + "/" + str(maxCubes -1 )
        maxLayers = len(cubeFiles[cube_index])
        if maxLayers == 0: 
            self.ids.layer_txt.text = "Layers: None"
            self.ids.viewer_img.source = 'img_not_found.jpg'
            return 
        self.ids.layer_txt.text = "Layer " + str(layer_index)  + " of " + str(maxLayers -1)
        self.ids.viewer_img.source = cubeFiles[cube_index][layer_index]

    def imageChangebyFile(self, path, fname):
        fullpath = path + os.path.sep + fname
        self.ids.viewer_img.source = fullpath

    def viewerBack_release(self):
        global cubeIndex
        cubeIndex = cubeIndex - 1
        if (cubeIndex < 0):
            cubeIndex = len( cubeFolders ) - 1
        self.imageChange(cubeIndex, 0)

    def viewerNext_release(self):
        global cubeIndex
        cubeIndex = cubeIndex + 1
        if cubeIndex >= len(cubeFolders) :
            cubeIndex = 0
        self.imageChange(cubeIndex, 0)

    def viewerLayerUp_release(self):
        global layerIndex
        global cubeIndex
        layerIndex = layerIndex + 1
        if layerIndex > len(cubeFiles[cubeIndex]) -1:
            layerIndex = 0
        self.imageChange(cubeIndex, layerIndex)
    
    def viewerLayerDown_release(self):
        global layerIndex
        global cubeIndex
        layerIndex = layerIndex - 1
        if layerIndex < 0:
            layerIndex = len(cubeFiles[cubeIndex]) -1
        self.imageChange(cubeIndex, layerIndex)

class ConfigScreen(Screen):

    def __init__(self, **kwargs):
        super(ConfigScreen, self).__init__(**kwargs)

        self.exposure = 50    #50ms
        self.min_exp = 1
        self.max_exp = 1000
        self.autoExposure = True

        self.gain = 50
        self.min_gain = 1
        self.max_gain = 100
        self.autoGain = True  #auto gain flagdo df
        if camType == 'zwo':
            minmax = camWrap.getMinMaxGain() 
            self.ids.gain_slider.max = minmax[1]

    #######################  EXPOSURE CONTROLS ####################
    def exposureUp_press(self): 
        if (self.exposure < self.max_exp):
            self.exposure = self.exposure + 1
            self.ids.exp_txt.text = str(self.exposure)
            self.ids.exp_slider.value = self.exposure

    def exposureDown_press(self):
        if (self.exposure > self.min_exp):
            self.exposure = self.exposure - 1
            self.ids.exp_txt.text = str(self.exposure)  
            self.ids.exp_slider.value = self.exposure 

    def updateExpSlider(self, instance, value):
        self.exposure = value
        
    # Callback for the checkbox 
    def autoExposure_click(self, button): 
        if self.autoExposure == False:
            #auto calibrate and disable exposure input
            camWrap.setAutoExposure(True)
            self.ids.exp_slider.disabled = True
            self.ids.exp_up.disabled = True
            self.ids.exp_down.disabled = True
            # self.ids.exp_range_select.disabled = True
            button.opacity = 0.5
            button.text = "Auto ON"
            self.autoExposure = True
        else: 
            #update the GUI values 
            self.exposure = int(camWrap.get_exposure()/1000)  #in milliseconds 
            self.ids.exp_slider.value = self.exposure
            # self.ids.exp_range_select.disabled = False
            self.ids.exp_slider.disabled = False
            self.ids.exp_up.disabled = False
            self.ids.exp_down.disabled = False
            # if self.exposure < 100:
            #     self.exposureRange_change(self.exp_range_values[0])
            # else:
            #     self.exposureRange_change(self.exp_range_values[1])
            camWrap.setAutoExposure(False)
            button.opacity = 1.0
            button.text = "Auto OFF"
            self.autoExposure = False

    #######################  GAIN GUI CONTROLS ####################

    def gainUp_press(self): 
        if (self.gain < self.max_gain):
            self.gain = self.gain + 1
            self.ids.gain_txt.text = str(self.gain)
            self.ids.gain_slider.value = self.gain

    def gainDown_press(self):
        if (self.gain > self.min_gain ):
            self.gain = self.gain - 1
            self.ids.gain_txt.text = str(self.gain)
            self.ids.gain_slider.value = self.gain

    def updateGainSlider(self, instance, value):
        self.gain = value

    def autoGain_click(self, button): 
        if self.autoGain == False:
            #auto calibrate and disable exposure input
            camWrap.setAutoGain(True)
            self.ids.gain_slider.disabled = True
            self.ids.gain_up.disabled = True
            self.ids.gain_down.disabled = True
            button.opacity = 0.5
            button.text = 'Auto ON'
            self.autoGain = True
        else: 
            #update the GUI values 
            self.gain = camWrap.get_gain()  #in milliseconds 
            self.ids.gain_slider.value = self.gain #udpate gain value
            self.ids.gain_slider.disabled = False
            self.ids.gain_up.disabled = False
            self.ids.gain_down.disabled = False
            camWrap.setAutoGain(False)
            button.opacity = 1.0
            button.text = 'Auto OFF'
            self.autoGain = False


    #######################  GENERAL CONTROLS  ####################
    # Take the config values and send them to the camera
    def backToCamera_release(self):
        if self.autoGain == False: #if not auto exposure 
            camWrap.set_gain(self.gain)
        if self.autoExposure == False:  #it not auto gain
            camWrap.set_exposure(self.exposure)
        
        self.manager.current = 'camera'  #switch screen

    # Function that calibrates the exposure levels of each led
    def autoCalibration_click(self):
        global calibThread

        calibThread = threading.Thread(target=runLightCalibration())
        calibThread.start()

    
    
class PmiruApp(App):
    def build(self):
        global sm 
        sm = ScreenManager()
        sm.add_widget(CameraScreen(name='camera'))
        sm.add_widget(ConfigScreen(name='config'))
        sm.add_widget(ViewerScreen(name='viewer'))

        Window.size = (wSizeX, wSizeY)
        Window.bind(on_resize=self.check_resize)
        Window.fullscreen = maximizeStart #Maximizes Kivy Window

        return sm

    def on_start(self, **kwargs):
        if sm.current == 'camera':
            Clock.schedule_interval(sm.get_screen("camera").cameraRefreshCallback, 0.01)
        sm.get_screen("camera").hide_progress_bar(True)

    def check_resize(self, instance, x, y):
        global wSizeX, wSizeY
        wSizeX = Window.size[0]
        wSizeY = Window.size[1]

# NOTE FOR THIS FUNCTION TO WORK THE CAMERA HAS TO BE PLACEN INFRONT A WHITE SCREEN OR SURFACE
# Gain/Exposore calibration for each LED of the camera by
# taking calculating the median illumination value of a white surface
def runLightCalibration():
    # # First use the all LEDs in auto gain/exp to get a reference median value
    camWrap.captureLoop(False) #for zwo camera is necessary to stop the video loop

    darkIndex = leds.getDarkestIndex()
    camWrap.setAutoExposure(True)
    camWrap.setAutoGain(True)
    sm.get_screen("camera").refreshByFile = True # Disable camera refresh screen
    tmpFilePath = os.getcwd() + os.path.sep + "median_calib.tiff"
    
    nColors = leds.nColors
    autoGainVals = [];  autoExpVals = [];  autoMedVals = []
    darkGain = 0; darkExp = 0; darkMed = 0
    for color in range(0,nColors): # For each color
    
        leds.colorOnOff(color, True)  # Turn on the darkest LED ON
        
        autoMedVals.append(camWrap.get_median_singleShoot(tmpFilePath, drops=3, avgs=1))
        autoExpVals.append(camWrap.get_exposure()/1000.0)    #in miliseconds
        autoGainVals.append(camWrap.get_gain())              #unitless 

        if darkIndex == color:
            darkMed = autoMedVals[-1]
            darkExp = autoExpVals[-1]
            darkGafin = autoGainVals  

        leds.colorOnOff(color, False)  # Turn on the darkest LED OFF

    # # Adjust the gain / exp of each LED to approach the reference median value (darkIndex)
    camWrap.setAutoExposure(False)
    camWrap.setAutoGain(False)

    # autoMedVals = [34186.666666666664, 20864.0, 52800.0, 60736.0, 30762.666666666668, 19392.0, 20608.0, 82560.0, 42560.0, 11136.0, 54421.333333333336]
    # autoExpVals = [17.712, 20.545, 16.488, 12.284, 12.284, 15.799, 18.405, 9.639, 8.555, 11.292, 8.865]
    # autoGainVals = [196, 204, 200, 196, 196, 212, 220, 212, 208, 216, 212]
    # darkGain = 220; darkExp = 18.405; darkMed = 20608
    # darkIndex = leds.getDarkestIndex()
    # nColors = leds.nColors


    print (autoMedVals)
    print (autoExpVals)
    print (autoGainVals)

    drops = 5
    avgs = 3
    cycles = 0
    threshold = 5
    # gains = [0]*nColors; exps = [0]*nColors; meds = [0]*nColors; ok = [False]*nColors
    gains = autoGainVals; exps = autoExpVals; meds = autoMedVals; ok = [False]*nColors
    g_step = 5; e_step = 3
    ok[darkIndex] = True
    while (cycles <= 10):

        for color in range(0,nColors):
            if ok[color] == True:
                continue

            if (meds[color] <= meds[darkIndex]): # increase gain / exp
                exps[color] =  exps[color] + e_step
                gains[color] =  gains[color] + g_step
            elif (meds[color] > meds[darkIndex]):  # decrease gain
                exps[color] =  exps[color] - e_step
                gains[color] =  gains[color] - g_step

            camWrap.set_gain(gains[color])
            camWrap.set_exposure(exps[color])
            leds.colorOnOff(color, True)  # Turn on the darkest LED ON

            meds[color] = camWrap.get_median_singleShoot(tmpFilePath, drops=3, avgs=1)
            # exp = camWrap.get_exposure()   #in microseconds
            # gain = camWrap.get_gain()      #unitless

            # adjust the gain and the median
            # gains[color] = (autoGainVals[darkIndex] * meds[color]) / autoGainVals[darkIndex]
            # exps[color] = (autoExpVals[darkIndex] * meds[color]) / autoExpVals[darkIndex]

            # check if threshold is reached
            if abs(meds[color] - meds[darkIndex]) < thrsaeshold:
                ok[color] = True

            leds.colorOnOff(color, False)  # Turn on the darkest LED ON
            print (ok)
            print (meds)
            print (exps)
            print (gains)

        #break cycle if all medians are bellow the threshold
        allOk = True
        for color in range(0,leds.nColors):
            if ok[color] == False:
                allOk = False
                break
         
        if allOk == True:
            break

        cycles = cycles +1
        print ('cyclo:' + str(cycles))


    # for color in range(0,leds.nColors): # For each color
    #     if color == darkIndex: #Jump the darkest LED
    #        continue

    #     leds.colorOnOff(color, True)  # Turn on the darkest LED ON

    #     camWrap.set_gain(darkGain)
    #     camWrap.set_exposure(darkExp)
        
    #     median = 0
    #     limit = 1000
    #     while (darkMedian - median > limit):
    #         median = camWrap.get_median(drops=3, avgs=3)
    #         print (darkMedian)
    #         print (median)
    #         print (median - darkMedian)

    #         camWrap.set_gain(darkGain)
    #         camWrap.set_exposure(darkExp)

    #     leds.colorOnOff(color, False)  # Turn on the darkest LED ON
        

    # # sm.get_screen("camera").refreshByFile = False # Disable camera refresh screen


    # # Save the calibration results in config json file



# Rotate, change light and take picture
def takeHyperCube():
    global sm
    camWrap.captureLoop(False) #for zwo camera is necessary to stop the video loop

    folder = camWrap.getNewFolder()
    counter = 1
    nAngles = motor.getNumAngles()
    nlayers = leds.nColors * nAngles 
    motor.movetoInit()  #moves motor to the first angle of the list
    sm.get_screen("camera").hide_progress_bar(False)  #show progress bar
    sm.get_screen("camera").ids.prog_bar.value = 0
    sm.get_screen("camera").ids.shoot_btn.disabled = True
    # camWrap.stopVideoMode()
    for angle in range(0,nAngles): # For each angle
        motor.moveToAngle(angle) # Move the motor to the next angle
        for color in range(0,leds.nColors): # For each color
            leds.colorOnOff(color, True)  # Turn lights ON
            fname = "img_" + format(counter, '02d') + "_c" + format(color, '02d') + "_a" + format(motor.getAngle(angle), '02d') + ".tiff"
            camWrap.takeSingleShoot(path=folder, filename=fname, drops=3)
            # time.sleep(5)  #Image save is asynchonus, so lets wait a sec.
            leds.colorOnOff(color, False)  # Turn lights OFF
            
            progress = int((counter * 100) / nlayers)
            counter = counter + 1
            print ("Progress: " + format(progress, '02d') )
            sm.get_screen("camera").ids.prog_bar.value = progress

            # Update camera viewer
            # TODO Only load 1/3 of the images is only a quick fix not a bug solution
            if color % 3 == 0:
                sm.get_screen("camera").refreshByFile = True
                with sm.get_screen("camera")._lock:
                    sm.get_screen("camera").image_name = fname
                    sm.get_screen("camera").image_path = folder
                
    if rotateImages == True:
        camWrap.rotateImageFiles(folder)  #If ZWO, then rotate the captured images
    if stackedTiffs == True:
        camWrap.buildTiffStacks(folder, leds, sm.get_screen("camera").ids.prog_bar)  #Stacked tiffs by led color 

    camWrap.saveControlValues(path=folder, filename="controlValues.txt")
    camWrap.captureLoop(True)
    sm.get_screen("camera").ids.shoot_btn.disabled = False  #enable shoot button again
    sm.get_screen("camera").refreshByFile = False  #go back to normal camera refresh
    sm.get_screen("camera").hide_progress_bar(True) #hide progress bar


if __name__ == "__main__":
    # #Check cmd line arguments
    # parser = argparse.ArgumentParser(prog="pmiru")
    # parser.add_argument("-m", help="full screen start", action='store_true', required=False)
    # args = parser.parse_args()
    # if args.m :
    #     maximizeStart = True
    
    # Read config json file and initilize config flags and led values
    with open('config.json') as cfile:
        cfg = json.load(cfile)
        for c in cfg['config']:
            enableWheel = c['wheel']
            maximizeStart = c['maximized'] 
            stackedTiffs = c['stacks']
            rotateImages = c['rotate']

    #Start camera and read avalaible captures
    camWrap = camWrap() 
    camType = camWrap.camType
    cubeFolders, cubeFiles = camWrap.getCubesList()

    #Init LED control object
    leds = ledControl()

    #Init Motor control object
    motor = Motor()
    motor.initAngles([-144, -99, -54, -9, 36])
    motor.movetoInit() 

    #In case you want to use the filter wheel
    if enableWheel:
        wheel = WheelControl()
        #wheel.startINDIServer()  #TODO if this is not done connected function just loops 
        wheel.connect("localhost",7624,"ASI EFW",5) 

        #first ensure conection to the INDIServer
        print (wheel.isConnected())
        if (wheel.isConnected() == False):
            print("ERROR: Cannot connect to INDI server.")
            sys.exit()

        slot = wheel.getSlot()
        print ("current slot: " + str(slot))

    PmiruApp().run()
