import os
import pandas as pd
from typing import List, TypedDict, Tuple
from enum import Enum

class MatchType(str, Enum):
  EXACT = "exact"
  EXACT_REGEX = "exact_regex"
  EXACT_NO_SPACE = "exact_no_space"
  TOKEN_SET = "token_set"
  TOKEN_SORT = "token_sort"
  TOKEN_SET_NO_SPACE = "token_set_no_space"
  TOKEN_SORT_NO_SPACE = "token_sort_no_space"

class MatchDetails(TypedDict):
  keyword: str
  matched_text: str
  start: int
  end: int
  confidence: int
  match_type: MatchType

class CategoryMatch(TypedDict):
  name: str
  details: List[MatchDetails] 

class ClassifierResult(TypedDict):
  found_keywords: set[str]
  found_categories: List[CategoryMatch]

class Classifier:
  keywords: pd.DataFrame

  def __init__(self, keywords_file: str):
    self.keywords = pd.read_csv(keywords_file, encoding='utf-8')
    self.keywords['Keywords'] = self.keywords['Keywords'].apply(
      lambda x: [
        k.strip()
        for k in x.lower().split(',')
      ] if pd.notna(x) else [])

  def _preprocess(self, text: str) -> str:
    return text.lower()

  def run(self, text: str) -> ClassifierResult:
    raise NotImplementedError()


