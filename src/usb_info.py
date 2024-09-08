import dataclasses


@dataclasses.dataclass
class HIDInfo:
    """Base data class for a Custom HID implementation."""

    VID: int
    PID: int
    WRITE_EP: int
    READ_EP: int
    BYTES: int


class ReflexV2Info(HIDInfo):
    """HID information for a RE:Flex v2 Dance Pad."""

    def __init__(self):
        super(ReflexV2Info, self).__init__(0x0483, 0x5750, 0x01, 0x81, 64)


@dataclasses.dataclass
class FSRSerialInfo():
    """Sensor information for a dance pad with serial port communication"""

    NUM_SENSORS: int


class FSRReflexInfo(FSRSerialInfo):
    """Sensor information for a reflex-style dance pad with serial port communication"""

    def __init__(self):
        super(FSRReflexInfo, self).__init__(16)
