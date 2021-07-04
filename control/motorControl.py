import pigpio
import time

class Motor():
    def __init__(self, gpio_pin=12):
        self.PIN = gpio_pin
        self.pi = pigpio.pi()
        self.pi.set_mode(self.PIN, pigpio.OUTPUT)
        self.start_angle = 0
        self.index = 0
        self.calib_index = 0

    #For Fuataba angle goes from -144 to 144
    def moveTo(self, angle, sleep=0.3):
        duty = int((333.34 * angle) + 76000)  #lineal approx formula for FUTABA PWM motor !!!
        print ('Moving to... angle: ' + str(angle) + ' dc value: ' + str(duty))  #DEBUG
        self.pi.hardware_PWM(self.PIN, 50, duty )  # Changing the Duty Cycle to rotate the motor   
        time.sleep(sleep) 

    #receives the start and step to build angles list
    def initAngles(self, start_angle, step_angle):
        self.start_angle = start_angle
        self.step_angle = step_angle
        motor_angles = range(self.start_angle, 144, self.step_angle)
        self.angleList = motor_angles

    def initCalibAngles(self, step_calib):
        calib_angles = range(-144,144,step_calib)
        self.calibAngles = calib_angles
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

    def getAngle(self,index):
        return self.angleList[index]

    def __del__(self):
        self.pi.set_mode(self.PIN, pigpio.INPUT)
        self.pi.stop() 
        