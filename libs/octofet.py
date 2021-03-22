"""The module contains the Octofet class, which allows you to communicate with
a particular Octofet board. One Octofet board provides 8 power switches also
known as "channels".
This module requires that `spidev` be installed within the Python environment
you are using it.
"""

import spidev


class Octofet:
    """Class for 8-channel Octofet board.

    Methods:
    --------
    digital_write(channel: int, value: bool, device: int = 0) -> None
        Sets the state ("on" or "off") of one power switch.

    digital_write_all(value: List[bool], device: int = 0) -> None
        Sets the state ("on" or "off") of all power switches at once.

    get_channel_state(channel: int, device: int = 0) -> bool
        Returns the last (i.e., current) set state for one power switch of the
        device. Returns True if turned on or False otherwise.

    get_all_channel_states(device: int = 0) -> List[bool]
        Returns a boolean list of the last (i.e., current) set state for all 8
        power switches of the device at once. One value from the list
        corresponds to one channel: True is "on" and False is "off".
    """

    # This library has been modified by me, in order to work on SPI1 
    def __init__(self, pin_CE, device_count=1, bus=0):
        """Constructs a new Octofet board object that uses the default
        hardware SPI bus.

        Parameters:
        -----------
        pin_CE: int
            The chip enable (also known as chip select or slave select) pin
            used to control the shift-register latch. It can take the values
            0 or 1, which corresponds to the CE0 or CE1 pins on the Raspberry
            Pi board.

        device_count: int
            The number of Octofet boards connected in a daisy-chain. If
            omitted, defines a single Octofet board.
        """
        self._device_count = device_count
        self._data = [0x00] * self._device_count
        # Create an SPI object on the "0" SPI bus and connected to "pin_CE".
        self._spi = self._spi_init(bus, pin_CE)
        self._spi.writebytes(self._data)

    def digital_write(self, channel, value, device=0):
        """Sets the state ("on" or "off") of one power switch.

        Parameters:
        -----------
        channel: int
            The power switch index. Ranges from 0 to 7.

        value: bool
            Defines the desired switch state. Valid values: True to turn on or
            False to turn off.

        device: int
            The index of the affected Octofet in the daisy-chain. Ranges from
            0 to n - 1, where n is the number of Octofets in the chain. If
            omitted, targets Octofet nearest to the controller.
        """
        if value:
            self._data[device] |= (1 << channel) & 0xFF
        else:
            self._data[device] &= ~(1 << channel) & 0xFF

        self._spi.writebytes(self._data[::-1])

    def digital_write_all(self, value, device=0):
        """Sets the state ("on" or "off") of all power switches at once.

        Parameters:
        -----------
        value: List[bool]
            list of boolean values for all of 8 power switches. One value for
            one channel: True is "on" and False is "off".

        device: int
            the index of the affected Octofet in the daisy-chain. Ranges from
            0 to n - 1, where n is the number of Octofets in the chain. If
            omitted, targets Octofet nearest to the controller.
        """
        state = self._data[device]
        for i, val in enumerate(value):
            if val:
                state |= (1 << i) & 0xFF
            else:
                state &= ~(1 << i) & 0xFF
        self._data[device] = state

        self._spi.writebytes(self._data[::-1])

    def get_channel_state(self, channel, device=0):
        """Returns the last (i.e., current) set state for one power switch of
        the device. Returns True if turned on or False otherwise.

        Parameters:
        -----------
        channel: int
            The power switch index. Ranges from 0 to 7.

        device: int
            The index of the affected Octofet in the daisy-chain. Ranges from
            0 to n - 1, where n is the number of Octofets in the chain. If
            omitted, targets Octofet nearest to the controller.
        """
        return bool(self._data[device] & ((1 << channel) & 0xFF))

    def get_all_channel_states(self, device=0):
        """Returns a boolean list of the last (i.e., current) set state for all
        8 power switches of the device at once. One value from the list
        corresponds to one channel: True is "on" and False is "off".

        Parameters:
        -----------
        device: int
             The index of the affected Octofet in the daisy-chain. Ranges from
             0 to n - 1, where n is the number of Octofets in the chain. If
             omitted, targets Octofet nearest to the controller.
        """
        states_list = []
        for i in range(8):
            if self._data[device] & (1 << i):
                states_list.append(True)
            else:
                states_list.append(False)
        return states_list

    def _spi_init(self, bus, pin_CE):
        """Return a new SPI object that is connected to the specified SPI
        device interface.

        Parameters:
        -----------
        bus: int
            SPI bus number.
        pin_CE: int
            The chip enable pin.
        """
        spi = spidev.SpiDev()
        spi.open(bus, pin_CE)
        spi.max_speed_hz = 125000
        spi.mode = 0
        return spi

    def __del__(self):
        """The destructor is used to set the switches to the default state and
        to close the SPI connection.
        """
        self._data = [0x00] * self._device_count
        self._spi.writebytes(self._data)
        self._spi.close()
