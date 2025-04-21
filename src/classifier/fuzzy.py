import re
from thefuzz import process, fuzz
from typing import Tuple

from . import Classifier, CategoryMatch, MatchDetails, MatchType, ClassifierResult

class FuzzyClassifier(Classifier):
  min_keyword_length: int
  min_ratio: int
  fuzz_enabled: bool

  def __init__(self, keywords_file: str, min_keword_length = 3, min_ratio = 90, enable_fuzz = True):
    self.min_keyword_length = min_keword_length
    self.min_ratio = min_ratio
    self.fuzz_enabled = enable_fuzz
    
    super().__init__(keywords_file)

  def _preprocess(self, text: str) -> str:
    text = re.sub(r'([.!?])\s', r'\1\n', text)
    text = re.sub(r'([.!?])([A-Z])', r'\n\2', text)
    
    text = text.lower()
    
    # Remove special characters
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespaces (including newlines) with a single space
    return text
  
  def run(self, text: str) -> ClassifierResult:
    # print(self.min_keyword_length)

    found_categories: list[CategoryMatch] = []
    preprocessed_text = self._preprocess(text)
    
    text_lines = [l.strip() for l in preprocessed_text.splitlines() if l.strip()]

    # Split text into sentences by newlines and sentence boundaries
    # text_lines = []
    # for line in preprocessed_text.split('\n'):
    #   if line.strip():
    #     # Split by sentence endings (., !, ?) followed by whitespace
    #     sentences = re.split(r'(?<=[.!?])\s+', line)
    #     text_lines.extend([s for s in sentences if s.strip()])
    
    # print(text_lines)

    found_keywords: set[str] = set()

    for _, row in self.keywords.iterrows():
      category = row['Category']
      keywords = row['Keywords']
      category_matches: list[MatchDetails] = []

      for keyword in keywords:
        
        if not keyword:
          continue

        processed_keyword = self._preprocess(keyword)
        keyword_words = set(processed_keyword.split())
        keyword_no_spaces = processed_keyword.replace(' ', '')

        if not processed_keyword:
          continue

        # # For very short keywords, require exact match as a whole word
        # if len(processed_keyword) <= self.min_keyword_length:
        #   pos = 0
        #   for _, word in enumerate(text_words):
        #     pos += len(word)
        #     if processed_keyword == word.strip():
        #       start_idx = pos
        #       found_keywords.add(keyword)
        #       category_matches.append({
        #         'keyword': keyword,
        #         'matched_text': word,
        #         'start': start_idx,
        #         'end': start_idx + len(word),
        #         'match_type': MatchType.EXACT,
        #         'confidence': 100
        #       })
        #       break
        #   continue

        # Check if keyword is in text (exact match using regex)
        match = re.search(r'\b' + re.escape(processed_keyword) + r'\b', preprocessed_text)
        if match:
          start_idx = match.start()
          found_keywords.add(keyword)
          category_matches.append({
            'keyword': keyword,
            'matched_text': match.group(),
            'start': start_idx,
            'end': match.end(),
            'match_type': MatchType.EXACT,
            'confidence': 100
          })
          continue  
        elif len(processed_keyword) <= self.min_keyword_length:
          continue

        if not self.fuzz_enabled:
          continue
        
        # Count words in the keyword
        keyword_word_count = len(processed_keyword.split())

        # Filter text lines to only include those with at least as many words as the keyword
        filtered_lines = [line for line in text_lines if len(line.split()) >= keyword_word_count and len(line) >= len(processed_keyword)]

        # Only perform matching if we have lines that meet our criteria
        if filtered_lines:
          matches = process.extractBests(processed_keyword, filtered_lines, scorer=fuzz.token_set_ratio, score_cutoff=self.min_ratio)
          
          for match in matches:
            match_text = match[0]
            score = match[1]
            
            # Additional check for multi-word keywords to ensure words are close together
            if len(processed_keyword.split()) > 1:
              
              # Check if all keyword words are within a reasonable distance of each other
              words_found = [word for word in match_text.split() if word in keyword_words]
              
              if len(words_found) < len(keyword_words):
                continue  # Not all keyword words found, skip this match
              
              # Find positions of keyword words in the match text
              positions = []
              for word in keyword_words:
                for i, match_word in enumerate(match_text.split()):
                  if word == match_word:
                    positions.append(i)
                    break
              
              # Check if the words are within max_distance of each other
              max_distance = 5  # Maximum number of words between keyword parts
              if max(positions) - min(positions) > max_distance:
                continue  # Words are too far apart, skip this match
            
            start_idx = preprocessed_text.find(match_text)
            if start_idx >= 0:
              found_keywords.add(keyword)
              category_matches.append({
                'keyword': keyword,
                'matched_text': match_text,
                'start': start_idx,
                'end': start_idx + len(match_text),
                'confidence': score,
                'match_type': MatchType.TOKEN_SORT
              })
            else:
              print("[!] Cannot find index for", keyword, "in", match_text)
          
          if len(matches): 
            continue

        # filter line to only include those with at least as many characters as the keyword
        filtered_lines = [line for line in text_lines if len(line) >= len(keyword_no_spaces)]
        
        # Find matches using token_set_ratio for keyword without spaces
        no_spaces_matches = process.extractBests(keyword_no_spaces, filtered_lines, scorer=fuzz.token_set_ratio, score_cutoff=self.min_ratio)
        
        for match in no_spaces_matches:
          match_text = match[0]
          score = match[1]
          
          start_idx = preprocessed_text.find(match_text)
          if start_idx >= 0:
            found_keywords.add(keyword)
            category_matches.append({
              'keyword': keyword,
              'matched_text': match_text,
              'start': start_idx,
              'end': start_idx + len(match_text),
              'confidence': score,
              'match_type': MatchType.TOKEN_SORT_NO_SPACE
            })
          else:
            print("[!] Cannot find index for", keyword, "in", match_text)

        if len(no_spaces_matches): continue

        # p = process.extractBests(keyword, preprocessed_text.split('\n'), scorer=fuzz.token_set_ratio, score_cutoff=min_ratio)
        # if len(p) > 0:
        #   found_keywords.add(keyword)

        # p = process.extractBests(keyword_no_spaces, preprocessed_text.split('\n'), scorer=fuzz.token_set_ratio, score_cutoff=min_ratio)
        # if len(p) > 0:
        #   found_keywords.add(keyword)

      if category_matches:
        found_categories.append({
          'name': category,
          'details': category_matches,
        })

    return {
      'found_keywords': found_keywords,
      'found_categories': found_categories,
    }

