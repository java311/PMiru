# Python imports 
import time
import sys

# Global variables 
cam = None   #ZWO,Baumer camera control
camType = 'zwo' 
wheel = None  #ZWO wheel control
enableWheel = False
cubeIndex = 0
layerIndex = 0
cubeFolders = None
cubeFiles = None

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

# Program python classes 
if enableWheel:
    from control.wheel_control import WheelControl   #class to control the wheel
from control.camWrap import camWrap              #class to wrap ZWO and Baumer API cameras

class FirstScreen(Screen):
    def __init__(self, **kwargs):
        super(FirstScreen, self).__init__(**kwargs)

class CameraScreen(Screen):
    #clock to refresh the camera live feed
    def cameraRefreshCallback(self, dt=0):
        frame = camWrap.get_video_frame()
        if frame is not None:
            image_texture = Texture.create(size=(800,600), colorfmt='rgb')
            if camWrap.get_img_type() == 8:
                image_texture.blit_buffer(frame.tostring(), colorfmt='rgb', bufferfmt='ubyte')
            if camWrap.get_img_type() == 16:
                image_texture.blit_buffer(frame.tostring(), colorfmt='rgb', bufferfmt='ubyte')  #TODO not tested yet
            self.ids.cam_img.texture = image_texture
        else:
            print ("ERROR: No image...")
            pass

    def shoot_release(self):
        takeHyperCube()
        print ("Hypercube captured")


############  VIEWER GUI CONTROL CLASS ####################
class ViewerScreen(Screen):

    def on_start(self, **kwargs):
        layerIndex = 0
        self.viewerRefresh()
        
    def imageChange(self, cube_index, layer_index):
        maxCubes = len(cubeFolders)
        maxLayers = len(cubeFiles[cube_index])
        self.ids.layer_txt.text = "Layer " + str(layer_index)  + " of " + str(maxLayers -1)
        self.ids.cube_txt.text = str(cube_index) + "/" + str(maxCubes -1 )

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
    exposure = 50    #50ms
    min_exp = 1
    max_exp = 100
    # exp_label_min = ['10us','1ms','100ms','1s']
    # exp_label_max = ['10ms','100ms','1000ms','10s']
    # exp_range_values = ['10us~10ms', '1~100ms', '100~1000ms', '1s~10s']
    exp_label_min = ['1ms','100ms']
    exp_label_max = ['100ms','1000ms']
    exp_range_values = ['1~100ms', '100~1000ms']

    gain = 200
    min_gain = 0
    max_gain = 1000

    #######################  EXPOSURE CONTROLS ####################

    def exposureRange_change(self, text):
        if text == self.exp_range_values[0]:      # 1~100ms
            self.ids.exp_range_label.text = 'ms'
            self.exposure = 50
            self.min_exp = 1
            self.max_exp = 100
            self.refreshExpSlider(1)

        elif text == self.exp_range_values[1]:     # 100~1000ms
            self.ids.exp_range_label.text = 'ms'
            self.exposure = 500
            self.min_exp = 100
            self.max_exp = 1000
            self.refreshExpSlider(2) 

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

    def refreshExpSlider(self, range):
        self.ids.exp_slider_label_min.text = self.exp_label_min[range-1]
        self.ids.exp_slider_label_max.text = self.exp_label_max[range-1]
        self.ids.exp_slider.min = self.min_exp
        self.ids.exp_slider.max = self.max_exp
        self.ids.exp_slider.value = self.exposure

    def updateExpSlider(self, value):
        self.exposure = value
        self.ids.exp_txt.text = str(int(self.exposure))
        
    # Callback for the checkbox 
    def autoExposure_click(self, instance, value): 
        if value == True:
            #auto calibrate and disable exposure input
            camWrap.setAutoExposure(True)
            self.ids.exp_slider.disabled = True
            self.ids.exp_up.disabled = True
            self.ids.exp_down.disabled = True
            self.ids.exp_range_select.disabled = True
        else: 
            #update the GUI values 
            self.exposure = int(camWrap.get_exposure()/1000)  #in milliseconds 
            self.ids.exp_range_select.disabled = False
            self.ids.exp_slider.disabled = False
            self.ids.exp_up.disabled = False
            self.ids.exp_down.disabled = False
            if self.exposure < 100:
                self.exposureRange_change(self.exp_range_values[0])
            else:
                self.exposureRange_change(self.exp_range_values[1])
            camWrap.setAutoExposure(False)

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

    def updateGainSlider(self, value):
        self.gain = value
        self.ids.gain_txt.text = str(int(self.gain))

    def autoGain_click(self, instance, value): 
        if value == True:
            #auto calibrate and disable exposure input
            camWrap.setAutoGain(True)
            self.ids.gain_slider.disabled = True
            self.ids.gain_up.disabled = True
            self.ids.gain_down.disabled = True
        else: 
            #update the GUI values 
            self.gain = camWrap.get_gain()  #in milliseconds 
            self.ids.gain_slider.disabled = False
            self.ids.gain_up.disabled = False
            self.ids.gain_down.disabled = False
            camWrap.setAutoGain(True)


    #######################  GENERAL CONTROLS  ####################
    # Take the config values and send them to the camera
    def backToCamera_release(self):
        if self.ids.gain_auto.active == False: #if not auto exposure 
            camWrap.set_gain(self.gain)
        if self.ids.exp_auto.active == False:  #it not auto gain
            camWrap.set_exposure(self.exposure, 'ms')
        
        self.manager.current = 'camera'  #switch screen
    
    
class PmiruApp(App):
    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(CameraScreen(name='camera'))
        self.sm.add_widget(ConfigScreen(name='config'))
        self.sm.add_widget(ViewerScreen(name='viewer'))
        return self.sm

    def on_start(self, **kwargs):
        if self.sm.current == 'camera':
            Clock.schedule_interval(self.sm.get_screen("camera").cameraRefreshCallback, 0.01)
        else:
            pass
        pass
        

# Rotate, change light and take picture
def takeHyperCube():
    camWrap.captureLoop(False) #for zwo camera is necessary to stop the video loop

    #for each slot, rotate to the right 
    if wheel is not None:
        nSlots = wheel.num_slots
    else:
        nSlots = 5

    folder = camWrap.getNewFolder()
    counter = 1
    while (nSlots > 0):
        if wheel is not None:
            wheel.rotateRight()
        time.sleep(1)  #wait for the rotation to finish  #TODO make it a GUI option
        fname = "img_" + format(counter, '02d') + ".jpg"
        camWrap.takeSingleShoot(path=folder, filename=fname)
        nSlots = nSlots -1
        counter = counter + 1

    camWrap.saveControlValues(path=folder, filename="controlValues.txt")
    camWrap.captureLoop(True)


if __name__ == "__main__":
    
    camWrap = camWrap() 
    cubeFolders, cubeFiles = camWrap.getCubesList()

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