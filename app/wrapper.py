from typing import List, Tuple
from lxml import etree


class SmartTagWrapper:
    """
    XML-safe wrapper using lxml.

    Wraps segments with <reference> / <commentary> without breaking structure.
    """

    def __init__(
        self,
        original_xml: str,
        segment_classifications: List[Tuple[str, int, int, str]],
    ):
        self.original_xml = original_xml
        self.segment_classifications = sorted(
            segment_classifications, key=lambda x: x[1]
        )
        self.wrapped_xml = self._wrap()

    def _wrap(self) -> str:
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(self.original_xml.encode("utf-8"), parser)

        # Flatten text nodes with positions
        nodes = []
        self._collect_text_nodes(root, nodes)

        # Apply wrapping
        for text, start, end, classification in self.segment_classifications:
            self._apply_wrap(nodes, start, end, classification)

        return etree.tostring(root, encoding="unicode")

    def _collect_text_nodes(self, element, nodes, offset=0):
        """
        Collect all text and tail nodes with global offsets.
        """
        if element.text:
            length = len(element.text)
            nodes.append({
                "element": element,
                "type": "text",
                "start": offset,
                "end": offset + length
            })
            offset += length

        for child in element:
            offset = self._collect_text_nodes(child, nodes, offset)

            if child.tail:
                length = len(child.tail)
                nodes.append({
                    "element": child,
                    "type": "tail",
                    "start": offset,
                    "end": offset + length
                })
                offset += length

        return offset

    def _apply_wrap(self, nodes, start, end, classification):
        """
        Wrap relevant parts of text nodes.
        """
        for node in nodes:
            node_start = node["start"]
            node_end = node["end"]

            # no overlap
            if end <= node_start or start >= node_end:
                continue

            element = node["element"]
            node_type = node["type"]

            text = element.text if node_type == "text" else element.tail
            if not text:
                continue

            # local offsets
            local_start = max(0, start - node_start)
            local_end = min(len(text), end - node_start)

            before = text[:local_start]
            middle = text[local_start:local_end]
            after = text[local_end:]

            # create wrapper element
            wrapper = etree.Element(classification)
            wrapper.text = middle

            if node_type == "text":
                element.text = before
                element.insert(0, wrapper)
                wrapper.tail = after
            else:
                element.tail = before
                parent = element.getparent()
                index = parent.index(element)
                parent.insert(index + 1, wrapper)
                wrapper.tail = after

    def get_wrapped_xml(self) -> str:
        return self.wrapped_xml