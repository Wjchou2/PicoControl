import time
import usb_hid
from adafruit_hid.mouse import Mouse

mouse = Mouse(usb_hid.devices)

# Move the mouse in a small square repeatedly
while True:
    pass
    # mouse.click(Mouse.LEFT_BUTTON)
    # mouse.move(x=20)  # move right
    # time.sleep(0.5)
    # mouse.move(y=20)  # move down
    # time.sleep(0.5)
    # mouse.move(x=-20)  # move left
    # time.sleep(0.5)
    # mouse.move(y=-20)  # move up
    # time.sleep(0.5)
