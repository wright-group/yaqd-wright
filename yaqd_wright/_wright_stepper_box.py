__all__ = ["WrightStepperBox"]

import asyncio
from typing import Dict
import time

from yaqd_core import (
    HasTransformedPosition,
    IsHomeable,
    HasLimits,
    IsDiscrete,
    HasPosition,
    UsesUart,
    UsesSerial,
    aserial,
)


class WrightStepperBox(
    HasTransformedPosition, IsHomeable, HasLimits, IsDiscrete, HasPosition, UsesUart, UsesSerial
):
    _kind = "wright-stepper-box"
    serial_dispatchers: Dict[str, aserial.ASerial] = {}

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self._reset_on_not_busy = False
        self._motornum = config["motor"]
        self._units = config["units"]
        self._microstep = config["microstep"]
        self._steps_per_unit = config["steps_per_unit"]
        if config["serial_port"] in WrightStepperBox.serial_dispatchers:
            self._serial_port = WrightStepperBox.serial_dispatchers[config["serial_port"]]
        else:
            self._serial_port = aserial.ASerial(config["serial_port"], config["baud_rate"])
            WrightStepperBox.serial_dispatchers[config["serial_port"]] = self._serial_port
        self._set_microstep(self._microstep)
        self._factor = config["factor"]

    def _relative_to_transformed(self, relative_position):
        """allow param "factor" to multiply scale"""
        return relative_position * self._factor

    def _transformed_to_relative(self, transformed_position):
        """allow param "factor" to multiply axis"""
        return transformed_position / self._factor

    def _set_position(self, position):
        self._reset_on_not_busy = True

    def direct_serial_write(self, message):
        self._busy = True
        self._serial_port.write(message)

    def home(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._home())

    async def _home(self):
        self._busy = True
        self._serial_port.write(f"H {self._motornum}\n".encode())
        self._reset_on_not_busy = True
        self._state["position"] = 0.0

    def _set_microstep(self, microint):
        self._busy = True
        if microint in [2**i for i in range(0, 6)]:
            self._serial_port.write(f"U {microint}\n".encode())
            self._microstep = microint
        else:
            raise ValueError("microint must be a power of 2 (e.g. 1, 2,... 32)")

    async def update_state(self):
        while True:
            line = await self._serial_port.awrite_then_readline(f"Q {self._motornum}\n".encode())
            self._busy = line[0:1] != b"R"
            if self._reset_on_not_busy and not self._busy:
                self._busy = True
                self._reset_on_not_busy = False
                step_position = round(
                    self._microstep
                    * (self._state["destination"] - self._state["position"])
                    * self._steps_per_unit
                )
                self._serial_port.write(f"M {self._motornum} {step_position}\n".encode())
                self._state["position"] += step_position / (self._steps_per_unit * self._microstep)
            self.logger.debug(f"{self._busy=}")
            await asyncio.sleep(0.2)
            if self._busy:
                self._state["position_identifier"] = None
            else:
                k1 = None
                for k, v in self._position_identifiers.items():
                    if round(self._state["position"]) == round(v):
                        k1 = k
                self._state["position_identifier"] = k1

    def get_factor(self) -> float:
        return self._factor
