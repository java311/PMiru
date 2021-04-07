import time
from libs.octofet import Octofet

# TODO link the color dictionary [channel, device, index] of each color to the UI 
class ledControl():
    def __init__(self, ceNum=2, nboards=2, bus=1):
        # inits Octofet controler class. CE number, Number of Amperka boards, bus number (bus SPI0 or SPI1)
        self.octo = Octofet(ceNum,nboards,bus=bus)
        self.ch = 0
        self.dev = 0
        self.nColors = 10 # BY NOW manually set number of colors  
        self.whiteLight = False # Flag to control the white light 
        # Wavelenghts in building order. 
        #Yellow, Violet, White, Red, Green, Blue, DeepBlue, DeepRed, Inf 740, Inf 850, Inf 940
        self.waveLenghts = [590,400,8000,620,520,460,390,660,740,850,940]  

    def nextColorON(self):
        self.ch = self.ch + 1
        if self.ch > 7 and self.dev == 0:
            self.ch = 0
            self.dev = 1
        if self.ch > 1 and self.dev == 1:
            self.ch = 0
            self.dev = 0

        self.octo.digital_write(channel=self.ch, value=True,  device=self.dev)
        time.sleep(0.3)

    def nextColorOFF(self):
        self.octo.digital_write(channel=self.ch, value=False,  device=self.dev)
        time.sleep(0.3)

    def whiteLightShuffle(self):
        self.whiteLight = not self.whiteLight
        self.octo.digital_write(channel=2, value=self.whiteLight, device=0)
        time.sleep(0.3)

    def getWavelenght(self, index):
        return self.waveLenghts[index]








    