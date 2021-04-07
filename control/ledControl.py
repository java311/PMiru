import time
from libs.octofet import Octofet

# TODO link the color dictionary [channel, device, index] of each color to the UI 
class ledControl():
    def __init__(self, ceNum=2, nboards=2, bus=1):
        # inits Octofet controler class. CE number, Number of Amperka boards, bus number (bus SPI0 or SPI1)
        self.octo = Octofet(ceNum,nboards,bus=bus)
        self.ch = 0  # Channel index 
        self.dev = 0 # Device index
        self.nColors = 10 # BY NOW manually set number of colors  
        # Wavelenghts in building order. 
        #Yellow, Violet, White, Red, Green, Blue, DeepBlue, DeepRed, Inf 740, Inf 850, Inf 940
        self.waveLenghts = [590,400,8000,620,520,460,390,660,740,850,940]  

    # turns the LED following the channel and device order
    def nextColorON(self):
        self.octo.digital_write(channel=self.ch, value=True,  device=self.dev)
        time.sleep(0.3)

    # turns the current LED off (nextColorON MUST be called before calling this function)
    def nextColorOFF(self):
        self.octo.digital_write(channel=self.ch, value=False,  device=self.dev)
        time.sleep(0.3)

        self.ch = self.ch + 1
        if self.ch > 7 and self.dev == 0:
            self.ch = 0
            self.dev = 1
        if self.ch > 1 and self.dev == 1:
            self.ch = 0
            self.dev = 0

    # Init ch and dev indices to their intial values
    def initIndices(self):
        self.ch = 0
        self.dev = 0

    # Giving the index and device numbers shuffles the state of the LED
    def lightShuffle(self, ch=2, dev=0):
        state = self.octo.get_channel_state(ch, dev)
        state = not state
        self.octo.digital_write(channel=ch, value=state, device=dev)
        time.sleep(0.3)

    def getWavelenght(self, index):
        return self.waveLenghts[index]








    