import re
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Segment:
    """Represents a text segment with its position and content"""
    text: str
    start_pos: int
    end_pos: int


class CitationAwareTokenizer:
    """Splits text into segments based on citation structure, not just punctuation"""
    
    def __init__(self, text: str):
        self.text = text
        self.segments = self._tokenize()
    
    def _tokenize(self) -> List[Segment]:
        """
        Split text into segments intelligently:
        - Use semicolons (;) as primary citation separators
        - Only use periods that END citations (followed by space and capital letter OR end of text)
        - Avoid splitting on periods in abbreviations (e.g., "C. Carroll", "pp.", "p.")
        
        Returns: List of Segment objects
        """
        segments = []
        text = self.text
        current_pos = 0
        current_segment = ""
        
        i = 0
        while i < len(text):
            current_segment += text[i]
            
            # Check for semicolon - primary citation boundary
            if text[i] == ';':
                segment_text = current_segment.strip()
                if segment_text:
                    segments.append(Segment(
                        text=segment_text,
                        start_pos=current_pos,
                        end_pos=i + 1
                    ))
                
                # Skip whitespace
                i += 1
                while i < len(text) and text[i].isspace():
                    i += 1
                current_pos = i
                current_segment = ""
                continue
            
            # Check for period - only split on "real" sentence endings
            elif text[i] == '.':
                # Look ahead to determine if this is a real sentence boundary
                is_real_boundary = self._is_sentence_boundary(text, i)
                
                if is_real_boundary:
                    segment_text = current_segment.strip()
                    if segment_text:
                        segments.append(Segment(
                            text=segment_text,
                            start_pos=current_pos,
                            end_pos=i + 1
                        ))
                    
                    # Skip whitespace
                    i += 1
                    while i < len(text) and text[i].isspace():
                        i += 1
                    current_pos = i
                    current_segment = ""
                    continue
            
            i += 1
        
        # Add remaining text
        if current_segment.strip():
            segments.append(Segment(
                text=current_segment.strip(),
                start_pos=current_pos,
                end_pos=len(text)
            ))
        
        return segments
    
    def _is_sentence_boundary(self, text: str, period_pos: int) -> bool:
        """
        Determine if a period marks a real sentence boundary.
        
        Real boundaries:
        - Period at end of text
        - Period followed by space and capital letter (start of new sentence/citation)
        - Period in format like "), 1997)."
        
        False boundaries:
        - "C. " or "A. " (initials)
        - "pp. " or "p. " (page abbreviation)
        - "et al. " (common abbreviation)
        """
        # Check if at end of text
        if period_pos == len(text) - 1:
            return True
        
        # Look at what comes before the period
        before = text[max(0, period_pos - 3):period_pos].strip()
        
        # Known abbreviations that don't end sentences
        if before in ('pp', 'p', 'al', 'ed', 'vol', 'no'):
            return False
        
        # Single capital letter followed by period = initial (e.g., "C.")
        if period_pos >= 1 and text[period_pos - 1].isupper() and (period_pos == 1 or text[period_pos - 2].isspace()):
            return False
        
        # Check what comes after
        after_pos = period_pos + 1
        
        # Skip spaces
        while after_pos < len(text) and text[after_pos].isspace():
            after_pos += 1
        
        # If followed by capital letter, it's likely a new citation/sentence
        if after_pos < len(text) and text[after_pos].isupper():
            return True
        
        # If we reached end of text, it's a boundary
        if after_pos >= len(text):
            return True
        
        return False
    
    def get_segments(self) -> List[Segment]:
        """Get list of segments"""
        return self.segments
