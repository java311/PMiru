import pigpio
import time

class Motor():
    def __init__(self, gpio_pin=12):
        self.PIN = gpio_pin
        self.pi = pigpio.pi()
        self.pi.set_mode(self.PIN, pigpio.OUTPUT)

    #For Fuataba angle goes from -144 to 144
    def moveTo(self, angle, sleep=0.3):
        duty = int((333.34 * angle) + 76000)  #lineal approx formula for FUTABA PWM motor !!!
        # print ('angle: ' + str(angle) + ' dc value: ' + str(duty))  #DEBUG
        self.pi.hardware_PWM(self.PIN, 50, duty )  # Changing the Duty Cycle to rotate the motor   
        time.sleep(sleep) 

    #alist MUST be a list of integers 
    def initAngles(self, alist):
        self.angleList = alist
        self.iAngle = 0

    def movetoInit(self):
        self.moveTo(self.angleList[0])

    def moveToNextAngle(self, sleep=0.3):
        self.moveTo(self.angleList[self.iAngle],sleep)
        self.iAngle = self.iAngle + 1
        if self.iAngle > len(self.angleList)-1:
            self.iAngle = 0

    def moveToPrevAngle(self, sleep=0.3):
        self.moveTo(self.angleList[self.iAngle],sleep)
        self.iAngle = self.iAngle - 1
        if self.iAngle < 0:
            self.iAngle = len(self.angleList)-1

    def getNumAngles(self):
        return len(self.angleList)

    def getCurAngle(self):
        return self.angleList[self.iAngle]

    def __del__(self):
        self.pi.set_mode(self.PIN, pigpio.INPUT)
        self.pi.stop() 
        