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
        inside_tag = False
        skip_del = False

        while i < len(xml):
            char = xml[i]

            # detect tag start
            if char == "<":
                tag_end = xml.find(">", i)
                tag_content = xml[i:tag_end + 1]

                # detect del span
                if 'class="del"' in tag_content:
                    skip_del = True

                if tag_content.startswith("</span") and skip_del:
                    skip_del = False

                i = tag_end + 1
                continue

            # skip deleted text
            if skip_del:
                i += 1
                continue

            # visible text
            text.append(char)
            position_map.append(i)

            i += 1

        return "".join(text), position_map

    # ---------- TOKENIZATION ----------
    def _tokenize(self) -> List[Segment]:
        segments = []
        text = self.text

        current_start = 0
        current_segment = ""

        i = 0
        while i < len(text):
            char = text[i]
            current_segment += char

            # ---------- SEMICOLON ----------
            if char == ';':
                segments.append(self._build_segment(current_segment, current_start, i))
                i = self._skip_spaces(text, i + 1)
                current_start = i
                current_segment = ""
                continue

            # ---------- PERIOD ----------
            if char == '.' and self._is_sentence_boundary(text, i):
                segments.append(self._build_segment(current_segment, current_start, i))
                i = self._skip_spaces(text, i + 1)
                current_start = i
                current_segment = ""
                continue

            i += 1

        # final segment
        if current_segment.strip():
            segments.append(self._build_segment(current_segment, current_start, len(text) - 1))

        return segments

    # ---------- HELPERS ----------
    def _build_segment(self, segment_text, start, end):
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
        if pos == len(text) - 1:
            return True

        before = text[max(0, pos - 10):pos].strip()
        after = pos + 1

        while after < len(text) and text[after].isspace():
            after += 1

        if re.search(r'\(\d{4}\)$', before):
            return False

        if re.search(r'\b(pp|p|al|ed|vol|no)\.?$', before):
            return False

        if pos >= 1 and text[pos - 1].isupper():
            if pos == 1 or text[pos - 2].isspace():
                return False

        if after < len(text):
            return text[after].isupper()

        return False

    def get_segments(self) -> List[Segment]:
        return self.segments