import re
from typing import List
from dataclasses import dataclass


@dataclass
class Segment:
    text: str
    start_pos: int
    end_pos: int


class CitationAwareTokenizer:
    """
    Splits text into citation-aware segments.
    
    Rules:
    - Primary split: semicolon (;)
    - Period (.) only splits when it's a TRUE boundary between citations
    - Avoid splitting inside single citations (Author → Year → Title → Journal)
    """

    def __init__(self, text: str):
        self.text = text
        self.segments = self._tokenize()

    def _tokenize(self) -> List[Segment]:
        segments = []
        text = self.text

        current_start = 0
        current_segment = ""

        i = 0
        while i < len(text):
            char = text[i]
            current_segment += char

            # ---------- SEMICOLON (SAFE SPLIT) ----------
            if char == ';':
                segments.append(Segment(
                    text=current_segment.strip(),
                    start_pos=current_start,
                    end_pos=i + 1
                ))

                i += 1
                while i < len(text) and text[i].isspace():
                    i += 1

                current_start = i
                current_segment = ""
                continue

            # ---------- PERIOD (SMART SPLIT) ----------
            if char == '.' and self._is_sentence_boundary(text, i):
                segments.append(Segment(
                    text=current_segment.strip(),
                    start_pos=current_start,
                    end_pos=i + 1
                ))

                i += 1
                while i < len(text) and text[i].isspace():
                    i += 1

                current_start = i
                current_segment = ""
                continue

            i += 1

        # ---------- FINAL SEGMENT ----------
        if current_segment.strip():
            segments.append(Segment(
                text=current_segment.strip(),
                start_pos=current_start,
                end_pos=len(text)
            ))

        return segments

    def _is_sentence_boundary(self, text: str, period_pos: int) -> bool:
        """
        Determines if a period is a TRUE boundary between citations.
        """

        # End of text → always boundary
        if period_pos == len(text) - 1:
            return True

        before = text[max(0, period_pos - 10):period_pos]
        after_pos = period_pos + 1

        # Skip whitespace
        while after_pos < len(text) and text[after_pos].isspace():
            after_pos += 1

        # ---------- RULE 1: DO NOT split after year ----------
        # Example: (2010). Important elements...
        if re.search(r'\(\d{4}\)$', before.strip()):
            return False

        # ---------- RULE 2: DO NOT split inside citation flow ----------
        # Example: Title. Journal name...
        if re.search(r'\b[A-Z][a-z]+$', before.strip()) and \
           after_pos < len(text) and text[after_pos].isupper():
            return False

        # ---------- RULE 3: Abbreviations ----------
        if re.search(r'\b(pp|p|al|ed|vol|no)\.?$', before.strip()):
            return False

        # ---------- RULE 4: Initials (C. Smith) ----------
        if period_pos >= 1 and text[period_pos - 1].isupper():
            if period_pos == 1 or text[period_pos - 2].isspace():
                return False

        # ---------- RULE 5: TRUE boundary ----------
        # Only split if next token looks like NEW citation start
        if after_pos < len(text):
            return (
                text[after_pos].isupper() and
                re.match(r'[A-Z][a-z]+', text[after_pos:])
            )

        return False

    def get_segments(self) -> List[Segment]:
        return self.segments