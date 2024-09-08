import multiprocessing
from multiprocessing.sharedctypes import SynchronizedArray
from multiprocessing.synchronize import Event
import serial
from serial.tools import list_ports

from usb_info import FSRSerialInfo

class SerialDeviceList:
    """List of serial ports."""

    @staticmethod
    def connected_device_names() -> list[str | None]:
        ports: list[list_ports.ListPortInfo] = list_ports.comports()
        return [port.device for port in ports if port.device == "COM16"]

    @staticmethod
    def get_device_by_serial(
        vid: int, pid: int, serial: str
    ) -> None:
        # devices: list[usb.core.Devicenene] | None = libusb_package.find(
        #     find_all=True, idVendor=vid, idProduct=pid
        # )
        # if devices is None:
        #     return
        # for device in devices:
        #     if device.serial_number == serial:
        #         return device
        return None


class SerialDeviceProcess(multiprocessing.Process):
    """Base class that manages a single serial connection in its own process."""

    def __init__(self, pad_info: FSRSerialInfo, port: str):
        super(SerialDeviceProcess, self).__init__()
        self._info = pad_info
        self._port = port
        self._data = multiprocessing.Array('i', 64)
        self._event = multiprocessing.Event()
        self._serial = None
        self.start()

    def terminate(self) -> None:
        if self._serial is not None:
            self._serial.close()
        super().terminate()

    def run(self) -> None:
        self._serial: serial.Serial
        self._serial = serial.Serial(self._port, 115200, timeout=0.2)
        if self._port is None:
            return
        # Set sensor thresholds high to avoid extra inputs from the keyboard or mouse
        for i in range(20):
            self._serial_command(f"{i} 1023")
        while True:
            self._process()

    def _process(self) -> None:
        pass

    def _serial_command(self, command: str) -> str:
        # Request sensor reading
        self._serial.write(f'{command}\n'.encode())
        # Read response
        line = self._serial.readline().decode('ascii')
        # If no newline at end, the command timed out. Print an error and ignore response.
        if not line.endswith('\n'):
            print(f'Timeout reading sensor values. Command: "{command}" Response: "{line}"')
        return line.strip()

    @property
    def data(self) -> SynchronizedArray:
        return self._data

    @property
    def event(self) -> Event:
        return self._event


class SerialReadProcess(SerialDeviceProcess):
    """Child class for reading data from an serial device."""

    def _process(self) -> None:
        line = self._serial_command("v")
        if not line.startswith("v"):
            return
        reports = line.split(" ")
        reports.pop(0)

        # 20 sensor values, every 5th one we will ignore for now
        values = []
        for x in [0, 1, 2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 15, 16, 17, 18]:
            values.append(int(reports[x]))

        with self._data.get_lock():
            for i, v in enumerate(values):
                self._data[i * 2] = v.to_bytes(2, 'little')[0]
                self._data[i * 2 + 1] = v.to_bytes(2, 'little')[1]
        self._event.set()


class HIDWriteProcess(SerialDeviceProcess):
    """Child class for writing data to an HID Endpoint."""

    def _process(self) -> None:
        pass
        # self._device: usb.core.Device
        # with self._data.get_lock():
        #     data = [d for d in self._data]
        # self._device.write(self._info.WRITE_EP, data)
        # self._event.set()
