__all__ = ["WrightAerotech"]

import asyncio

from yaqd_core import ContinuousHardware, UsesSerial, UsesUart, IsHomeable, aserial


class WrightAerotech(UsesUart, IsHomeable, ContinuousHardware):
    _kind = "wright-aerotech"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self._serial_port = aserial.ASerial(config["serial_port"], config["baud_rate"])
        # Perform any unique initialization

    def _set_position(self, position):
        self._serial_port.write(f"M {position}\n".encode())

    def close(self):
        self._serial_port.close()

    def direct_serial_write(self, message):
        self._busy = True
        self._serial_port.write(message.encode())

    def home(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._home())

    async def _home(self):
        self._busy = True
        # Initiate the home
        self._serial_port.write(b"H\n")
        await self._not_busy_sig.wait()
        self.set_position(self._state["destination"])

    async def update_state(self):
        """Continually monitor and update the current daemon state."""
        # If there is no state to monitor continuously, delete this function
        while True:
            # Perform any updates to internal state
            self._serial_port.write(b"Q\n")
            line = await self._serial_port.areadline()
            self._busy = line[0:1] != b"R"
            # self.logger.debug(line[0:1])
            self._serial_port.write(b"G\n")
            self._state["position"] = float(await self._serial_port.areadline())
            if self._busy:
                await asyncio.sleep(0.1)
