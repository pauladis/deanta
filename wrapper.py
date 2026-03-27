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

        # Find end of opening <para ...>
        para_open_end = self.original_xml.find(">") + 1

        while xml_idx < len(self.original_xml):

            # ---------- CLOSE ----------
            if current_class is not None and seg_idx < len(segments):
                seg_start, seg_end, seg_class = segments[seg_idx]

                if text_idx >= seg_end:
                    result.append(f"</{current_class}>")
                    current_class = None
                    seg_idx += 1
                    continue  # re-evaluate after closing

            # ---------- OPEN ----------
            if seg_idx < len(segments):
                seg_start, seg_end, seg_class = segments[seg_idx]

                if text_idx == seg_start:
                    # Prevent wrapping <para> itself
                    if xml_idx >= para_open_end:
                        if current_class != seg_class:
                            if current_class is not None:
                                result.append(f"</{current_class}>")
                            result.append(f"<{seg_class}>")
                            current_class = seg_class

            # ---------- COPY ----------
            if self.original_xml[xml_idx] == "<":
                tag_end = self.original_xml.find(">", xml_idx)
                if tag_end != -1:
                    result.append(self.original_xml[xml_idx : tag_end + 1])
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