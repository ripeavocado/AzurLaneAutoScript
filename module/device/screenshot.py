import os
import time
from datetime import datetime
from io import BytesIO

from PIL import Image
from retrying import retry

from module.device.connection import Connection
from module.logger import logger
from module.base.timer import Timer


class Screenshot(Connection):
    _screenshot_method = 0
    _screenshot_method_fixed = False
    _screenshot_interval_timer = Timer(0.1)
    _adb = False
    _last_save_time = {}
    image: Image.Image

    def _screenshot_uiautomator2(self):
        image = self.device.screenshot()
        return image.convert('RGB')

    def _load_screenshot(self, screenshot):
        if self._screenshot_method == 0:
            return Image.open(BytesIO(screenshot)).convert('RGB')
        elif self._screenshot_method == 1:
            return Image.open(BytesIO(screenshot.replace(b'\r\n', b'\n'))).convert('RGB')
        elif self._screenshot_method == 2:
            return Image.open(BytesIO(screenshot.replace(b'\r\r\n', b'\n'))).convert('RGB')

    def _process_screenshot(self, screenshot):
        if self._screenshot_method_fixed:
            return self._load_screenshot(screenshot)
        else:
            for _ in range(3):
                try:
                    screenshot = self._load_screenshot(screenshot)
                except OSError:
                    self._screenshot_method += 1
                else:
                    self._screenshot_method_fixed = True
                    break
            return screenshot

    def _screenshot_adb(self):
        screenshot = self.adb_shell(['screencap', '-p'], serial=self.serial)
        return self._process_screenshot(screenshot)

    @retry()
    # @timer
    def screenshot(self):
        """
        Returns:
            PIL.Image.Image:
        """
        self._screenshot_interval_timer.wait()
        self._screenshot_interval_timer.reset()
        adb = self.config.USE_ADB_SCREENSHOT
        self._adb = adb

        if adb:
            self.image = self._screenshot_adb()
        else:
            self.image = self._screenshot_uiautomator2()

        self.image.load()
        if self.config.ENABLE_ERROR_LOG_AND_SCREENSHOT_SAVE:
            logger.screenshot_deque.append({'time': datetime.now(), 'image': self.image})

        return self.image

    def save_screenshot(self, genre='items'):
        """Save a screenshot. Use millisecond timestamp as file name.

        Args:
            genre (str, optional): Screenshot type.

        Returns:
            bool: True if save succeed.
        """
        now = time.time()
        if now - self._last_save_time.get(genre, 0) > self.config.SCREEN_SHOT_SAVE_INTERVAL:
            fmt = 'png' if self._adb else 'png'
            file = '%s.%s' % (int(now * 1000), fmt)

            folder = os.path.join(self.config.SCREEN_SHOT_SAVE_FOLDER, genre)
            if not os.path.exists(folder):
                os.mkdir(folder)

            file = os.path.join(folder, file)
            self.image.save(file)
            self._last_save_time[genre] = now
            return True
        else:
            self._last_save_time[genre] = now
            return False

    def screenshot_interval_set(self, interval):
        if interval < 0.1:
            interval = 0.1
        if interval != self._screenshot_interval_timer.limit:
            logger.info(f'Screenshot interval set to {interval}s')
            self._screenshot_interval_timer.limit = interval
