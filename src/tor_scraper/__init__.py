import logging
from typing import ContextManager, Union

from selenium.common import WebDriverException

from utils.storage.s3 import S3Client
from utils.storage import ScrapedPage

from utils.config import Config, Project, Route, Site
from utils.logger import get_logger, CTILogger
from .driver import Driver, HeadlessDriver

logger = get_logger(__name__)

class Scraper(ContextManager):
  s3: S3Client
  logger: CTILogger
  driver: Driver

  def __init__(self, config: Config):
    self.s3 = S3Client(config)
    self.driver = HeadlessDriver(config)

    self.logger = logger.getChild(__class__.__name__)

  def __enter__(self):
    self.driver.__enter__()
    self.logger.debug(f"Driver initialized")
    return self
  
  def __exit__(self, *args):
    self.driver.__exit__(args)

  # TODO: Handle errors
  def scrape(self, project: Project, site: Site, route: Route, store = True) -> Union[ScrapedPage, None]:
    job_logger = self.logger.getChild("scrape").set_context(project=project, site=site, route=route)

    job_logger.info("Loading page")

    # Try each mirror until one works
    loaded_mirror = None
    last_error = None
    
    for mirror in route['mirrors']:
      job_logger.debug(f"Trying mirror {mirror}")
      try:
        self.driver.load_url(mirror)
        loaded_mirror = mirror
        break
      except WebDriverException as e:
        job_logger.warning(f"Failed to load mirror: {e.msg}")
        last_error = e
        
    # Raise error if no mirror worked
    if loaded_mirror is None:
      error_msg = "All mirrors failed"
      if last_error:
        error_msg += f": {last_error.msg}"
      job_logger.error(error_msg)
      raise RuntimeError(error_msg)

    job_logger.debug(f"Page loaded: {self.driver.title}")

    # Take screenshot if requested
    screenshot_path = None
    if route['take_screenshot']:
      screenshot_path = self.driver.take_screenshot()
      job_logger.debug(f"Screenshot saved at {screenshot_path}")

    page: ScrapedPage = {
    'content': self.driver.page_source,
        'path': route['path'],
        'screenshot_path': screenshot_path,
        'metadata': {
          'url': loaded_mirror
        }
      }

    # Store the page content and screenshot in S3
    if store:
      self.s3.store_page(project['name'], page)
      job_logger.debug("Page stored")

    job_logger.info("Page scraped")

    return page