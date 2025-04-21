import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from Levenshtein import distance as levenshtein_distance
import difflib

# 0 - Reading file
# -------------------

def read_file(file_path : str) -> str:
    with open(file_path, 'r', encoding='utf-8') as fichier:
        return fichier.read()

# 1 - Pre Processing : cleaning text from stop words and punctuation and accents
# --------------------------------------------------------------------------------

# Match the . and , preceded AND followed by a number : (?<=\d)[\.,](?=\d)
# Match the % preceded by a number : (?<=\d)[\%]
# Match a single character not present in the list after the ^ symbol : [^\w\s\.,%]
# We replace = by ! to keep the decimal numbers and the percentage.


# Downloading stop words and tokenizer
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')

def preprocess_text(text : str , language : str = 'english' ) -> list[str] :

    # Delete punctuation and special characters
    text_cleaned = re.sub(r'[^\w\s\.,%]|(?<!\d)[\%]|(?<!\d)[\.,](?!\d)', '', text)
    
    # Tokenise et lowercase
    words = word_tokenize(text_cleaned.lower())
    
    # Load stop words in the desired language
    stop_words = set(stopwords.words(language))
    
    # Delete stop words
    filtered_words = [word for word in words if word not in stop_words]
    
    return filtered_words

# 2 - Jaccard comparison : is there new elements in the new set ?
# ----------------------------------------------------------------


def jaccard_distance(old_tokens : list[str], new_tokens : list[str]) -> float:
    # Jaccard distance between two sets
    old_set = set(old_tokens)
    new_set = set(new_tokens)
    intersection = len(old_set.intersection(new_set))
    union = len(old_set.union(new_set))
    if union == 0: return 0  # Both sets are empty, so they are identical
    return 1 - intersection / union

def jaccard_comparison(tokens : list[str], new_tokens : list[str]) -> bool:
    # Determine if the new set contains elements that are not in the original set
    old_set = set(tokens)
    new_set = set(new_tokens)
    if jaccard_distance(tokens, new_tokens) > 0:
        return not(new_set.issubset(old_set))
    return False

# 3 - Levenshtein comparison : how many modifications are needed to transform the old set into the new set ?
# ------------------------------------------------------------------------------------------------------------


def levenshtein_comparison(old_tokens : list[str], new_tokens : list[str]) -> bool:
    # Levenshtein distance between two sets
    old_text = ' '.join(old_tokens)
    new_text = ' '.join(new_tokens)
    if levenshtein_distance(old_text, new_text) > 40: # Average number of characters in a sentence is 47 according Mozilla
        return True
    return False

# 4 - Differences between sets
# ------------------------------


def differences_sets(old_tokens : list[str], new_tokens : list[str]) -> tuple[list[str], list[str]]:
    old_set = set(old_tokens)
    new_set = set(new_tokens)

    # Words exclusive to old_set
    exclusive_old_set = old_set - new_set

    # Words exclusive to new_set
    exclusive_new_set = new_set - old_set

    return list(exclusive_old_set), list(exclusive_new_set)

# 5 - Diffing texts
# ------------------


def diffing_texts(text1: str, text2: str) -> tuple[bool, str]:
    """
    Compare two texts and indicates if a modification is detected via Jaccard and Levenshtein.
    Returns a tuple (modification_detected, summary_of_modifications).
    """
    # Preprocessing
    tokens1 = preprocess_text(text1)
    tokens2 = preprocess_text(text2)

    # Changes 
    has_jaccard_changes = jaccard_comparison(tokens1, tokens2)
    has_levenshtein_changes = levenshtein_comparison(tokens1, tokens2)
    modification_detected = has_jaccard_changes and has_levenshtein_changes

    # Differences gathering
    if modification_detected:
        text1_lines = text1.splitlines()
        text2_lines = text2.splitlines()
    
        diff = difflib.unified_diff(text1_lines, text2_lines, lineterm='', fromfile='Last Version', tofile='Today Version')
        
        summary = ('\n'.join(diff))
    else:
        summary = "No modification detected."

    return modification_detected, summary 

"""
Differences between the texts:
--- Last Version
+++ Today Version
@@ -103,6 +103,34 @@ => @@-{beginning line},{length} +{beginning line},{length} @@
"""