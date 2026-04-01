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

        # Clamp indices to valid range
        start = max(0, min(start, len(self.text) - 1))
        end = max(0, min(end, len(self.text) - 1))

        # Return positions in text-space (not XML-space)
        # These are indices into self.text (the semantic text)
        return Segment(
            text=segment_text.strip(),
            start_pos=start,
            end_pos=end + 1
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

        # cf. / e.g. / viz. / etc.
        if re.search(r'\b(cf|e\.g|viz|etc)\.?\s*$', before_clean, re.IGNORECASE):
            return False

        # p. / pp.
        if re.search(r'\b(pp|p|vol|no|ed)\.\s*$', before_clean, re.IGNORECASE):
            return False

        # INITIALS: J. / J. C. / R.T. / E. P.
        # This includes cases with multiple initials, even without a surname following yet
        if re.search(r'(?:\b[A-Z]\.\s*){1,4}$', before_clean):
            return False

        # INITIALS + surname (J. C. Davis)
        if re.search(r'(?:\b[A-Z]\.\s*)+[A-Z][a-z]+$', before_clean):
            return False

        # ---------- SPLIT ONLY IF STRONG SIGNAL ----------
        if after < len(text):
            # Additional heuristic: author initials followed by lowercase name
            # e.g., "E. P. Thompson" should not split at "P."
            # If before ends with capital letter (initial) and after starts with capital word
            # then we're likely in an author citation pattern like "E. P. Thompson"
            if before_clean and before_clean[-1].isupper():
                check_after = text[after:min(after + 15, len(text))]
                
                # Does the next word start with capital followed by lowercase?
                # This pattern indicates a proper name, not a new sentence
                if re.match(r'[A-Z][a-z]+', check_after):
                    # Pattern looks like name: "Thompson", "Davis", etc.
                    # Check if we're in a citation context (multiple capitals/periods before)
                    if re.search(r'[A-Z]\. [A-Z]\. ', before_clean + " X. "):
                        # We're in a multi-initial pattern like "E. P. Thompson"
                        return False
                    # Also check if before ends with "X." where X is single capital
                    # This handles the "E. P." -> "Thompson" case where before is "E. P"
                    if re.search(r'[A-Z]\s*$', before_clean):
                        return False

            return (
                text[after].isupper()
                and re.match(r'[A-Z][a-z]+', text[after:])
            )

        return False

    def get_segments(self) -> List[Segment]:
        return self.segments