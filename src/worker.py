import os

from utils.config import Config, Project, Route, Site
from utils.storage.s3 import S3Client
from utils.logger import get_logger
from rss import RSSFeed
from tor_scraper import Scraper
from parser import Parser
from diffing_tool import diffing
from classifier.simple import SimpleClassifier
from classifier.fuzzy import FuzzyClassifier

cwd = os.getcwd()
data_folder = os.environ.get("DATA_FOLDER", os.path.join(cwd, 'rss'))


def worker(config: Config, project: Project, site: Site, route: Route):
  rss_feed = RSSFeed(config)

  ttpClassifier = SimpleClassifier(os.path.join(data_folder, "ttp.csv"))
  malwareCapacitiesClassifier = FuzzyClassifier(os.path.join(data_folder, "malware-cap.csv"), enable_fuzz=True)

  # Set up context-aware logger for this job
  job_logger = get_logger(__name__).set_context(project=project, site=site, route=route)
  
  s3 = S3Client(config)
  parser = Parser(route['content_filters'])

  try:
    with Scraper(config) as scraper:
      page = scraper.scrape(project, site, route, store=False)
  except Exception as e:
    job_logger.error(f"Failed to scrape: {str(e)}")
    return

  if not page:
    job_logger.info("No page")
    return
  
  # Update logger context with working mirror URL
  working_mirror = page['metadata']['url']
  job_logger.set_context(url=working_mirror)
  
  job_logger.info("Parsing page...")
  current_text = parser.parse_html(page['content'])
  job_logger.info("Text extracted")

  versions = s3.get_page_versions(project['name'], route['path'])
  if len(versions) < 1:
    job_logger.info("No previous versions")

    job_logger.info("Storing page...")
    s3.store_page(project['name'], page)
    job_logger.info("Page stored")

    job_logger.info("Classifying current version...")
    ttps = ttpClassifier.run(current_text)
    capacities = malwareCapacitiesClassifier.run(current_text)
    job_logger.info("Classified")
    job_logger.info(f"Found TTPs: {', '.join([t['name'] for t in ttps["found_categories"]]) if ttps else 'None'}")
    job_logger.info(f"Found capacities: {', '.join([c['name'] for c in capacities["found_categories"]]) if capacities else 'None'}")

    # Add entry to RSS feed
    job_logger.info("Exporting to RSS...")
    rss_feed.add_entry(
      page_text=current_text,
      project=project,
      site=site,
      route=route,
      mirror_url=working_mirror,
      ttps=ttps["found_categories"],
      capacities=capacities["found_categories"]
    )
    return

  previous_version = s3.get_page(project['name'], route['path'], version_id=versions[0])
  if not previous_version:
    job_logger.error("Previous version not found on S3")
    return
  
  job_logger.info("Parsing previous version...")
  previous_text = parser.parse_html(previous_version['content'])
  job_logger.info("Text extracted")

  modification_detected, summary = diffing.diffing_texts(previous_text, current_text)

  if not modification_detected:
    job_logger.info("No modification detected")
    return

  job_logger.info("Modification detected")
  job_logger.info(f"Summary: {summary}")

  job_logger.info("Storing page...")
  s3.store_page(project['name'], page)
  job_logger.info("Page stored")

  job_logger.info("Classifying current and previous versions...")
  ttps = ttpClassifier.run(current_text)
  capacities = malwareCapacitiesClassifier.run(current_text)

  prev_ttps = ttpClassifier.run(previous_text)
  prev_capacities = malwareCapacitiesClassifier.run(previous_text)

  # pprint(capacities)
  
  job_logger.info(f"Found TTPs: {', '.join([t['name'] for t in ttps["found_categories"]]) if ttps else 'None'}")
  job_logger.info(f"Found capacities: {', '.join([c['name'] for c in capacities["found_categories"]]) if capacities else 'None'}")
  job_logger.info("Classified")
  
  # Add entry to RSS feed with diff information
  job_logger.info("Exporting to RSS...")
  rss_feed.add_entry(
    page_text=current_text,
    project=project,
    site=site,
    route=route,
    mirror_url=working_mirror,
    ttps=ttps["found_categories"],
    capacities=capacities["found_categories"],
    prev_ttps=prev_ttps["found_categories"],
    prev_capacities=prev_capacities["found_categories"],
    summary=summary
  )
  
  job_logger.info("Done")
