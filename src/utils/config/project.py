from re import Pattern
from typing import TypedDict, List

from .stix import StixMalware

type ContentFilters = list[list[Pattern]]

class Route(TypedDict):
  name: str
  path: str
  mirrors: list[str]
  take_screenshot: bool
  content_filters: ContentFilters

class Site(TypedDict):
  name: str
  routes: list[Route]

class Project(TypedDict):
  name: str
  stix_details: StixMalware
  sites: list[Site]
