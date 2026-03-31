from typing import List, Tuple


class SmartTagWrapper:
    """
    Fully safe XML wrapper:
    - Works on visible text only
    - Supports adjacent segments
    - Supports multiple opens/closes at same position
    - Never breaks XML
    """

    def __init__(
        self,
        original_xml: str,
        segment_classifications: List[Tuple[str, int, int, str]],
    ):
        self.original_xml = original_xml

        self.segments = [
            (start, end, label)
            for _, start, end, label in segment_classifications
            if start < end
        ]

        self.wrapped_xml = self._wrap()

    # ---------- MAIN ----------
    def _wrap(self) -> str:
        xml = self.original_xml

        # ---------- BUILD EVENTS ----------
        events = {}
        for start, end, label in self.segments:
            events.setdefault(start, []).append(("open", label))
            events.setdefault(end, []).append(("close", label))

        result = []
        xml_idx = 0
        text_idx = 0

        open_stack = []

        while xml_idx < len(xml):

            # ---------- APPLY EVENTS ----------
            if text_idx in events:

                # CLOSE FIRST
                for action, label in sorted(events[text_idx], key=lambda x: x[0] == "open"):
                    if action == "close" and label in open_stack:
                        result.append(f"</{label}>")
                        open_stack.remove(label)

                # THEN OPEN
                for action, label in events[text_idx]:
                    if action == "open":
                        result.append(f"<{label}>")
                        open_stack.append(label)

            char = xml[xml_idx]

            # ---------- SKIP TAGS ----------
            if char == "<":
                tag_end = xml.find(">", xml_idx)
                if tag_end == -1:
                    result.append(char)
                    xml_idx += 1
                    continue

                result.append(xml[xml_idx:tag_end + 1])
                xml_idx = tag_end + 1
                continue

            # ---------- NORMAL TEXT ----------
            result.append(char)
            text_idx += 1
            xml_idx += 1

        # ---------- CLOSE REMAINING ----------
        while open_stack:
            result.append(f"</{open_stack.pop()}>")

        return "".join(result)

    def get_wrapped_xml(self) -> str:
        return self.wrapped_xml