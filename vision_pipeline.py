# Done by Frannecklp

import cv2
import numpy as np
import win32gui, win32ui, win32con

from game_driver import OverWatchDriver
from util import Position2D
from keypress import KeyCodes, pressKey, releaseKey

class VisionPipeline:
    NAMETAG_COLOR = np.array((0, 215, 0))
    UI_COLOR = np.array((40, 210, 240))
    PHARAH_BLOCKED_COLOR = np.array((54, 158, 198))
    # PHARAH_COLOR = np.array((60, 140, 200))

    def __init__(self, game: OverWatchDriver, debug=False):
        self.game = game
        self.debug = debug

        self.debug_img = None

        self.nametag_pos = None
        self.ui_border_pos = None
        self.pharah_pos = None

    def _colorKeyMask(self, img: np.ndarray, color: np.ndarray, tolerance: np.ndarray, blur: int = 25):
        mask = cv2.inRange(img, color - tolerance, color + tolerance)
        if blur:
            mask = cv2.GaussianBlur(mask, (blur, blur), 0)
        return mask

    def _findContours(self, mask: np.ndarray):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def _findLargestContour(self, contours: list):
        largest_contour = None
        largest_area = 0
        for contour in contours:
            area = cv2.contourArea(contour)

            if area > largest_area:
                largest_area = area
                largest_contour = contour
        
        return largest_contour, largest_area
    
    def applyROIMask(self, img: np.ndarray):
        avatar_panel_mask_loc = ((20, 454), (240, 560))
        ult_panel_mask_loc = ((455, 440), (575, 560))
        skill_panel_mask_loc = ((780, 470), (1010, 560))

        mask = np.ones((img.shape[0], img.shape[1]), dtype=np.uint8)
        mask[
            avatar_panel_mask_loc[0][1]:avatar_panel_mask_loc[1][1],
            avatar_panel_mask_loc[0][0]:avatar_panel_mask_loc[1][0]] = 0
        mask[
            ult_panel_mask_loc[0][1]:ult_panel_mask_loc[1][1],
            ult_panel_mask_loc[0][0]:ult_panel_mask_loc[1][0]] = 0
        mask[
            skill_panel_mask_loc[0][1]:skill_panel_mask_loc[1][1],
            skill_panel_mask_loc[0][0]:skill_panel_mask_loc[1][0]] = 0
        
        img = cv2.bitwise_and(img, img, mask=mask)
        return img

    def getHealth(self, img: np.ndarray):
        # health_bar_loc = ((20, 560), (20 + 240, 560 + 20))
        # crop_img = img[y:y+h, x:x+w]
        pass

    def run(self):
        try:
            while True:
                img = controller.grabWindow()
                self.debug_img = np.zeros_like(img)
                

                img = self.applyROIMask(img)
                

                ### Find Nametag ###
                nametag_mask = self._colorKeyMask(
                    img,
                    color=self.NAMETAG_COLOR,
                    tolerance=np.array([40] * 3),
                    blur=25)

                self.debug_img[:, :, 1] += nametag_mask

                nametag_contours = self._findContours(nametag_mask)
                nametag_contour, nametag_area = self._findLargestContour(nametag_contours)

                nametag_found = nametag_contour is not None and nametag_area > 200

                if nametag_found:
                    x, y, w, h = cv2.boundingRect(nametag_contour)

                    nametag_pos = Position2D(x + w // 2, y + h // 2)
                    self.nametag_pos = nametag_pos

                    nametag_offset = nametag_pos - self.game.center
                    mouse_offset_y = nametag_offset.y + 80

                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.line(img, (img.shape[1] // 2, img.shape[0] // 2), (x + w // 2, y + h // 2), (0, 255, 0), 2)

                

                ### find UI ###
                ui_border_mask = self._colorKeyMask(
                    img,
                    color=self.UI_COLOR,
                    tolerance=np.array([35] * 3),
                    blur=21)
                
                self.debug_img[:, :, 1] += ui_border_mask
                self.debug_img[:, :, 2] += ui_border_mask

                ui_border_contours = self._findContours(ui_border_mask)

                for contour in ui_border_contours:
                    x, y, w, h = cv2.boundingRect(contour)

                    pos = Position2D(x + w // 2, y + h // 2)
                    ui_offset = pos - self.game.center
                    
                    if nametag_found and abs(nametag_offset.x - ui_offset.x) < 10:
                        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 128, 255), 2)
                        ui_border_pos = pos
                        self.ui_border_pos = ui_border_pos

                ### find Pharah ###
                            
                tolerance = np.array([30] * 3)
                pharah_mask = self._colorKeyMask(img, self.PHARAH_BLOCKED_COLOR, tolerance, blur=25)

                self.debug_img[:, :, 2] += pharah_mask

                # Find contours in the filtered mask
                pharah_contours = self._findContours(pharah_mask)

                largest_contour_area = 0
                largest_contour = None
                largest_bbox = None
                for contour in pharah_contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    area = cv2.contourArea(contour)

                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 64), 2)  # Blue rectangle

                    if area > largest_contour_area:
                        largest_contour_area = area
                        largest_contour = contour
                        largest_bbox = (x, y, w, h)
                



                if self.debug:
                    # increase intensity of the debug image
                    self.debug_img = self.debug_img * 2

                    cv2.imshow("Debug Mask", cv2.cvtColor(cv2.resize(self.debug_img, (0, 0), fx=0.5, fy=0.5), cv2.COLOR_RGB2BGR))
                    cv2.imshow("Debug Overlay", cv2.cvtColor(cv2.resize(img, (0, 0), fx=0.5, fy=0.5), cv2.COLOR_RGB2BGR))
                    pass


                if cv2.waitKey(25) & 0xFF == ord("q"):
                    cv2.destroyAllWindows()
                    break

        except KeyboardInterrupt:
            pass
        self.stop()
        print("exiting")


    def stop(self):
        cv2.destroyAllWindows()


if __name__ == "__main__":

    controller = OverWatchDriver()
    vision = VisionPipeline(controller, debug=True)


    vision.run()