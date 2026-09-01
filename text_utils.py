"""Türkçe TTS girdisini temizleme, doğrulama ve parçalara ayırma yardımcıları."""

from __future__ import annotations

import re

MAX_WORDS = 1000
DEFAULT_CHUNK_SIZE = 450
MAX_CHUNK_SIZE = 500
_SENTENCE_PATTERN = re.compile(r"[^.!?]+(?:[.!?]+|$)")


class TextValidationError(ValueError):
    """Metin, TTS için geçerli olmadığında yükseltilir."""


def clean_text(text: str) -> str:
    """Boşlukları ve satır sonlarını tek boşluğa indirger."""
    if not isinstance(text, str):
        raise TypeError("Metin bir yazı olmalıdır.")
    return re.sub(r"\s+", " ", text).strip()


def count_words(text: str) -> int:
    """Temizlenmiş metindeki kelime sayısını döndürür."""
    return len(clean_text(text).split())


def validate_text(text: str, max_words: int = MAX_WORDS) -> str:
    """Metni temizler; boş veya fazla uzun metni kullanıcı dostu hatayla reddeder."""
    if max_words < 1:
        raise ValueError("En fazla kelime sayısı en az 1 olmalıdır.")

    cleaned_text = clean_text(text)
    if not cleaned_text:
        raise TextValidationError("Metin alanı boş bırakılamaz.")

    word_count = count_words(cleaned_text)
    if word_count > max_words:
        raise TextValidationError(
            f"Metin en fazla {max_words} kelime olabilir. Girilen metin: {word_count} kelime."
        )
    return cleaned_text


def split_sentences(text: str) -> list[str]:
    """Nokta, ünlem ve soru işaretlerine göre cümleleri ayırır."""
    cleaned_text = clean_text(text)
    if not cleaned_text:
        return []
    return [sentence.strip() for sentence in _SENTENCE_PATTERN.findall(cleaned_text) if sentence.strip()]


def _split_long_sentence(sentence: str, max_chars: int) -> list[str]:
    """Uzun cümleyi hiçbir kelimeyi bölmeden daha küçük parçalara ayırır."""
    words = sentence.split()
    chunks: list[str] = []
    current_words: list[str] = []

    for word in words:
        candidate = " ".join([*current_words, word])
        if current_words and len(candidate) > max_chars:
            chunks.append(" ".join(current_words))
            current_words = [word]
        else:
            current_words.append(word)

    if current_words:
        chunks.append(" ".join(current_words))
    return chunks


def split_text_into_chunks(
    text: str,
    target_chars: int = DEFAULT_CHUNK_SIZE,
    max_chars: int = MAX_CHUNK_SIZE,
) -> list[str]:
    """Metni cümle öncelikli, kelime sınırlarını koruyan TTS parçalarına ayırır.

    Her parça mümkün olduğunda ``target_chars`` civarındadır ve ``max_chars``
    değerini aşmaz. Tek bir kelime ``max_chars`` değerinden uzunsa kelimeyi
    bölmemek için bu istisnaya izin verilir.
    """
    if target_chars < 1 or max_chars < 1 or target_chars > max_chars:
        raise ValueError("Parça hedefi 1 ile maksimum karakter sayısı arasında olmalıdır.")

    cleaned_text = validate_text(text)
    sentences = split_sentences(cleaned_text)
    chunks: list[str] = []
    current_chunk = ""

    for sentence in sentences:
        sentence_parts = _split_long_sentence(sentence, max_chars)
        for sentence_part in sentence_parts:
            candidate = (
                f"{current_chunk} {sentence_part}".strip()
                if current_chunk
                else sentence_part
            )

            if current_chunk and len(candidate) > max_chars:
                chunks.append(current_chunk)
                current_chunk = sentence_part
            else:
                current_chunk = candidate

            if len(current_chunk) >= target_chars:
                chunks.append(current_chunk)
                current_chunk = ""

    if current_chunk:
        chunks.append(current_chunk)
    return chunks
