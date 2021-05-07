# P-MIRU
An Open Source hyperspectral polarized light camera. 

![](https://i.ibb.co/4tCZpwy/img-20210320-wa0007.jpg)

## Install instructions for Raspberry

These instructions are for a Raspberry fresh install. 

### Install Numpy
`pip3 install numpy`

### Install OpenCV 3
use pip3 (it musb be pip3) as: 
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

(note. the rotation of the screen must be the same as indicated in Raspbery script) 

Also in the `[graphics]` section modify width and height parameters to 320, 240 respectevely.
And then Reboot

#### Touchscreen connection pins
The touchscreen must be connected to the Raspberyy suing SPI0, plus 3.3V, 5V, ground. 
And other GPIO pins with unknown usability. Here are the PINS: 
(pin number are normal PIN numbers not GPIO)
| Function  | PIN GPIO number |
| ------------- | ------------- |
| 5 Volt   | PIN 2  |
| 3.3 Volt   | PIN 17  |
| SPI pins GND and extras   | PINs 19, 20, 21, 22, 23, 24  |

![](https://maker.pro/storage/g9KLAxU/g9KLAxUiJb9e4Zp1xcxrMhbCDyc3QWPdSunYAoew.png)

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
Then connect Amperka boards using the following configuration: 
| Amperka  | Raspberry GPIO |
| ------------- | ------------- |
| pulse icon pin   | SLCK      PIN 40  |
| Ground   | GND       PIN 39  |
| DI   | MOSI SPI1 PIN 38  |
| CS   | SPI CE2   PIN 36  |
| pin between GND and Clock (5V)   | 5V        PIN 2  |

![](https://maker.pro/storage/g9KLAxU/g9KLAxUiJb9e4Zp1xcxrMhbCDyc3QWPdSunYAoew.png)

(the boards had been hacked to work with 3.3Volts) 
with the purple cables soldered on each of the boards. 

To control the 10 colors, it is necessary to have two Amperka boards connected to each other using SPI.
Just use jumper camples to connect the SPI output to the SPI input with the correspondant PINs on the other board.
(Do not forget to connect the 5V hacked PIN)

### Motor (PWM daemon) 
Motors are controlled using PWM. pigpio demon needs to be started as a daemon on every boot. 
To do so, use the following commands:
```
$ sudo systemctl enable pigpiod.service
$ sudo shutdown -r now
```

Then check if everything is OK by using 
`$ sudo systemctl status pigpiod.service`

### Finally 
Go to the folder where P-Miru is and excecute it using this command: 
`python3 pmiru.py -m` to star it maximized or without options for normal startup

### Optional
Switch beteen python2 to python3. 
So when you call python you use python 3. 
