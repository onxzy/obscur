from textsearch import TextSearch
from collections import defaultdict
from typing import Tuple

from . import Classifier, CategoryMatch, MatchDetails, MatchType, ClassifierResult

class SimpleClassifier(Classifier): 
  def run(self, text: str) -> ClassifierResult:
    text = self._preprocess(text)

    found_categories: list[CategoryMatch] = []
    found_keywords: set[str] = set()
    for _, row in self.keywords.iterrows():
      category = row['Category']
      keywords = row['Keywords']

      ts = TextSearch(case="ignore", returns="match", replace_foreign_chars=True)
      ts.add(keywords)
      found = ts.findall(text)

      if found:
        match: CategoryMatch = {
          'name': category,
          'details': []
        }
        found_keywords.update(found)
        for f in found:
          match['details'].append({
            'keyword': f,
            'matched_text': f,
            'start': 0,
            'end': 0,
            'confidence': 100,
            'match_type': MatchType.EXACT
          })
        found_categories.append(match)

    return {
      'found_keywords': found_keywords,
      'found_categories': found_categories
    }
