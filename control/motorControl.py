import pigpio            # pwm for Raspberry
import RPi.GPIO as GPIO  # pwm for Jetson
import time
import os

class Motor():
    def __init__(self):
        # Identify the hardware 
        self.jetson = False   #Jetson or Raspberry
        if os.uname()[4] == 'aarch64':
            self.jetson = True

        self.PIN = 12
        self.pi = None
        if self.jetson:  # For Jetson Nano
            self.PIN = 33
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.PIN, GPIO.OUT)
            self.pi = GPIO.PWM(self.PIN, 50)
            self.pi.start(10)
        else:            # For Raspberry      
            self.pi = pigpio.pi()
            self.pi.set_mode(self.PIN, pigpio.OUTPUT)

        self.start_angle = 0
        self.stop_angle = 0
        self.index = 0
        self.calib_index = 0

    #For Fuataba angle goes from -144 to 144
    def moveTo(self, angle, sleep=0.3):
        duty = (333.34 * angle) + 76000  #lineal approx formula for FUTABA PWM motor !!!
        print ('Moving to... angle: ' + str(angle) + ' dc value: ' + str(duty))  #DEBUG
        if self.jetson:
            duty = (duty * 100) / 1000000
            print (duty)
            print (int( 20000000 * duty / 100.0))
            self.pi.ChangeDutyCycle(duty)
        else:
            self.pi.hardware_PWM(self.PIN, 50, int(duty) )  # Changing the Duty Cycle to rotate the motor   
        time.sleep(sleep) 

    #receives the start and step to build angles list
    def initAngles(self, start_angle, stop_angle, step_angle):
        self.start_angle = start_angle
        self.stop_angle = stop_angle
        self.step_angle = step_angle
        self.angleList = range(self.start_angle, self.stop_angle, self.step_angle)

    def initCalibAngles(self, step_calib):
        self.calibAngles = range(-144,144,step_calib)
        for i,a in enumerate(self.calibAngles):
            if a >= self.start_angle:
                self.calib_index = i
                break

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

    # Moves the lens in small steps to calibrate the camera
    def moveCalibAngle(self, up, sleep=0.3):
        if up == True: 
            self.calib_index =  self.calib_index + 1
        else:
            self.calib_index =  self.calib_index - 1

        if self.calib_index == len(self.calibAngles):
            self.calib_index = 0
        if self.calib_index < 0:
            self.calib_index = len(self.calibAngles) -1

        self.moveTo(self.calibAngles[self.calib_index])
        return self.calibAngles[self.calib_index]

    def getNumAngles(self):
        return len(self.angleList)

    # Returns real polarizer angle in a string for the image name format
    def getRealAngle(self,index):
        return format(90 + (self.angleList[index] - self.start_angle) , '02d')
        # return self.angleList[index] - start_angle
        # return self.angleList[index]

    def motorOff(self):
        if self.jetson:
            self.pi.stop()
            GPIO.cleanup()
            print ("(Jetson) Motor OFF...")
        else:
            self.pi.set_mode(self.PIN, pigpio.INPUT)
            self.pi.stop() 
            print ("(Rasp) Motor OFF...")
        