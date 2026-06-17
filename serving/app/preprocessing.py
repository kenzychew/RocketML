"""Text preprocessing shared by training and serving.

The same cleaning must run at train time and at inference time, so it lives in
one place and is imported by both ``model/train.py`` and the serving app.
Cleaning is regex-only (no NLTK) to keep the serving image light.
"""

import re

_HTML = re.compile(r"<[^>]+>")
_URL = re.compile(r"http\S+|www\S+|https\S+", re.MULTILINE)
_EMAIL = re.compile(r"\S+@\S+")
_NON_TEXT = re.compile(r"[^a-zA-Z0-9\s']")
_DOUBLE_APOS = re.compile(r"''")
_LONE_APOS = re.compile(r"\s'\s")
_WHITESPACE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Normalise raw review text for the sentiment model.

    Strips HTML, lowercases, drops URLs/emails, keeps alphanumerics and
    apostrophes, and collapses whitespace. Applied identically at train and
    inference time so the model sees the same text distribution.

    Args:
        text: Raw input text.

    Returns:
        The cleaned text.
    """
    text = _HTML.sub(" ", text)
    text = text.lower()
    text = _URL.sub("", text)
    text = _EMAIL.sub("", text)
    text = _NON_TEXT.sub(" ", text)
    text = _DOUBLE_APOS.sub("", text)
    text = _LONE_APOS.sub(" ", text)
    text = _WHITESPACE.sub(" ", text)
    return text.strip()
