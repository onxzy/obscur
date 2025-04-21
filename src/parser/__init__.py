import re

from bs4 import BeautifulSoup, PageElement
from bs4.element import Tag

from utils.config.project import ContentFilters

class Parser():
  _filters: ContentFilters

  def __init__(self, filters: ContentFilters):
    self._filters = filters

  def _filter_function(self, tag: Tag):
    if not tag.has_attr('class'): return False
    classes = tag['class']
    return any([
      all([
        any([
          re.search(pattern, c)
        for c in classes
        ])
      for pattern in filter
      ])
    for filter in self._filters
    ])

  def parse_html(self, html_content: str):
    soup = BeautifulSoup(html_content, 'lxml')

    if len(self._filters) == 0:
      return soup.get_text()
    
    content: list[PageElement]
    content = soup.find_all(self._filter_function)
    return '\n'.join([c.get_text() for c in content])
