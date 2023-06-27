__all__ = ["WrightServoShutter"]

import asyncio
from typing import Dict
import time

from yaqd_core import IsDiscrete, HasPosition, UsesUart, UsesSerial, aserial


class WrightServoShutter(IsDiscrete, HasPosition, UsesUart, UsesSerial):
    _kind = "wright-servo-shutter"
    serial_dispatchers: Dict[str, aserial.ASerial] = {}

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        #self._reset_on_not_busy = False
        self._motornum = config["motor"]
        #self._units = config["units"]
        if config["serial_port"] in WrightServoShutter.serial_dispatchers:
            self._serial_port = WrightServoShutter.serial_dispatchers[config["serial_port"]]
        else:
            self._serial_port = aserial.ASerial(config["serial_port"], config["baud_rate"])
            WrightServoShutter.serial_dispatchers[config["serial_port"]] = self._serial_port


    def _set_position(self, position):
        #self._reset_on_not_busy = True
        if (position > 1.0):
            position = 1.00
        elif (position < 0.0):
            position = 0.00
        else:
            position=float(round(position))
        self._state["destination"] = position
        self._busy=False


    def direct_serial_write(self, message):
        #self._busy = True
        self._serial_port.write(message)


    async def update_state(self):
        while True:
            line = await self._serial_port.awrite_then_readline(f"G{self._motornum}\n".encode())
            #self._busy = line[0:1] != b"R"
            self._busy=False
            self._state["position"]=float(int(line[0:1]))
            #if self._reset_on_not_busy and not self._busy:
            #    self._busy = True
            #    self._reset_on_not_busy = False
            if (self._state["destination"] != self._state["position"]):
                self._serial_port.write(f"M{self._motornum}\n".encode())

            await asyncio.sleep(0.25)
            #if self._busy:
            #    self._state["position_identifier"] = None
            #else:
            k1 = None
            for k, v in self._position_identifiers.items():
                if round(self._state["position"]) == round(v):
                    k1 = k
            self._state["position_identifier"] = k1
