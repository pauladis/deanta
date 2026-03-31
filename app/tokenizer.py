from typing import List
from dataclasses import dataclass
import re


@dataclass
class Segment:
    text: str
    start_pos: int
    end_pos: int


class CitationAwareTokenizer:
    """
    Tokenizes XML text while preserving correct position mapping.

    Improvements:
    - Robust initials handling (J. C. Davis)
    - Safe XML stripping with position map
    - Avoids splitting inside citations
    """

    def __init__(self, xml_text: str):
        self.original_xml = xml_text
        self.text, self.position_map = self._extract_semantic_text(xml_text)
        self.segments = self._tokenize()

    # ---------- EXTRACT TEXT + POSITION MAP ----------
    def _extract_semantic_text(self, xml: str):
        text = []
        position_map = []

        i = 0
        skip_stack = []

        while i < len(xml):
            char = xml[i]

            # ---------- TAG ----------
            if char == "<":
                tag_end = xml.find(">", i)
                if tag_end == -1:
                    break

                tag = xml[i:tag_end + 1].lower()

                # detect deleted span
                if "<span" in tag and 'class="del"' in tag:
                    skip_stack.append("del")

                elif tag.startswith("</span") and skip_stack:
                    skip_stack.pop()

                i = tag_end + 1
                continue

            # ---------- SKIP DELETED ----------
            if skip_stack:
                i += 1
                continue

            # ---------- NORMAL TEXT ----------
            text.append(char)
            position_map.append(i)

            i += 1

        return "".join(text), position_map

    # ---------- TOKENIZATION ----------
    def _tokenize(self) -> List[Segment]:
        segments = []
        text = self.text

        current_start = 0
        buffer = ""

        i = 0
        while i < len(text):
            char = text[i]
            buffer += char

            # ---------- SEMICOLON ----------
            if char == ';':
                segments.append(self._build_segment(buffer, current_start, i))
                i = self._skip_spaces(text, i + 1)
                current_start = i
                buffer = ""
                continue

            # ---------- PERIOD ----------
            if char == '.' and self._is_sentence_boundary(text, i):
                segments.append(self._build_segment(buffer, current_start, i))
                i = self._skip_spaces(text, i + 1)
                current_start = i
                buffer = ""
                continue

            i += 1

        # ---------- FINAL ----------
        if buffer.strip():
            segments.append(self._build_segment(buffer, current_start, len(text) - 1))

        return segments

    # ---------- BUILD SEGMENT ----------
    def _build_segment(self, segment_text, start, end):
        if not segment_text.strip():
            return Segment("", 0, 0)

        start = max(0, min(start, len(self.position_map) - 1))
        end = max(0, min(end, len(self.position_map) - 1))

        return Segment(
            text=segment_text.strip(),
            start_pos=self.position_map[start],
            end_pos=self.position_map[end] + 1
        )

    def _skip_spaces(self, text, i):
        while i < len(text) and text[i].isspace():
            i += 1
        return i

    # ---------- SENTENCE BOUNDARY ----------
    def _is_sentence_boundary(self, text: str, pos: int) -> bool:
        if pos >= len(text) - 1:
            return True

        before = text[max(0, pos - 20):pos]
        after = pos + 1

        while after < len(text) and text[after].isspace():
            after += 1

        before_clean = before.strip()

        # ---------- DO NOT SPLIT ----------

        # (1999)
        if re.search(r'\(\d{4}\)\s*$', before_clean):
            return False

        # p. / pp.
        if re.search(r'\b(pp|p|vol|no|ed)\.\s*$', before_clean, re.IGNORECASE):
            return False

        # INITIALS: J. / J. C. / R.T.
        if re.search(r'(?:\b[A-Z]\.\s*){1,3}$', before_clean):
            return False

        # INITIALS + surname (J. C. Davis)
        if re.search(r'(?:\b[A-Z]\.\s*)+[A-Z][a-z]+$', before_clean):
            return False

        # ---------- SPLIT ONLY IF STRONG SIGNAL ----------
        if after < len(text):
            return (
                text[after].isupper()
                and re.match(r'[A-Z][a-z]+', text[after:])
            )

        return False

    def get_segments(self) -> List[Segment]:
        return self.segments