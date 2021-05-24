import PyIndi
import time
 
class WheelControl(PyIndi.BaseClient):

    def __init__(self):
        self.cmonitor = None 
        self.dmonitor = None 
        self.newval = None 
        self.prop = None
        self.monitored = "ASI EFW"
        self.slot = None 
        self.num_slots = 5
        
        super(WheelControl, self).__init__()
    
    def newDevice(self, d):
        # We catch the monitored device
        self.dmonitor=d
        print("New device ", d.getDeviceName())
    def newProperty(self, p):
        
        # we catch the "CONNECTION" property of the monitored device
        if (p.getDeviceName()==self.monitored and p.getName() == "CONNECTION"):
            self.cmonitor=p.getSwitch()
        print("New property ", p.getName(), " for device ", p.getDeviceName())
    def removeProperty(self, p):
        pass
    def newBLOB(self, bp):
        pass
    def newSwitch(self, svp):
        pass
    def newNumber(self, nvp):
        # We only monitor Number properties of the monitored device
        self.prop=nvp
        self.newval=True
    def newText(self, tvp):
        pass
    def newLight(self, lvp):
        pass
    def newMessage(self, d, m):
        pass
    def serverConnected(self):
        pass
    def serverDisconnected(self, code):
        pass
 
 
    def connect(self, host, port, name, num):
        self.num_slots = num
        self.setServer(host,port)
        
        # we are only interested in the telescope device properties
        self.watchDevice(name)
        self.connectServer()
        
        # repeat until you can connect
        while not(self.cmonitor):
            time.sleep(0.05)

        # if the monitored device is not connected, we do connect it
        if not(self.dmonitor.isConnected()):
            # Property vectors are mapped to iterable Python objects
            # Hence we can access each element of the vector using Python indexing
            # each element of the "CONNECTION" vector is a ISwitch
            self.cmonitor[0].s=PyIndi.ISS_ON  # the "CONNECT" switch
            self.cmonitor[1].s=PyIndi.ISS_OFF # the "DISCONNECT" switch
            self.sendNewSwitch(self.cmonitor) # send this new value to the device
            print("d")

        self.slot = self.getCurrentSlot()

    def isConnected(self):
        return self.dmonitor.isConnected()

    def rotateLeft(self):
        next_slot = self.slot
        next_slot[0].value = next_slot[0].value - 1
        if next_slot[0].value == 0:
            next_slot[0].value = self.num_slots
        self.sendNewNumber(next_slot)
        time.sleep(1)

    def rotateRight(self): 
        next_slot = self.slot
        next_slot[0].value = next_slot[0].value + 1
        if next_slot[0].value > self.num_slots:
            next_slot[0].value = 1
        self.sendNewNumber(next_slot)
        time.sleep(1)

    def rotateTo(self, num):
        self.sendNewNumber(num)
        time.sleep(1)

    def getCurrentSlot(self):
        cur_slot = None
        cur_slot = self.dmonitor.getNumber("FILTER_SLOT")
        while not(cur_slot):
            print("failed getting slot number...")
            time.sleep(1)
            cur_slot = self.dmonitor.getNumber("FILTER_SLOT")

        return cur_slot

    def getSlot(self):
        s = self.getCurrentSlot()
        return s[0].value




# get the number of wheel slots

# print (num_slots)

# self.newval=False
# self.prop=None
# nrecv=0
# while (nrecv<10):
#     # we poll the newval global variable
#     if (self.newval):
#         print("newval for property", prop.name, " of device ",self.prop.device)
#         # prop is a property vector, mapped to an iterable Python object
#         for n in self.prop:
#             # n is a INumber as we only monitor number vectors
#             print(n.name, " = ", n.value)
#         nrecv+=1
#         self.newval=False
 