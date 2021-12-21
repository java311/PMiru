# Install instructions for Jetson Nano

## Install general dependencies tools
```
install pip3
apt get install python3-pip

install cython
pip install -U cython 

install numpy and tifffile  (-U means --update)
pip3 install -U numpy 
pip3 install -U tifffile 
```

## OpenCV
Install Open CV using pip3, to avoid compiling source code. 

First install dependencies   

`pip3 install scikit-build`

Then install OpenCV using pip. 

`pip3 install opencv-python`

It is necessary to install contrib version for superpixel support
`pip3 install opencv-contrib-python`

Be patient this step takes a lot of time

Then install the OpenCV dependencies 
```
sudo apt-get install libatlas-base-dev
sudo apt-get install libhdf5-dev
sudo apt-get install libhdf5-serial-dev
sudo apt-get install libatlas-base-dev
sudo apt-get install libjasper-dev
sudo apt-get install libqtgui4 
sudo apt-get install libqt4-test
```

Also it is necessary to install polanalyser for the superpixel segmentation:
`pip install git+https://github.com/elerac/polanalyser`

## Kivy
The best is to install it from apt
https://kivy.org/doc/stable/installation/installation-linux.html#start-from-the-command-line

### SDL Kivy bug
There is a bug related do the SDL (https://github.com/kivy/kivy/issues/6007), that can only be fixed by installing an updated version of SDL by compiling the source code. Please follow this instructions: https://github.com/dhewm/dhewm3/issues/335#issuecomment-750332678

Once you have compiled SDL, you must link the compiled libraries by adding the following line to  `~/.bashrc` :

`export LD_LIBRARY_PATH=/home/pmiru/tmp/SDL2-2.0.8/build`

### Pillow Kivy bug 
Kivy has a problem when trying to render fonts uising Free Type fonts. To solve this problem, first install the free type development package:

`sudo apt-get install libfreetype6-dev`

Then reinstall Pillow 

```
$ sudo apt-get install libfreetype6-dev
$ pip uninstall pillow
$ pip install --no-cache-dir pillow
```

( Instructions taken from: https://stackoverflow.com/questions/4011705/python-the-imagingft-c-module-is-not-installed )


## Install ZWO libraries 
`pip3 install zwoasi`

Then it is necessary to install ASIO C++ binary library, from INDI-lib repositories (https://indilib.org/download.html):

```
sudo apt-add-repository ppa:mutlaqja/ppa
sudo apt-get update
sudo apt-get install indi-full gsc
```

## Install Octofet dependencies
```
pip3 install -U spidev
pip3 install -U pigpio
```

## Install jetston-GPIO libraries 
pigpio doesnt work in jetson nano, so it is necessary to use Jetson GPIO libraries insteadl 

`sudo pip install Jetson.GPIO`

Also follow the instructions of the git hub webpage (https://github.com/NVIDIA/jetson-gpio), because daemon and groups need further configuration


After this use Jetpack script to activate PWM and SPI pins 

`sudo /opt/nvidia/jetson-io/jetson-io.py`

To activate SPI is necessary to start the spidev kernel module automatically, by adding `spidev` it to the `/etc/modules` file.


## Connections

### How to connect the PWM

| Servo Motor PIN  | Jetson PIN  |
| ------------- | ------------- |
| 5 Volt   | PIN 4  |
| GND   | PIN 6  |
| COMM   | PIN 33  |

### Conenct Amperka boards

| Amperka  | Jetson PIN |
| ------------- | ------------- |
| pulse icon pin   | PIN 23  (SLCK) |
| G (Ground) | PIN 25 (GND)  |
| DI   | PIN 19 (MOSI SPI1) |
| CS   | PIN 24 (SPI CS0) |
| pin between GND and Clock (5V)   | PIN 2 (5V) |

#### LED connection troubleshoot
- Issue: Leds turn on at the same or in the wrong order
- Fix: It is caused by a missconnection of the CS cable on the wrong pin.

- Issue: Amperka LED do not turn on and also LEDs do not turn on
- Fix: The 5V from the Jetson board is not connected to Amperka board

- Issue: Amperka LED is ON but LEDs do not turn on
- Fix: The 3.3v power supply is not connected to the Amperka board





