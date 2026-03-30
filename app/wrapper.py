from typing import List, Tuple
import logging

logger = logging.getLogger("deanta")


class SmartTagWrapper:
    """
    Wraps text segments with classification tags while preserving DOM structure.
    
    This class carefully inserts <reference> and <commentary> tags around
    classified text segments while maintaining the integrity of existing XML/HTML tags.
    
    Attributes:
        original_xml: The original paragraph text with XML/HTML tags
        segment_classifications: List of (text, start, end, classification) tuples
        wrapped_xml: The result after wrapping with tags
    """

    def __init__(
        self,
        original_xml: str,
        segment_classifications: List[Tuple[str, int, int, str]],
    ) -> None:
        if not isinstance(original_xml, str):
            raise TypeError("original_xml must be a string")
        if not isinstance(segment_classifications, list):
            raise TypeError("segment_classifications must be a list")

        self.original_xml: str = original_xml
        self.segment_classifications: List[Tuple[str, int, int, str]] = segment_classifications
        self.wrapped_xml: str = self._wrap()

    def _wrap(self) -> str:
        """
        Wrap segments with classification tags while preserving XML/HTML structure.
        
        Returns:
            str: The wrapped XML with <reference> and <commentary> tags inserted
            
        Raises:
            ValueError: If segment positions are invalid or overlapping
        """
        # Validate segments
        for text, start, end, classification in self.segment_classifications:
            if not isinstance(start, int) or not isinstance(end, int):
                logger.error(f"Invalid segment positions: start={start}, end={end}")
                raise ValueError("Segment start and end must be integers")
            if start < 0 or end < 0 or start > end:
                logger.error(f"Invalid segment range: start={start}, end={end}")
                raise ValueError(f"Invalid segment range: {start}-{end}")
            if end > len(self.original_xml):
                logger.error(f"Segment end {end} exceeds text length {len(self.original_xml)}")
                raise ValueError(f"Segment end {end} exceeds text length")

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
        """Retrieve the wrapped XML result.
        
        Returns:
            str: The paragraph text with classification tags inserted
        """
        return self.wrapped_xml
