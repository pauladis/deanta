from typing import List, Tuple


class SmartTagWrapper:
    """Wraps text with classification tags while preserving DOM structure"""

    def __init__(
        self,
        original_xml: str,
        segment_classifications: List[Tuple[str, int, int, str]],
    ):
        self.original_xml = original_xml
        self.segment_classifications = segment_classifications
        self.wrapped_xml = self._wrap()

    def _wrap(self) -> str:
        # Build (start, end, classification)
        segments = [
            (start, end, classification)
            for _, start, end, classification in self.segment_classifications
        ]
        segments.sort(key=lambda x: x[0])

        result = []
        text_idx = 0
        xml_idx = 0
        seg_idx = 0
        current_class = None

        # ---------- SAFE <para> DETECTION ----------
        para_start = self.original_xml.lower().find("<para")
        if para_start != -1:
            para_open_end = self.original_xml.find(">", para_start) + 1
        else:
            para_open_end = 0

        while xml_idx < len(self.original_xml):

            # ---------- CLOSE (handle multiple boundaries) ----------
            while current_class is not None and seg_idx < len(segments):
                seg_start, seg_end, classification = segments[seg_idx]

                if text_idx == seg_end:
                    result.append(f"</{current_class}>")
                    current_class = None
                    seg_idx += 1
                else:
                    break

            # ---------- OPEN ----------
            if seg_idx < len(segments):
                seg_start, seg_end, classification = segments[seg_idx]

                if text_idx == seg_start:
                    # Prevent wrapping <para> itself
                    if xml_idx >= para_open_end:
                        if current_class != classification:
                            if current_class is not None:
                                result.append(f"</{current_class}>")
                            result.append(f"<{classification}>")
                            current_class = classification

            # ---------- COPY ----------
            if self.original_xml[xml_idx] == "<":
                tag_end = self.original_xml.find(">", xml_idx)
                if tag_end != -1:
                    result.append(self.original_xml[xml_idx: tag_end + 1])
                    xml_idx = tag_end + 1
                else:
                    result.append(self.original_xml[xml_idx])
                    xml_idx += 1
            else:
                result.append(self.original_xml[xml_idx])
                text_idx += 1
                xml_idx += 1

        # ---------- FINAL CLOSE ----------
        if current_class is not None:
            result.append(f"</{current_class}>")

        return "".join(result)

    def get_wrapped_xml(self) -> str:
        return self.wrapped_xml