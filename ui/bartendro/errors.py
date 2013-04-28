class SerialIOError(Exception):
    """Error raised when serial port cannot be opened, read or written"""
    pass

class I2CIOError(Exception):
    """Error raised when I2C bus cannot be opened, read or written"""
    pass
