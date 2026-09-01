"""text_utils yardımcılarının birim testleri."""

from __future__ import annotations

import unittest

from text_utils import (
    MAX_WORDS,
    TextValidationError,
    clean_text,
    count_words,
    split_sentences,
    split_text_into_chunks,
    validate_text,
)


class TextUtilsTests(unittest.TestCase):
    def test_clean_text_normalizes_spaces_and_newlines(self) -> None:
        text = "  Merhaba\r\n\r\n  Türkiye!\n\nNasılsın?  "

        self.assertEqual(clean_text(text), "Merhaba Türkiye! Nasılsın?")

    def test_count_words_ignores_extra_whitespace(self) -> None:
        self.assertEqual(count_words("bir  iki\nüç\t dört"), 4)

    def test_validate_text_rejects_empty_text(self) -> None:
        with self.assertRaisesRegex(TextValidationError, "boş"):
            validate_text(" \n\t ")

    def test_validate_text_rejects_more_than_max_words(self) -> None:
        too_long_text = " ".join(["kelime"] * (MAX_WORDS + 1))

        with self.assertRaisesRegex(TextValidationError, "1000"):
            validate_text(too_long_text)

    def test_split_sentences_uses_terminal_punctuation(self) -> None:
        text = "Merhaba dünya. Bugün nasılsın? Harika!"

        self.assertEqual(
            split_sentences(text),
            ["Merhaba dünya.", "Bugün nasılsın?", "Harika!"],
        )

    def test_chunks_preserve_words_and_maximum_length(self) -> None:
        sentence = "Bu cümle TTS için düzenli biçimde parçalara ayrılmalıdır."
        text = " ".join([sentence] * 30)
        cleaned_text = clean_text(text)

        chunks = split_text_into_chunks(text, target_chars=350, max_chars=500)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 500 for chunk in chunks))
        self.assertEqual(" ".join(chunks), cleaned_text)

    def test_long_sentence_never_splits_words(self) -> None:
        words = [f"kelime{i}" for i in range(100)]
        text = " ".join(words) + "."

        chunks = split_text_into_chunks(text, target_chars=100, max_chars=120)

        self.assertEqual(" ".join(chunks), clean_text(text))
        self.assertTrue(all(len(chunk) <= 120 for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
