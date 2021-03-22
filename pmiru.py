# Python imports 
import time
import cv2
import sys
import argparse

# Global variables 
cam = None   #ZWO,Baumer camera control
camType = 'baumer' 
wheel = None  #ZWO wheel control
leds = None #LED control object
enableWheel = False
cubeIndex = 0
layerIndex = 0
cubeFolders = None
cubeFiles = None
maximizeStart = False
wSizeX = 320
wSizeY = 240
sm = None #Kivy ScreenManager

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
from kivy.uix.image import Image
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
    #clock to refresh the camera live feed
    def cameraRefreshCallback(self, dt=0):
        frame = camWrap.get_video_frame()
        if frame is not None:   #3648, 5472
            #reshape the frame to the windows size anc convert to RGB 
            frame = cv2.resize(frame,(wSizeX,wSizeY))
            frame = cv2.cvtColor(frame,cv2.COLOR_GRAY2RGB) 
            
            #create texture buffer for to show the image 
            image_texture = Texture.create(size=(wSizeX,wSizeY), colorfmt='rgb')
            if camWrap.get_img_type() == 8:
                image_texture.blit_buffer(frame.tostring(), colorfmt='rgb', bufferfmt='ubyte')
            if camWrap.get_img_type() == 16:
                image_texture.blit_buffer(frame.tostring(), colorfmt='rgb', bufferfmt='ubyte')  #TODO not tested yet
            self.ids.cam_img.texture = image_texture
        else:
            # print ("ERROR: No image...")
            pass

    def shoot_release(self):
        takeHyperCube()
        print ("Hypercube captured")

    def screen_change(self, screen):
        if (screen == 'viewer'):
            global cubeFolders
            global cubeFiles
            cubeFolders, cubeFiles = camWrap.getCubesList()
            sm.get_screen("viewer").imageChange(cubeIndex, 0)

        self.manager.current = screen

    def exit_press(self):
        sys.exit(0)

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


    def check_resize(self, instance, x, y):
        global wSizeX, wSizeY
        wSizeX = Window.size[0]
        wSizeY = Window.size[1]

# Rotate, change light and take picture
def takeHyperCube():
    camWrap.captureLoop(False) #for zwo camera is necessary to stop the video loop

    folder = camWrap.getNewFolder()
    counter = 1
    nlayers = leds.nColors * motor.getNumAngles() 
    motor.movetoInit()  #moves motor to the first angle of the list
    for angle in range(0,motor.getNumAngles()): #For each angle
        for color in range(0,leds.nColors): #For each color
            leds.nextColorON()  #Next LED color ON

            fname = "img_" + format(counter, '02d') + "_c" + format(color, '02d') + "_a" + format(motor.getCurAngle(), '02d') + ".tiff"
            camWrap.takeSingleShoot(path=folder, filename=fname)
            leds.nextColorOFF()  #Next LED color OFF
            motor.moveToNextAngle() #Move the motor to the next angle
            
            progress = int((counter * 100) / nlayers)
            counter = counter + 1
            print ("Progress: " + format(progress, '02d') )

    # camWrap.rotateImageFiles(folder)  #If ZWO, then rotate the captured images
    camWrap.saveControlValues(path=folder, filename="controlValues.txt")
    camWrap.captureLoop(True)


if __name__ == "__main__":
    #Check cmd line arguments
    parser = argparse.ArgumentParser(prog="pmiru")
    parser.add_argument("-m", help="full screen start", action='store_true', required=False)
    args = parser.parse_args()
    if args.m :
        maximizeStart = True

    #Start camera and read avalaible captures
    camWrap = camWrap() 
    camType = camWrap.camType
    cubeFolders, cubeFiles = camWrap.getCubesList()

    #Init LED control object
    leds = ledControl() 

    #Init Motor control object
    motor = Motor()
    motor.initAngles([-144, -99, -54, -9, 36])

    #In case you want to use the filter wheel
    if enableWheel:
        wheel=WheelControl()
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
