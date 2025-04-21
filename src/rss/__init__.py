import os
import xml.etree.ElementTree as ET
import datetime
import hashlib
import json
from urllib.parse import urljoin

from typing import Dict, Optional, Tuple

from classifier import CategoryMatch
from .formatter import HtmlFormatter
from .stix import StixBuilder
from utils.config import Project, Site, Route, Config


# Update to use environment variable with default fallback
cwd = os.getcwd()
rss_folder = os.environ.get("RSS_FOLDER", os.path.join(cwd, 'rss'))

class RSSFeed:
  formater: HtmlFormatter
  stix_builder: StixBuilder
  config: Config  # Store the full config object instead of just the server URL

  def __init__(self, config: Config):
    self.formater = HtmlFormatter()
    self.stix_builder = StixBuilder()
    self.config = config
    os.makedirs(rss_folder, exist_ok=True)

  def _get_feed_path(self, project: Project) -> str:
    feed_path = os.path.join(rss_folder, project['name'])
    os.makedirs(feed_path, exist_ok=True)
    return os.path.join(feed_path, "feed.xml")
    
  def _get_stix_folder(self, project: Project) -> str:
    project_stix_folder = os.path.join(rss_folder, project['name'], "stix2")
    os.makedirs(project_stix_folder, exist_ok=True)
    return project_stix_folder
    
  def _get_stix_path(self, project: Project, guid: str) -> str:
    return os.path.join(self._get_stix_folder(project), f"{guid}.json")

  def _create_feed(self, project: Project):
    path = self._get_feed_path(project)
        
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    
    title = ET.SubElement(channel, "title")
    title.text = project['name']

    author = ET.SubElement(channel, "author")
    author.text = "TorScraper"
    
    link = ET.SubElement(channel, "link")
    link.text = project.get('url', '')
    
    description = ET.SubElement(channel, "description")
    description.text = f"{project['name']} RSS Feed"
    
    tree = ET.ElementTree(rss)
    tree.write(os.path.realpath(path), encoding="utf-8", xml_declaration=True)

  def _export_stix(self, project: Project, guid: str, ttps: list[CategoryMatch], 
                          capacities: list[CategoryMatch]) -> Tuple[str, str]:
    
    # Génération et sérialisation des objets STIX par StixBuilder
    stix_json = self.stix_builder.run(project, ttps, capacities)
    stix_file_path = self._get_stix_path(project, guid)

    # Sauvegarde du fichier JSON
    with open(stix_file_path, 'w', encoding='utf-8') as file:
      file.write(stix_json)
    
    # Construit l'URL complète en utilisant urljoin pour une construction propre de l'URL
    relative_path = os.path.relpath(stix_file_path, rss_folder)
    # Pas de fallback - on suppose que server_url est obligatoire
    full_url = urljoin(self.config.rss['server_url'], relative_path)
    
    return stix_file_path, full_url

  def add_entry(self, project: Project, site: Site, route: Route, mirror_url: str, 
                page_text: str, 
                ttps: list[CategoryMatch], capacities: list[CategoryMatch], 
                prev_ttps: Optional[list[CategoryMatch]] = None, prev_capacities: Optional[list[CategoryMatch]] = None,
                summary: Optional[str] = None) -> None:
        
    path = self._get_feed_path(project)
    if not os.path.exists(path):
      self._create_feed(project)
        
    tree = ET.parse(path)
    root = tree.getroot()
        
    channel = root.find("channel")
    if channel is None:
      channel = ET.SubElement(root, "channel")

    now = datetime.datetime.now()
        
    # Create new item
    new_item = ET.Element("item")
    
    # Title
    title = ET.SubElement(new_item, "title")
    title.text = f"{site['name']}/{route['name']} Update" # TODO: Change prefix to FirstScrape on first scrape
    
    # Link to the monitored page
    link = ET.SubElement(new_item, "link")
    link.text = mirror_url

    # Guid : unique identifier by hashing project, site, route, URL and date
    guid = ET.SubElement(new_item, "guid")
    guid_string = f"{project['name']}-{site['name']}-{route['name']}-{mirror_url}-{now.isoformat()}"
    guid_hash = hashlib.sha256(guid_string.encode()).hexdigest()
    guid.text = guid_hash
    
    # Publication date
    pubDate = ET.SubElement(new_item, "pubDate")
    pubDate.text = now.isoformat()
    
    # Génération du fichier STIX JSON et récupération de l'URL complète
    stix_file_path, stix_file_url = self._export_stix(project, guid_hash, ttps, capacities)
    
    # Ajout de la pièce jointe STIX au format JSON avec une URL complète
    enclosure = ET.SubElement(new_item, "enclosure")
    enclosure.set("url", stix_file_url)
    enclosure.set("type", "application/json")
    enclosure.set("length", str(os.path.getsize(stix_file_path)))

    # Description with TTPs and capacities
    description = ET.SubElement(new_item, "description")
    description.text = self.formater.run(page_text, ttps, capacities, stix_file_url, prev_ttps, prev_capacities, summary)

    channel.insert(0, new_item)  # Add at the top
    
    # Limit the number of items in the feed
    max_items = self.config.rss['max_items']
    items = channel.findall('item')
    if len(items) > max_items:
      # Get items that need to be removed
      items_to_remove = items[max_items:]
      for item in items_to_remove:
        # Check for STIX file to remove
        enclosure = item.find("enclosure")
        if enclosure is not None and enclosure.get("type") == "application/json":
          guid_element = item.find("guid")
          if guid_element is not None and guid_element.text:
            # Try to remove the associated STIX file
            try:
              stix_path = self._get_stix_path(project, guid_element.text)
              if os.path.exists(stix_path):
                os.remove(stix_path)
            except Exception as e:
              # Just log the error, don't fail the feed update
              print(f"Error removing STIX file: {e}")
        
        # Remove the item from the feed
        channel.remove(item)
    
    tree.write(path, encoding="utf-8", xml_declaration=True)


