# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 09:53:37 2020

@author: jsche
"""
__all__ = ["YaqdWrightFilterWheelsContinuous"]

import asyncio
import time
from yaqd_core import ContinuousHardware, aserial

from .__version__ import __branch__

class YaqdWrightFilterWheelsContinuous(ContinuousHardware):
    _kind = "wright-filter-wheels-continuous"
    _version = "0.1.0" + f"+{__branch__}" if __branch__ else ""

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self._motornum=config["motor"]
        self._serial_port = aserial.ASerial(config["serial_port"], config["baud_rate"])
        self._units=config["units"]
        self._microstep=config["microstep"]
        self._set_microstep(self._microstep)
        time.sleep(0.2)
        self._steps_per_rotation=400

    def _set_position(self, position):
        step_position=round(self._microstep*(position-self._state["position"])*self._steps_per_rotation/360)
        self._serial_port.write(f"M {self._motornum} {step_position}\n".encode())
        self._state["position"]=position

    def direct_serial_write(self, message):
        self._busy = True
        self._serial_port.write(message)

    def home(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._home())
    
    async def _home(self):
        self._busy = True
        self._serial_port.write(f"H {self._motornum}\n".encode())
        await self._not_busy_sig.wait()
        self._state["position"]=0
        self.set_position(self._state["destination"])
    
    def _set_microstep(self, microint):
        self._busy = True
        if microint in [2**i for i in range(0,6)]:
            self._serial_port.write(f"U {microint}\n".encode())
            self._microstep=microint

    async def update_state(self):
        while True:
            self._serial_port.write(f"Q {self._motornum}\n".encode())
            line = await self._serial_port.areadline()
            self._busy = (line[0:1] != b"R")
            await asyncio.sleep(0.2)
            if self._busy:
                pass