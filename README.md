# P-MIRU
An Open Source hyperspectral polarized light camera. 

![](https://i.ibb.co/4tCZpwy/img-20210320-wa0007.jpg)

## User Guide

### How to use the camera 

#### Turn ON and start the sofware


#### Graphical User Interface


#### Use the camera with monitor and mouse


#### Use the camera with touch screen only 


#### How to transfer the photos to my PC ?


### How to connect the camera

#### Touch Screen connections
The touchscreen must be connected to the Raspberyy using SPI0, 3.3V, 5V, ground and plus touch communication pins.
Here are the PINs configuration: 

| PIN Function  | Raspbery-LCD PIN number |
| ------------- | ------------- |
| 5 Volt   | PIN 2  |
| 3.3 Volt   | PIN 1  |
| SPI0 and COMMs   | PINs 18, 19, 20, 21, 22, 23, 24, 26  |

LCD PIN numbers are the same as the Raspberry. 
Just check the orientation of the LCD PIN slot, it is designed to cover all the Raspberry output pins.

![](https://i.ibb.co/m00sgT8/pitft-pinout.png)

#### LED control boards connections (Amperka)
The camera has two control boards to control the LEDs. This is where the cables from the 
LED plates are connected. Also the boards need to be connected to the Raspberry PINs. 

The first control board is connected to the Raspberry using the following PINs: 
| Control Board IN  | Raspberry PINs |
| ------------- | ------------- |
| pulse icon pin   | PIN 40  (SLCK) |
| G (Ground) | PIN 39 (GND)  |
| DI   | PIN 38 (MOSI SPI1) |
| CS   | PIN 36 (SPI CE2) |
| pin between GND and Clock (5V)   | PIN 2 (5V) |

![](https://maker.pro/storage/g9KLAxU/g9KLAxUiJb9e4Zp1xcxrMhbCDyc3QWPdSunYAoew.png)

Then the fist board OUT must connected the the second control board IN.
To connect them togheter, just connect the SPI OUT of the first board to the same PINS on the SPI IN pins of the second board. 

| First board OUT  | Second board IN |
| ------------- | ------------- |
| Pulse icon pin   | Pulse icon pin (SLCK) |
| G (Ground) | G (Ground)  |
| pin between GND and Clock (5V) | pin between GND and Clock (5V) |
| DI (MOSI) | DI (MOSI) |
| CS (CS)  | CS (CS) |

The LEDs blades cables must be connetected to the numbered outputs of the boards.
The cables are numbered, just connect them in the following order:

| LED cable num.  | Control Board port | Control Board number | 
| ------------- | ------------- | ------------- |
| cable 0  | + port 0 | board 1 |
| cable 1  | + port 1 | board 1 | 
| cable 2  | + port 2 | board 1 |
| cable 3  | + port 3 | board 1 | 
| cable 4  | + port 4 | board 1 |
| cable 5  | + port 5 | board 1 | 
| cable 6  | + port 6 | board 1 |
| cable 7  | + port 7 | board 1 | 
| cable 8  | + port 8 | board 1 |
| GROUND cable  | any - port | board 1 |
| cable 9  | + port 0 | board 2 |
| cable 10  | + port 1 | board 2 |
| cable 11  | + port 2 | board 2 | 

This is the default order, but you can alter this order by editing the config.json file. 

#### Motor connections
The motor gets power from the second board, but it is controlled directly from the Raspberry. 
So, it must be connected the following way: 

| Motor  | Connection |
| ------------- | ------------- |
| 5 Volt   | Control board 2 PIN between CS and GND |
| Ground   | COntrol board 2 GND PIN |
| Comm    | Raspberry PIN 32 (PWM0)  |

#### Camera connection
The camera is connected using a USB 2 or USB 3 cable. 
Just follow the colors in the ports. Very easy. 


### Troubleshooting

#### The software got freezed


#### The program freeze or stoped and the LEDs are ON


#### The autocalibration gets stuck in a single color


#### When taking photos the progress bar restarts several times 

#### 