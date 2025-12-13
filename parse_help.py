import string
import os
from pathlib import Path  
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

STOP_WORDS = set(stopwords.words("english"))
PUNCT_TABLE = str.maketrans("", "", string.punctuation)
DIGIT_TABLE = str.maketrans("", "", string.digits)

def normalize_text(text):
    text = text.lower()
    text = text.translate(PUNCT_TABLE)
    text = text.translate(DIGIT_TABLE)
    
    return text.strip()

def normalize(filepath):

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            text = file.read()

        text = text.lower()

        text = text.translate(PUNCT_TABLE)

        text = text.translate(DIGIT_TABLE)

        return text.strip()

    except FileNotFoundError:
        print(f"Error: The file '{filepath}' not found")
        return ""
    except IOError as e:
        print(f"Error reading file '{filepath}': {e}")
        return ""

def tokenize(text):

    tokens = word_tokenize(text)
    filtered_tokens = [
        word for word in tokens if word.lower() not in STOP_WORDS and word.isalpha()
    ]

    return filtered_tokens


def main():
    dir_name = Path("datasets/docs")
    
    if not dir_name.is_dir():
        print(f"Error: Directory '{dir_name}' not found. Please create it or check the path.")
        return

    try:
        all_entries = os.listdir(dir_name)
    except PermissionError:
        print(f"Error: Permission denied for directory: '{dir_name}'")
        return
    
    full_paths = [dir_name / entry for entry in all_entries]
    
    file_paths = sorted([p for p in full_paths if p.is_file()])
    
    if not file_paths:
        print(f"Directory '{dir_name}' contains no files to process.")
        return

    file_to_process = file_paths[0]

    print(f"--- Processing File: {file_to_process.name} ---")
    with open(file_to_process, 'r') as file:
        file_content = file.read()
        print(file_content)


    normalized_text = normalize(file_to_process)
    
    if normalized_text:
        print("\n--- Normalized Output (Snippet) ---")
        print(normalized_text)

    tokens = tokenize(normalized_text)

    print("\n ----- tokens --------")
    print(tokens)
        

if __name__ == "__main__":
    main()
