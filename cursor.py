import time

import numpy as np
import win32api, win32ui, win32con

from game_driver import OverWatchDriver



if __name__ == "__main__":

    controller = OverWatchDriver()
    
    # show cursor position
    while True:
        x, y = win32api.GetCursorPos()
        print(x, y)
        time.sleep(0.1)