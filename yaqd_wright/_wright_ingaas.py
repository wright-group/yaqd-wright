import numpy as np  # type: ignore
import serial  # type: ignore
import asyncio

from yaqd_core import HasMapping, UsesUart, HasMeasureTrigger, IsSensor, IsDaemon


class WrightInGaAs(HasMapping, UsesUart, HasMeasureTrigger, IsSensor, IsDaemon):
    _kind = "wright-ingaas"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self._channel_names = ["ingaas"]
        self._channel_units = {"ingaas": None}
        self._channel_shapes = {"ingaas": (256,)}

        self._channel_mappings = {"ingaas": ["wavelengths"]}
        self._mapping_units = {"wavelengths": "nm"}

        self._spec_position = self._config["spectrometer_position"]
        if isinstance(self._spec_position, str):
            host, port = self._spec_position.split(":")
            import yaqc  # type: ignore

            self._spec_client = yaqc.Client(int(port), host=host)
        else:
            self._spec_client = None

        self._mappings["wavelengths"] = self._gen_mappings()
        self._ser = serial.Serial()
        self._ser.baudrate = self._config["baud_rate"]  # must be 57600
        self._ser.port = self._config["serial_port"]
        self._ser.open()

    def _gen_mappings(self):
        """Get map."""
        # translate inputs into appropriate internal units
        spec_inclusion_angle_rad = np.radians(self._config["inclusion_angle"])
        spec_focal_length_tilt_rad = np.radians(self._config["focal_length_tilt"])
        pixel_width_mm = 0.050  # 50 microns
        # create array
        i_pixel = np.arange(256)  # 256 pixels
        # calculate terms
        x = np.arcsin(
            (1e-6 * self._config["order"] * self._config["grooves_per_mm"] * self.spec_position)
            / (2 * np.cos(spec_inclusion_angle_rad / 2.0))
        )
        A = np.sin(x - spec_inclusion_angle_rad / 2)
        B = np.sin(
            (spec_inclusion_angle_rad)
            + x
            - (spec_inclusion_angle_rad / 2)
            - np.arctan(
                (
                    pixel_width_mm * (i_pixel - self._config["calibration_pixel"])
                    + self._config["focal_length"] * spec_focal_length_tilt_rad
                )
                / (self._config["focal_length"] * np.cos(spec_focal_length_tilt_rad))
            )
        )
        out = ((A + B) * 1e6) / (self._config["order"] * self._config["grooves_per_mm"])
        return out

    async def _measure(self):
        out = np.zeros((256,))
        # update mapping
        self._mappings["wavelengths"] = self._gen_mappings()

        for _ in range(self._config["spectra_averaged"]):
            self._ser.reset_input_buffer()
            self._ser.write("S".encode())
            raw_string = self._read()
            # transform to floats
            raw_pixels = np.frombuffer(raw_string, dtype=">i2", count=256)
            # hardcoded processing
            pixels = 0.00195 * (raw_pixels[::-1] - (2060.0 + -0.0142 * np.arange(256)))
            out += pixels / self._config["spectra_averaged"]
        return {"ingaas": out}

    def _read(self):
        # handle communication with special end of line 'ready'
        eol = r"ready".encode()
        line = "".encode()
        while True:
            c = self._ser.read(1)
            if c:
                line += c
                if line.endswith(eol):
                    break
            else:
                break
        self._ser.flush()
        return line[-517:-5]

    def direct_serial_write(self, data):
        self._busy = True
        self._ser.write(data)

    @property
    def spec_position(self) -> float:
        if self._spec_client is None:
            return self._spec_position
        else:
            units = self._spec_client.get_units()
            # inflexible with units; can improve later
            assert units == "nm"
            position = self._spec_client.get_position()
            return position
