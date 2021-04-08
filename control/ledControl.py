import time
from libs.octofet import Octofet

# TODO link the color dictionary [channel, device, index] of each color to the UI 
class ledControl():
    def __init__(self, ceNum=2, nboards=2, bus=1):
        # inits Octofet controler class. CE number, Number of Amperka boards, bus number (bus SPI0 or SPI1)
        self.octo = Octofet(ceNum,nboards,bus=bus)
        self.cindex = 0  # index by color
        
        # Wavelenghts in building order. 
        #Yellow, Violet, White, Red, Green, Blue, DeepBlue, DeepRed, Inf 740, Inf 850, Inf 940
        self.waveLenghts = [590,400,8000,620,520,460,390,660,740,850,940]  
        self.colors = [[0,0],[1,0],[2,0],[3,0],[4,0],[5,0],[6,0],[7,0], [0,1],[1,1],[2,1] ]
        self.nColors = len(self.colors)

    # Turns ON a led using color index in colors list
    def colorOnOff(self, color_index, val=True):
        ch = self.colors[color_index][0] # get channel
        dev = self.colors[color_index][1] # get device
        self.octo.digital_write(channel=ch, value=val,  device=dev)

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

    def getWavelenght(self, index):
        return self.waveLenghts[index]








    