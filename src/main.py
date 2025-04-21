import multiprocessing as mp
from dotenv import load_dotenv
import logging

from utils.config import Config
from utils.logger import get_logger, configure_logging
from worker import worker

if __name__ == '__main__':

  # Configure logging once with our custom setup instead of basicConfig
  configure_logging(level=logging.DEBUG)
  logger = get_logger(__name__)
  [
    logging.getLogger(l).setLevel(logging.WARNING)
    for l in ["urllib3", "pyvirtualdisplay", "selenium"]
  ]

  load_dotenv()
  config = Config()

  logger.info('Starting worker pool')
  with mp.Pool(mp.cpu_count()) as pool:
      # Process all routes from all sites in all projects
      pool.starmap(worker, [(config, p, s, r) for p in config.projects for s in p['sites'] for r in s['routes']])

  logger.info('Pool done')