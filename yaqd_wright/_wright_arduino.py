__all__ = ["WrightArduino"]

import asyncio
from typing import Dict

from yaqd_core import HasPosition, UsesUart, UsesSerial, aserial

# current command set consists of one:
#  "M X Y" M=move (switch digital state), X= DO number(int), Y = 0 or 1
# "R00" reset to values of setup in firmware
# cross-reference firmware of Arduino to that shown here for confirmation
# firmware itself must reset to its setup on reading this command, can be checked


class WrightArduino(HasPosition, UsesUart, UsesSerial):
    _kind = "wright-arduino"
    serial_dispatchers: Dict[str, aserial.ASerial] = {}

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        #self._reset_on_not_busy = False
        if config["default_active_pin"]:
            self._state["active_pin"] = int(config["default_active_pin"])
        else:
            self._state["active_pin"] = int(0)

        if config["serial_port"] in WrightArduino.serial_dispatchers:
            self._serial_port = WrightArduino.serial_dispatchers[config["serial_port"]]
        else:
            self._serial_port = aserial.ASerial(config["serial_port"], config["baud_rate"])
            WrightArduino.serial_dispatchers[config["serial_port"]] = self._serial_port
        
         #following is based on firmware settings
        self._totalpins=14
        self._digitalarray=list(range(0,self._totalpins,1))
        self.reset()


    def reset(self):
        self._resetting=True

    def set_active_pin(self, pin):
        pin = int(pin)
        self._state["active_pin"] = pin

    def get_active_pin(self):
        pin= int(self._state["active_pin"])
        return pin 

    def get_total_position(self):
        return self._digitalarray

    def _set_position(self, position):
        #self._reset_on_not_busy = True
        if (position > 1.0):
            position = 1.00
        elif (position < 0.0):
            position = 0.00
        else:
            position=float(round(position))

        self._busy=False

    def direct_serial_write(self, message):
        #self._busy = True
        self._serial_port.write(message)


    async def update_state(self):
        while True:
            if self._resetting:
                self._serial_port.write(f"R00\n".encode())
                for i in range(len(self._digitalarray)):
                    self._digitalarray[i] = 0
                self._state["position"]=0
                self._state["destination"]=0
                self._resetting=False
            if (int(self._state["destination"]) != int(self._state["position"])):
                activepin=int(self._state["active_pin"])
                activepinhex=str(hex(activepin)[2:])
                destination=int(self._state["destination"])
                self._serial_port.write(f"M{activepinhex}{destination}\n".encode())
                # note the lines below assumes the write was successful
                self._digitalarray[activepin]=int(self._state["destination"])
                self._state["position"]=int(self._state["destination"])
            await asyncio.sleep(0.1)
