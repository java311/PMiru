import time
from octofet import Octofet

class ledControl():
    def __init__(self, ce=2, nboards=2, bus=1):
        # inits Octofet controler class. CE number, Number of Amperka boards, bus number (bus SPI0 or SPI1)
        self.octo = Octofet(ce,nboards,bus=bus)
        self.ch = 0
        self.dev = 0
    
    def nextColorON(self):
        self.ch = self.ch + 1
        if self.ch > 7 and self.dev == 0:
            self.ch = 0
            self.dev = 1
        if self.ch > 1 and self.dev == 1:
            self.ch = 0
            self.dev = 0

        self.octo.digital_write(channel=self.ch, value=True,  device=self.dev)

    def nextColorOFF(self):
        self.octo.digital_write(channel=self.ch, value=False,  device=self.dev)






    