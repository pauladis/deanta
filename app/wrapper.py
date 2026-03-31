from typing import List, Tuple


class SmartTagWrapper:
    """
    Fully safe XML wrapper:
    - Receives segments with positions in text-space (semantic text indices)
    - Inserts tags while preserving XML structure
    - Works by tracking visible text position while iterating through XML
    - Converts text-space event positions to XML insertion points using position_map
    """

    def __init__(
        self,
        original_xml: str,
        segment_classifications: List[Tuple[str, int, int, str]],
        semantic_text: str,
        position_map: List[int],
    ):
        self.original_xml = original_xml
        self.semantic_text = semantic_text
        self.position_map = position_map

        # Build a map of XML insertion positions from text-space positions
        # text_pos_i -> xml_insert_pos
        self.xml_insertion_map = {}
        for text_i in range(len(position_map)):
            self.xml_insertion_map[text_i] = position_map[text_i]
        # Add final position (after last character)
        if position_map:
            self.xml_insertion_map[len(position_map)] = position_map[-1] + 1

        # Build events at each text position
        self.events = {}
        for _, text_start, text_end, label in segment_classifications:
            if text_start < text_end and text_end <= len(position_map):
                self.events.setdefault(text_start, []).append(("open", label))
                self.events.setdefault(text_end, []).append(("close", label))

        self.wrapped_xml = self._wrap()

    # ---------- MAIN ----------
    def _wrap(self) -> str:
        xml = self.original_xml
        result = []
        xml_idx = 0
        text_idx = 0  # Position in semantic text
        open_stack = []

        def apply_events(position):
            """Apply any events at the given position."""
            if position in self.events:
                for action, label in sorted(self.events[position], key=lambda x: (x[0] != "close", x[1])):
                    if action == "close" and label in open_stack:
                        result.append(f"</{label}>")
                        open_stack.remove(label)
                    elif action == "open":
                        result.append(f"<{label}>")
                        open_stack.append(label)

        while xml_idx < len(xml):
            char = xml[xml_idx]

            # ---------- SKIP XML TAGS ----------
            if char == "<":
                tag_end = xml.find(">", xml_idx)
                if tag_end == -1:
                    result.append(char)
                    xml_idx += 1
                    continue

                # Before outputting a closing tag, check for pending events at current text position
                # This ensures semantic content ends before structural tags close
                tag = xml[xml_idx:tag_end + 1]
                if tag.startswith("</"):
                    apply_events(text_idx)

                result.append(tag)
                xml_idx = tag_end + 1
                continue

            # ---------- VISIBLE TEXT CHAR - Apply events BEFORE outputting text ----------
            apply_events(text_idx)

            result.append(char)
            text_idx += 1
            xml_idx += 1

        # ---------- PROCESS FINAL EVENTS (at EOF) ----------
        apply_events(text_idx)

        # ---------- CLOSE REMAINING OPEN TAGS ----------
        while open_stack:
            result.append(f"</{open_stack.pop()}>")

        return "".join(result)

    def get_wrapped_xml(self) -> str:
        return self.wrapped_xml