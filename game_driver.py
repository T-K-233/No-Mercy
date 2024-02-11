import time

import cv2
import numpy as np
import win32gui, win32api, win32con, win32ui

from keypress import KeyCodes, pressKey, releaseKey
from util import Position2D

class GameConstants:
    MOVEMENT_SPEED = 5.5  # m/s


class ViewController:
    """
    Controller for the viewport in the game. 
    
    """
    GAME_MOUSE_X_RATIO = 1.515
    GAME_MOUSE_Y_RATIO = 1.500
    
    def __init__(self):
        # default mouse sensitivity is 15%
        self.mouse_sensitivity = .15
        
        self.yaw = 0
        self.pitch = 0
    
    def _angleToPixelX(self, angle: float) -> int:
        return -int(angle * (self.GAME_MOUSE_X_RATIO / self.mouse_sensitivity))
    
    def _angleToPixelY(self, angle: float) -> int:
        return -int(angle * (self.GAME_MOUSE_Y_RATIO / self.mouse_sensitivity))
        
    def moveRelative(self, pitch: float, yaw: float):
        """
        Move the view in the game by the given relative yaw and pitch.
        
        positive yaw moves the view to the left, negative to the right.
        positive pitch moves the view up, negative down.
        
        Args:
            pitch (float): The pitch to move the view by, in degrees.
            yaw (float): The yaw to move the view by, in degrees. 
        """
        x_value = self._angleToPixelX(yaw)
        y_value = self._angleToPixelY(pitch)
        
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, x_value, y_value, 0, 0)

    def reset(self):
        self.moveRelative(180, 0)
        time.sleep(0.05)
        self.moveRelative(-90, 0)
        time.sleep(0.05)
        self.pitch = 0
    
    def setPitch(self, pitch: float):
        """
        Set the pitch of the view in the game.
        
        positive pitch moves the view up, negative down.
        
        Args:
            pitch (float): The pitch to set the view to, in degrees.
        """
        err = pitch - self.view_pitch
        self.moveRelative(err, 0)
        self.pitch = pitch
    
    def setYaw(self, yaw: float):
        """
        Set the yaw of the view in the game.
        
        positive yaw moves the view to the left, negative to the right.
        
        Args:
            yaw (float): The yaw to set the view to, in degrees.
        """
        err = yaw - self.view_yaw
        self.moveRelative(0, err)
        self.yaw = yaw

class Message:
    YES = KeyCodes._1
    NO = KeyCodes._2
    ON_MY_WAY = KeyCodes._3
    READY = KeyCodes._4
    FALL_BACK = KeyCodes._5
    GROUP_UP = KeyCodes._6
    NEED_HELP = KeyCodes._7

class KeyboardController:
    def __init__(self):
        pass

    def sendMessage(self, message: Message):
        pressKey(KeyCodes.LMENU)
        pressKey(message)
        time.sleep(0.05)
        releaseKey(message)
        releaseKey(KeyCodes.LMENU)
        time.sleep(0.05)


class OverWatchDriver:
    WINDOWS_BAR_HEIGHT = 32
    WINDOWS_MARGIN_WIDTH = 9

    def __init__(self):
        self.view = ViewController()
        
        for i in range(3):
            print("Starting in", 3 - i)
            time.sleep(1)
        
        
        self.hwnd = OverWatchDriver.getWindowByTitle("Overwatch")
        if not self.hwnd:
            print("No window found, using full desktop capture instead")
            self.hwnd = win32gui.GetDesktopWindow()

        self.focus()

        self.reset()

    def focus(self):
        win32gui.SetForegroundWindow(self.hwnd)
        time.sleep(0.05)

    def reset(self):
        # reset window capture
        # (x1, y1, x2, y2)
        bbox_full = win32gui.GetWindowRect(self.hwnd)

        # trim off the window bar
        self.bbox = (
            bbox_full[0] + self.WINDOWS_MARGIN_WIDTH,
            bbox_full[1] + self.WINDOWS_BAR_HEIGHT,
            bbox_full[2] - self.WINDOWS_MARGIN_WIDTH,
            bbox_full[3] - self.WINDOWS_MARGIN_WIDTH
        )

        print("Window bbox:", self.bbox)

        self.bbox_offset = Position2D(self.WINDOWS_MARGIN_WIDTH, self.WINDOWS_BAR_HEIGHT)

        self.width = self.bbox[2] - self.bbox[0] + 1
        self.height = self.bbox[3] - self.bbox[1] + 1

        self.center = Position2D(self.width // 2, self.height // 2)

        # reset view
        self.view.reset()
        
    def step(self, actions: np.ndarray) -> np.ndarray:
        """
        Perform a step in the game.
        
        Action mapping:
        | Index | Type  | Name  | Description                   |
        | ----- | ----- | ----- | ----------------------------- |
        | 0     | float | pitch | -90 (down) to +90 (up)        |
        | 1     | float | yaw   | -180 (right) to +180 (left)   |
        | 2     | bool  | LMB   | left mouse button             |
        | 3     | bool  | RMB   | right mouse button            |
        | 4     | bool  | W     | forward                       |
        | 5     | bool  | S     | backward                      |
        | 6     | bool  | A     | left                          |
        | 7     | bool  | D     | right                         |
        | 8     | bool  | Space | jump                          |
        | 9     | bool  | Ctrl  | crouch                        |
        | 10    | bool  | Shift | ability 1                     |
        | 11    | bool  | E     | ability 2                     |
        | 12    | bool  | Q     | ability 3                     |
        | 13    | bool  | R     | reload                        |
        | 14    | bool  | V     | melee                         |
        
        Args:
            actions (np.ndarray): The actions to perform. 
        
        Returns:
            np.ndarray: The observation after the step.
        """
        pitch = actions[0]
        yaw = actions[1]
        
        self.view.setPitch(pitch)
        self.view.setYaw(yaw)
        
        obs = None
        
        return obs
        
    def grabWindow(self) -> np.ndarray:
        hwindc = win32gui.GetWindowDC(self.hwnd)
        srcdc = win32ui.CreateDCFromHandle(hwindc)
        memdc = srcdc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, self.width, self.height)
        memdc.SelectObject(bmp)
        memdc.BitBlt((0, 0), (self.width, self.height), srcdc, self.bbox_offset.asTuple(), win32con.SRCCOPY)
        
        buffer = bmp.GetBitmapBits(True)
        img = np.frombuffer(buffer, dtype="uint8")
        img.shape = (self.height, self.width, 4)

        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwindc)
        win32gui.DeleteObject(bmp.GetHandle())

        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        return img

    @staticmethod
    def getWindowByTitle(title):
        winlist = []
        win32gui.EnumWindows(lambda hwnd, results: winlist.append((win32gui.GetWindowText(hwnd), hwnd)), [])
        
        target_hwnds = [hwnd for hwnd_title, hwnd in winlist if hwnd_title == title]
        
        if not target_hwnds:
            return None
        
        hwnd = target_hwnds[0]
        return hwnd


if __name__ == "__main__":
    controller = OverWatchDriver()

    pressKey(KeyCodes.W)
    time.sleep(2)
    releaseKey(KeyCodes.W)
