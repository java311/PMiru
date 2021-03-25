import pigpio
import time

class Motor():
    def __init__(self, gpio_pin=12):
        self.PIN = gpio_pin
        self.pi = pigpio.pi()
        self.pi.set_mode(self.PIN, pigpio.OUTPUT)
        self.index = 0

    #For Fuataba angle goes from -144 to 144
    def moveTo(self, angle, sleep=0.3):
        duty = int((333.34 * angle) + 76000)  #lineal approx formula for FUTABA PWM motor !!!
        print ('Moving to... angle: ' + str(angle) + ' dc value: ' + str(duty))  #DEBUG
        self.pi.hardware_PWM(self.PIN, 50, duty )  # Changing the Duty Cycle to rotate the motor   
        time.sleep(sleep) 

    #alist MUST be a list of integers 
    def initAngles(self, alist):
        self.angleList = alist

    def movetoInit(self):
        self.moveTo(self.angleList[0])

    # index must be an angleList valid index
    def moveToAngle(self, index, sleep=0.3):
        if index > 0 and index < len(self.angleList): 
            self.moveTo(self.angleList[index])    

    # rotate to next angle 
    def moveToNextAngle(self, sleep=0.3):
        self.index =  self.index + 1
        if self.index == len(self.angleList):
            self.index = 0

        self.moveTo(self.angleList[self.index])
        return self.index
    
    def getNumAngles(self):
        return len(self.angleList)

    def getAngle(self,index):
        return self.angleList[index]

    def __del__(self):
        self.pi.set_mode(self.PIN, pigpio.INPUT)
        self.pi.stop() 
        