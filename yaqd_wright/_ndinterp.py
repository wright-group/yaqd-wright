__all__ = ["NDInterp"]

import asyncio
from typing import Dict, Any, List, Union

from scipy.interpolate import RegularGridInterpolator  # type: ignore
import yaqc  # type: ignore
from yaqd_core import HasLimits, IsHomeable, HasPosition, IsDaemon
import WrightTools as wt  # type: ignore


class NDInterp(HasLimits, IsHomeable, HasPosition, IsDaemon):
    _kind = "ndinterp"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)

        self._data = wt.open(config["data_path"], edit_local=True)
        self._offset_channel = config["offset_channel"]
        self._interp = RegularGridInterpolator(
            [ax[:].flatten() for ax in self._data.axes],
            self._data[self._offset_channel][:],
            bounds_error=False,
            fill_value=0,
        )

        if isinstance(config["wrapped_daemon"], int):
            self._wrapped_daemon = yaqc.Client(config["wrapped_daemon"])
        else:
            host, port = config["wrapped_daemon"].split(":")
            self._wrapped_daemon = yaqc.Client(port=int(port), host=host)

        self._units = self._wrapped_daemon.get_units()

    def _set_position(self, position):
        position += self.get_offset() + self._state["zero_position"]
        self._wrapped_daemon.set_position(position)
        self._set_limits()

    def get_offset(self):
        if not self._state["offset_enabled"]:
            return 0
        try:
            return float(
                self._interp([self._state["control_position"][ax] for ax in self._data.axis_names])
            )
        except KeyError:
            self.logger.error("Not all control positions found, no offset applied")
        return 0

    def set_control_position(self, control: str, position: float):
        self._state["control_position"][control] = position
        self.set_position(self._state["destination"])

    def get_control_positions(self):
        return self._state["control_position"]

    def home(self):
        self._busy = True
        self._wrapped_daemon.home()

    def get_dependent_hardware(self):
        return {"stage": f"{self._wrapped_daemon._host}:{self._wrapped_daemon._port}"}

    def _set_limits(self):
        min_, max_ = self._wrapped_daemon.get_limits()
        min_ = self._to_offset(min_)
        max_ = self._to_offset(max_)
        if min_ < max_:
            self._state["hw_limits"] = [min_, max_]
        else:
            self._state["hw_limits"] = [max_, min_]

    def _to_offset(self, mm):
        mm -= self._state["zero_position"]
        offset = self.get_offset()
        return mm - offset

    async def update_state(self):
        """Continually monitor and update the current daemon state."""
        while True:
            self._busy = self._wrapped_daemon.busy()
            self._state["position"] = self._to_offset(self._wrapped_daemon.get_position())
            if self._busy:
                await asyncio.sleep(0.01)
            else:
                await asyncio.sleep(0.1)

    def set_zero_position(self, position: float):
        self._state["zero_position"] = position

        # Zero curves
        offset = self._data[self._offset_channel]
        offset -= self.get_offset()
        self._data.flush()

        self._interp = RegularGridInterpolator(
            [ax[:].flatten() for ax in self._data.axes],
            self._data[self._offset_channel][:],
            bounds_error=False,
            fill_value=0,
        )

        self._state["position"] = self._to_offset(self._wrapped_daemon.get_position())
        self._state["destination"] = self._state["position"]
        self._set_limits()

    def get_zero_position(self):
        return self._state["zero_position"]

    def get_zero_position_units(self):
        return self._wrapped_daemon.get_units()

    def get_zero_position_limits(self):
        return self._wrapped_daemon.get_limits()

    def get_control_tunes(self):
        return {}

    def set_control_tune(self, control, tune):
        return

    def get_control_active(self):
        return {}

    def set_control_active(self, control, active):
        return

    def set_offset_enabled(self, enable):
        self._state["offset_enabled"] = enable
        self.set_position(self._state["destination"])

    def get_offset_enabled(self):
        return self._state["offset_enabled"]
