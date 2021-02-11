import octofet
from wheel_control import WheelControl

wheel=WheelControl()
wheel.connect("localhost",7624,"ASI EFW",5)
wheel.rotateLeft()
