import time
import json
import os
from libs.octofet import Octofet
from sys import platform

# TODO link the color dictionary [channel, device, index] of each color to the UI 
class ledControl():
    def __init__(self, ceNum=2, nboards=2, bus=1):

        ceNum=0; nboards=0; bus=0
        if os.uname()[4] == 'armv7l':           #For Raspberry 4B
            ceNum=2; nboards=2; bus=1
        elif os.uname()[4] == 'aarch64':   #For Jetson nano
            ceNum=0; nboards=2; bus=0

        # inits Octofet controler class. CE number, Number of Amperka boards, bus number (bus SPI0 or SPI1)
        self.octo = Octofet(ceNum,nboards,bus=bus)
        self.cindex = 0  # index by color 

        # Wavelenghts in building order. 
        #Yellow, Violet, White, Red, Green, Blue, DeepBlue, DeepRed, Inf 740, Inf 850, Inf 940
        # self.waveLenghts = [590,400,8000,620,520,460,390,660,740,850,940]  
        # self.colors = [[0,0],[1,0],[2,0],[3,0],[4,0],[5,0],[6,0],[7,0], [0,1],[1,1],[2,1] ]
        # self.nColors = len(self.colors)

        # Initilize wavelenghts, led conections and indexes
        self.waveLenghts = []
        self.colors = []
        self.zwo_exp = []
        self.zwo_gain = []
        self.baumer_exp = []
        self.baumer_gain = []
        with open('config.json') as cfile:
            cfg = json.load(cfile)
            for c in cfg['lights']:
                self.waveLenghts.append(c['wavelenght'])
                self.colors.append( [ c['channel'] ,  c['device'] ]  )
                self.zwo_exp.append( c['zwo-exp'] )
                self.zwo_gain.append( c['zwo-gain'] )
                self.baumer_exp.append( c['baumer-exp'] )
                self.baumer_gain.append( c['baumer-gain'] )
            self.nColors = len(cfg['lights'])

    # Turns ON a led using color index in colors list
    def colorOnOff(self, color_index, val=True, wait=1):
        ch = self.colors[color_index][0] # get channel
        dev = self.colors[color_index][1] # get device
        self.octo.digital_write(channel=ch, value=val,  device=dev)
        time.sleep(wait)

    # Rotates colors list turning ON and OFF every listed led
    def rotateLight(self):
        ch = self.colors[self.cindex][0] # get channel
        dev = self.colors[self.cindex][1] # get device

        state = self.octo.get_channel_state(ch, dev)
        if state == True:  # If ON turn OFF
            self.octo.digital_write(channel=ch, value=False, device=dev)
            
            self.cindex = self.cindex + 1
            if self.cindex >= self.nColors:
                self.cindex = 0

        else:   # If OFF turn ON
            self.octo.digital_write(channel=ch, value=True, device=dev)

    # Giving the index and device numbers shuffles the state of the LED
    def lightShuffle(self, ch=2, dev=0):
        state = self.octo.get_channel_state(ch, dev)
        state = not state
        self.octo.digital_write(channel=ch, value=state, device=dev)
        time.sleep(0.3)

    # Return the wavelenght value of the LED
    def getWavelenght(self, index):
        return self.waveLenghts[index]

    # Return the [exposure, gain] values read from JSON config file
    def getColorExpGain(self, camType, index):  
        if camType == 'zwo':  # for zwo
            return [self.zwo_exp[index], self.zwo_gain[index]]
        elif camType == 'baumer': # for baumer
            return [self.baumer_exp[index], self.baumer_gain[index]]
        else:
            return [self.zwo_exp[index], self.zwo_gain[index]]

    # Turn all LEDs OFF (called on closing)
    def lightsOff(self, wait=1):
        allOff = [False,False,False,False,False,False,False,False]
        self.octo.digital_write_all(value=allOff, device=0) # Amperka board 1 ALL OFF
        self.octo.digital_write_all(value=allOff, device=1) # Amperka board 2 ALL OFF
        print ("Lights OFF...")
        time.sleep(wait)









    