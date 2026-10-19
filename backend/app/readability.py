# CareBridge Readability Assessment Engine
# Implements PRD Section 8, 11, 12, 18, and FR-11

import re
from typing import Dict, Tuple


def count_syllables_en(word: str) -> int:
    # Syllable counter for English clinical text
    w = word.lower().strip(".,;:!?()[]\"'")
    if not w:
        return 0
    if len(w) <= 3:
        return 1

    # Remove silent e
    if w.endswith("e") and not w.endswith("le") and not w.endswith("ee"):
        w = w[:-1]

    # Count vowel sequences
    vowels = re.findall(r"[aeiouy]+", w)
    count = len(vowels)
    return max(1, count)


def flesch_kincaid_grade(text: str) -> float:
    # Computes Flesch-Kincaid Grade Level for English text:
    # 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
    # Target: Class 8 or below
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return 0.0

    # Split sentences by terminators or line breaks
    sentences = []
    for ln in lines:
        sents = re.split(r"[.!?]+", ln)
        for s in sents:
            if s.strip():
                sentences.append(s.strip())

    num_sentences = max(1, len(sentences))

    # Clean words
    words = []
    for s in sentences:
        for w in s.split():
            clean = re.sub(r"[^A-Za-z0-9]", "", w)
            if clean:
                words.append(clean)

    num_words = max(1, len(words))
    total_syllables = sum(count_syllables_en(w) for w in words)

    grade = 0.39 * (num_words / num_sentences) + 11.8 * (total_syllables / num_words) - 15.59
    # Clamp to reasonable pedagogical bounds
    return round(max(1.0, min(16.0, grade)), 1)


def telugu_readability_proxy(text: str) -> Dict[str, float]:
    # PRD Section 12: No accepted grade formula exists for Telugu.
    # Reports standard linguistic proxy metrics clearly labelled as proxy:
    # - Average words per sentence
    # - Proportion of short words (<= 6 characters)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {
            "avg_words_per_sentence": 0.0,
            "short_word_ratio": 0.0,
            "is_proxy": True,
            "notice": "Standard grade formula does not exist for Telugu; reported as linguistic proxy.",
        }

    sentences = []
    for ln in lines:
        sents = re.split(r"[.!?]+", ln)
        for s in sents:
            if s.strip():
                sentences.append(s.strip())

    num_sentences = max(1, len(sentences))
    words = [w for s in sentences for w in s.split() if w]
    num_words = max(1, len(words))

    short_words = sum(1 for w in words if len(w) <= 6)
    short_ratio = round(short_words / num_words, 2)
    avg_words = round(num_words / num_sentences, 1)

    return {
        "avg_words_per_sentence": avg_words,
        "short_word_ratio": short_ratio,
        "is_proxy": True,
        "notice": "Standard grade formula does not exist for Telugu; reported as linguistic proxy.",
    }
