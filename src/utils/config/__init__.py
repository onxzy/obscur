import os
import logging
import json
import re
import yaml
from urllib.parse import urljoin
from .tor import Tor
from .project import Project, Site, Route
from .storage import Storage
from .stix import StixMalware
from .rss import RSS  # Import the new RSS TypedDict

HOME = os.environ.get("HOME", default="/")

logger = logging.getLogger(__name__)

class Config():
  projects: list[Project]
  storage: Storage
  tor: Tor
  rss: RSS  # Update type annotation to use the TypedDict
  
  def __init__(self, configFolder: str = os.environ.get("CONFIG_FOLDER", "config")):
    logger.info(f"Parsing config in {os.path.realpath(configFolder)} folder")
    # Read default config file
    default_path = os.path.join(configFolder, "default.yaml")
    with open(default_path, 'r') as f:
      default = yaml.safe_load(f)

    # Init Tor config
    logger.debug(f"Parsing tor configuration")
    self.tor = {
      "tbb_path": os.environ.get("TBB_PATH") or os.path.join(HOME, "tor-browser"),
      "screenshot_quality": default['tor']['screenshot_quality'],
      "tmp_path": default['tor']['tmp_path']
    }
    logger.info(f"tbb_path: {self.tor['tbb_path']}")
    logger.debug(f"screenshot_quality: {self.tor['screenshot_quality']}")
    logger.debug(f"tmp_path: {self.tor['tmp_path']}")

    # Init Storage config
    logger.debug(f"Parsing storage configuration")
    self.storage = {
      "bucket_content": default['storage']['bucket']['content'],
      "bucket_screenshot": default['storage']['bucket']['screenshot'],
      "s3": {
        "endpoint": os.environ["S3_ENDPOINT"],
        "port": int(os.environ["S3_PORT"]),
        "region": os.environ["S3_REGION"],
        "access_key": os.environ["S3_ACCESS_KEY"],
        "secret_key": os.environ["S3_SECRET_KEY"]
      }
    }
    logger.debug(f"bucket_content: {self.storage['bucket_content']}")
    logger.debug(f"bucket_screenshot: {self.storage['bucket_screenshot']}")
    logger.info(f"s3.endpoint: {self.storage['s3']['endpoint']}")
    logger.debug(f"s3.port: {self.storage['s3']['port']}")
    logger.debug(f"s3.region: {self.storage['s3']['region']}")
    
    # Init RSS config
    logger.debug(f"Parsing RSS configuration")
    self.rss = {
      "server_url": default.get('rss', {}).get('server_url', ''),
      "max_items": default.get('rss', {}).get('max_items', 50)  # Default to 50 if not specified
    }
    logger.debug(f"rss.server_url: {self.rss['server_url']}")
    logger.debug(f"rss.max_items: {self.rss['max_items']}")

    # Init Project config
    logger.debug(f"Parsing projects")
    self.projects = []
    for filename in os.listdir(configFolder):
      if filename != "default.yaml" and (filename.endswith(".yaml") or filename.endswith(".yml")):
        logger.debug(f"Parsing {filename}")
        project_path = os.path.join(configFolder, filename)
        with open(project_path, 'r') as f:
          project_config = yaml.safe_load(f)

        # Safely extract stix_details, only including defined fields
        stix_config = project_config['project'].get('stix_details', {})
        stix_details: StixMalware = {
          "name": stix_config.get('name'),
          "aliases": stix_config.get('aliases'),
          "is_family": stix_config.get('is_family', False)
        }

        project: Project = {
          "name": project_config['project']['name'],
          "stix_details": stix_details,
          "sites": []
        }

        logger.debug(f"Parsing sites for {project['name']}")

        # Parse sites for the current project
        for site_name, site_config in project_config.get('sites', {}).items():
          site_mirrors = site_config.get('mirrors', [])
          
          site: Site = {
            "name": site_name,
            "routes": []
          }

          # Get site-level content filters
          site_content_filters = self._parse_filters(site_config.get('content_filters', []))
          
          logger.debug(f"Parsing routes for site {site_name}")

          # Parse routes for the current site
          for route_name, route_config in site_config.get('routes', {}).items():
            take_screenshot = route_config.get('take_screenshot', 
                                           site_config.get('take_screenshot', 
                                                       project_config['project'].get('take_screenshot', False)))
            
            # Get route specific content filters or fall back to site filters
            content_filters = self._parse_filters(route_config.get('content_filters', [])) if 'content_filters' in route_config else site_content_filters
            
            route_path = route_config.get('path', 'index.html').rstrip('/')
            
            # Handle route-specific mirrors
            route_mirrors = route_config.get('mirrors', [])
            if not route_mirrors:
              # If no route-specific mirrors, construct mirrors from site mirrors + route path
              route_mirrors = [urljoin(mirror, route_path) for mirror in site_mirrors]
            
            if not route_mirrors:
              raise ValueError(f"No mirrors found for route '{route_name}' in site '{site_name}'")

            route: Route = {
              "name": route_name,
              "path": route_path,
              "mirrors": route_mirrors,
              "take_screenshot": take_screenshot,
              "content_filters": content_filters
            }

            site['routes'].append(route)
            primary_url = route_mirrors[0] if route_mirrors else ""
            logger.debug(f"Parsed route {route['name']} primary mirror: {primary_url}, {len(route_mirrors)} total mirrors")

          project['sites'].append(site)
          
        self.projects.append(project)

  def _parse_filters(self, filters_data):
    if not filters_data:
      return []
      
    return [
      [re.compile(pattern) for pattern in filter_patterns]
      for filter_patterns in filters_data
    ]



