# P-MIRU
An Open Source hyperspectral polarized light camera. 

![](https://i.ibb.co/4tCZpwy/img-20210320-wa0007.jpg)

## Install instructions for Raspberry

These instructions are for a Raspberry fresh install. 

### Install Numpy and Tifffile
```
pip3 install numpy
pip3 install tifffile
```

### Install OpenCV 3
use pip3 (it MUST be pip3) as: 
`pip3 install opencv-python`

Then install all OpenCV dependencies:
```
sudo apt-get install libatlas-base-dev
sudo apt-get install libhdf5-dev
sudo apt-get install libhdf5-serial-dev
sudo apt-get install libatlas-base-dev
sudo apt-get install libjasper-dev
sudo apt-get install libqtgui4 
sudo apt-get install libqt4-test
```

### Install Kivy
First install Kivy dependencies: 
`sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev`
then install kivy using pip3 
`python3 -m pip install kivy[base] `

Add the following to `~/.bashrc` to disable Kivy default arguments:
```
# disable kivy command line for pmiru
KIVY_NO_ARGS=1
export KIVY_NO_ARGS
```

### Install ZWO libraries
`pip3 install zwoasi`

Then it is necessary to install ASIO C++ binary library, from Astroberry PI repositories:
```
wget -O - https://www.astroberry.io/repo/key | sudo apt-key add -
sudo su -c "echo 'deb https://www.astroberry.io/repo/ buster main' > /etc/apt/sources.list.d/astroberry.list"
sudo apt update
sudo apt upgrade
sudo apt-get install indi-full
```

### Install NeoApi (Baumer) 
Neoapi is installed by downloading the WHL python packages from Baumer site: 
https://www.baumer.com/us/en/product-overview/industrial-cameras-image-processing/software/baumer-neoapi/c/42528

Download Baumer neoAPI Python v1.0 (Linux ARM)  (armhf, tar.gz option)

Then install the whl file accordingly to your python3 version:
```
python3 --version
python3 -m pip install neoapi-1.0.0-py[your python version]-none-any.whl
```

Also it is necessary to increase the USB cache size of Raspberry. To do so add this line to `/etc/rc.local`. Before the `exit 0`, add this: 
```
sudo sh -c 'echo 1024 > /sys/module/usbcore/parameters/usbfs_memory_mb' &
```

### Touch Screen Install
These are the instructions for the touch screen install
Use the following comands:  (taken from: https://learn.adafruit.com/adafruit-pitft-3-dot-5-touch-screen-for-raspberry-pi/easy-install-2 )
```
cd ~
sudo pip3 install --upgrade adafruit-python-shell click==7.0
git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git
cd Raspberry-Pi-Installer-Scripts
```

Run Adafruit configuration script, with:
`sudo python3 adafruit-pitft.py `
and select the following options:
[4] [90 degrees] [No] [Yes] and DO NOT reboot. 

Also, Kivy needs special instructions to control the touch screen. 
Edit `~/.kivy/config.ini` and add the following lines in the [input] section:
```
[input]
mouse = mouse
mtdev_%(name)s = probesysfs,provider=mtdev
hid_%(name)s = probesysfs,provider=hidinput,param=rotation=90,param=invert_y=1
```

(NOTE: the rotation of the screen must be the same as indicated in Raspbery script) 

Also in the `[graphics]` section modify width and height parameters to 320, 240 respectevely.
And then Reboot

(NOTE: If you are going to use the camera without the touch screen, with mouse and keyboard.
Then the last two must be commented. Otherwise, Kivy will register ghost and random clicks. )

#### Touchscreen connection pins
The touchscreen must be connected to the Raspberyy using SPI0, 3.3V, 5V, Ground and 2 communications PINS 
Here are the PINs configuration: 

| PIN Function  | Raspbery-LCD PIN number |
| ------------- | ------------- |
| 5 Volt   | PIN 2  |
| 3.3 Volt   | PIN 1  |
| SPI0 and COMMs   | PINs 18, 19, 20, 21, 22, 23, 24, 26  |

LCD PIN numbers are the same as the Raspberry. 
Just check the orientation of the LCD PIN slot, it is designed to cover all the Raspberry output pins.

![](https://i.ibb.co/m00sgT8/pitft-pinout.png)

### Amperka board install (light control)
(Amperka python libraries were modified, so these are include in source code. There is no need to install them)
Since we are using SPI0 for the touchscreen, the light control boards must be connected using SPI1. 
First it is necesasry to enable SPI interface using sudo raspi-config. Then after reboot it is necessary
to enable SP1 too by editing `/boot/config.txt` and add the follwoing line:

`dtoverlay=spi1-3cs`

And then reboot. 
To check if SPI is activated excecute: `ls /dev/spi*`. The command output must be: 
```
pi@raspberrypi:~/PMiru $ ls /dev/spi*
/dev/spidev1.0  /dev/spidev1.1  /dev/spidev1.2
```

#### Amperka boards connection pins
Then connect Amperka board #0 with the Raspberry using the following PIN configuration: 
| Amperka  | Raspberry PIN |
| ------------- | ------------- |
| pulse icon pin   | PIN 40  (SLCK) |
| G (Ground) | PIN 39 (GND)  |
| DI   | PIN 38 (MOSI SPI1) |
| CS   | PIN 36 (SPI CE2) |
| pin between GND and Clock (5V)   | PIN 2 (5V) |

![](https://maker.pro/storage/g9KLAxU/g9KLAxUiJb9e4Zp1xcxrMhbCDyc3QWPdSunYAoew.png)

(The boards had been hacked to work with 3.3Volts 
with the cables soldered on each of the boards. Do not dissconnect them ! ) 

To control the 10 colors, it is necessary to have 2 Amperka boards connected to each other using SPI.
To connect them togheter, use jumper cables to connect the SPI output of board #0 to the same PINS of the SPI input in board #1
Connect all the 6 pins of SPI-Out (board #0) to the SPI-In (board #1) 

### Motor (PWM daemon) 
Motors are controlled using PWM. pigpio demon needs to be started as a daemon on every boot. 
To do so, use the following commands:
```
$ sudo systemctl enable pigpiod.service
$ sudo shutdown -r now
```
Then check if everything is OK by using 
`$ sudo systemctl status pigpiod.service`

Motor PINs are connected as follows: 
| Motor  | Amperka Board #2 |
| ------------- | ------------- |
| 5 Volt   | Amperka OUT between CS and GND |
| Ground   | Amperka OUT GND       PIN 39  |
| Comm    | Raspberry PIN 32 (PWM0)  |

### Finally 
Go to the folder where P-Miru is and excecute it using this command: 
`python3 pmiru.py -m` to star it maximized or without options for normal startup

### Optional
Set python3 as default (so when you call python you call python3 instead of python2)
https://linuxconfig.org/how-to-change-from-default-to-alternative-python-version-on-debian-linux