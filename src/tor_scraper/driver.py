import os
import io
import logging
from datetime import datetime

from PIL import Image
import tbselenium.common as tbs_cm
from tbselenium.tbdriver import TorBrowserDriver
from pyvirtualdisplay.display import Display

from utils.config import Config

logger = logging.getLogger(__name__)

class Driver(TorBrowserDriver):
  config: Config
  logger: logging.Logger
  screenshot_path: str

  def __init__(self, config: Config):
    self.config = config
    self.logger = logger.getChild(__class__.__name__)

    self.logger.info('Initializing driver')

    selenium_profile_path = os.path.join(self.config.tor['tbb_path'], tbs_cm.DEFAULT_TBB_DATA_DIR, 'Browser', 'profile.selenium')
    super().__init__(
      self.config.tor['tbb_path'],
      tor_cfg=tbs_cm.USE_RUNNING_TOR,
      tbb_profile_path=selenium_profile_path)
    
    self.screenshot_path = os.path.join(self.config.tor['tmp_path'], 'screenshots')
    for path in [self.config.tor['tmp_path'], self.screenshot_path]:
      try: os.mkdir(path)
      except FileExistsError: pass

    self.logger.info('Driver ready')
    
  def take_screenshot(self) -> str:
    file_path = os.path.join(self.screenshot_path, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    self.logger.debug('Taking full page screenshot as png')

    if self.config.tor['screenshot_quality'] == 100:
      file_path += ".png"
      self.get_full_page_screenshot_as_file(file_path)

    else:
      file_path += ".jpeg"

      screenshot = self.get_full_page_screenshot_as_png()
      
      self.logger.debug('Loading screenshot with PIL')
      pil_image = Image.open(io.BytesIO(screenshot)).convert('RGB')

      self.logger.debug('Exporting as JPEG')
      pil_image.save(file_path, format="JPEG", quality=self.config.tor['screenshot_quality'])
    
    self.logger.debug('Screenshot saved')

    return file_path

class HeadlessDriver(Driver):
  display: Display
  logger: logging.Logger

  def __init__(self, config: Config):
    self.logger = logger.getChild(__class__.__name__)

    self.logger.info('Initializing display')
    self.display = Display(manage_global_env=False).__enter__()

    os.environ['DISPLAY'] = self.display.new_display_var

    super().__init__(config)

  def __exit__(self, *args):
    super().__exit__(args);
    self.display.__exit__(args);