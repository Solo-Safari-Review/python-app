import requests
import json
import re
import emoji
import pandas as pd

from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

def load_indonesian_vocab():
    url = "https://raw.githubusercontent.com/damzaky/kumpulan-kata-bahasa-indonesia-KBBI/master/list_1.0.0.txt"
    response = requests.get(url)
    indonesian_words = response.text.splitlines()
    return set(word.lower() for word in indonesian_words)

def load_slang_dicts():
    combined_dict = {}

    try:
        url1 = "https://raw.githubusercontent.com/okkyibrohim/id-multi-label-hate-speech-and-abusive-language-detection/master/new_kamusalay.csv"
        slang1 = pd.read_csv(url1, header=None, names=['slang', 'formal'], encoding='latin1')
        for _, row in slang1.iterrows():
            slang = row['slang']
            formal = row['formal']
            if pd.notna(slang) and pd.notna(formal):
                combined_dict[slang.strip().lower()] = formal.strip().lower()
    except Exception as e:
        print("Failed to load slang1:", e)

    try:
        url2 = "https://raw.githubusercontent.com/louisowen6/NLP_bahasa_resources/master/combined_slang_words.txt"
        response = requests.get(url2)
        slang2 = json.loads(response.text)
        for slang, formal in slang2.items():
            if isinstance(formal, str):
                combined_dict[slang.strip().lower()] = formal.strip().lower()
    except Exception as e:
        print("Failed to load slang2:", e)

    try:
        url3 = "https://raw.githubusercontent.com/haryoa/indo-collex/main/data/full.csv"
        slang3 = pd.read_csv(url3, encoding='latin1')
        for _, row in slang3.iterrows():
            if 'original-for' in slang3.columns and 'transformed' in slang3.columns:
                formal = row['original-for']
                slang = row['transformed']
                if pd.notna(slang) and pd.notna(formal):
                    combined_dict[slang.strip().lower()] = formal.strip().lower()
    except Exception as e:
        print("Failed to load slang3:", e)

    return combined_dict

def replace_slang_with_formal(sentence, slang_dict):
    words = sentence.split()
    corrected_sentence = []

    for word in words:
        cleaned_word = ''.join(e for e in word if e.isalnum()).lower()
        if cleaned_word in slang_dict:
            corrected_sentence.append(slang_dict[cleaned_word])
        else:
            corrected_sentence.append(word)

    return ' '.join(corrected_sentence)

def normalize_repeated_chars(text):
    return re.sub(r'(\w)\1{2,}', r'\1', text)

# Tangani duplikasi kata khas Indonesia (teman2 -> teman-teman)
def handle_indonesian_duplicates(text):
    parts = re.split(r'(".*?")', text)
    processed_parts = []

    for part in parts:
        if part.startswith('"') and part.endswith('"'):
            processed_parts.append(part)
        else:
            part = re.sub(r'\b(\w+)(2|2an|")\b', r'\1-\1', part)
            processed_parts.append(part)

    return ''.join(processed_parts)

# Inisialisasi stopword remover dan stemmer
factory_stopwords = StopWordRemoverFactory()
stopword_remover = factory_stopwords.create_stop_word_remover()

factory_stemmer = StemmerFactory()
stemmer = factory_stemmer.create_stemmer()

# Fungsi untuk menghapus stopword
def remove_stopwords(text):
    return stopword_remover.remove(text)

# Fungsi untuk lemmatization/stemming
def lemmatize_text(text):
    return stemmer.stem(text)

# Fungsi utama preprocessing
def preprocessing(text):
    slang_dict = load_slang_dicts()
    indonesian_vocab = load_indonesian_vocab()

    clean_text = text.lower()
    clean_text = emoji.replace_emoji(clean_text, replace=' ')
    clean_text = handle_indonesian_duplicates(clean_text)
    clean_text = re.sub(r"(\w+)'s\b", r"\1", clean_text)
    clean_text = replace_slang_with_formal(clean_text, slang_dict)
    clean_text = replace_slang_with_formal(clean_text, slang_dict)
    clean_text = re.sub(r'\n+', ' ', clean_text)
    clean_text = re.sub(r'[^\w\s0-9]', ' ', clean_text)  # Menjaga angka
    clean_text = normalize_repeated_chars(clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    # Stopword removal dan lemmatization
    clean_text = remove_stopwords(clean_text)
    clean_text = lemmatize_text(clean_text)

    return clean_text
