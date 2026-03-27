import re
from typing import List


class EnhancedClassifier:
    """Classifies segments as reference or commentary with citation awareness"""
    
    # Strong commentary indicators - phrases that start commentary segments
    STRONG_COMMENTARY_PATTERNS = [
        r'^See\s+also:?',
        r'^For\s+an?\s+in-depth',
        r'^In\s+addition',
        r'^Furthermore',
        r'^Moreover',
        r'^Additionally',
    ]
    
    # Reference patterns - things that indicate bibliographic content
    REFERENCE_PATTERNS = [
        r'[A-Z][a-z]+(?:,\s+[A-Z]\.)+',  # Author: Surname, Initials
        r'\(\d{4}\)',  # Year in parentheses
        r'pp?\.\s*\d+',  # Page numbers
        r'https?://',  # URLs
        r'(?:IMF|UNESCO|OECD|Cambridge|Oxford|Palgrave)',  # Organizations/publishers
        r'(?:Working Papers?|Journal|Conference)',  # Publication types
    ]
    
    def __init__(self):
        self.strong_commentary = [re.compile(p, re.IGNORECASE) for p in self.STRONG_COMMENTARY_PATTERNS]
        self.reference = [re.compile(p) for p in self.REFERENCE_PATTERNS]
    
    def classify(self, segment_text: str) -> str:
        """
        Classify a segment as 'reference' or 'commentary'
        
        Args:
            segment_text: The text of the segment (without XML tags)
        
        Returns:
            'reference' or 'commentary'
        """
        segment_text = segment_text.strip()
        
        # Check for strong commentary indicators
        for pattern in self.strong_commentary:
            if pattern.search(segment_text):
                return 'commentary'
        
        # Check reference patterns
        reference_matches = sum(1 for p in self.reference if p.search(segment_text))
        
        # If multiple reference patterns match, it's likely a reference
        if reference_matches >= 2:
            return 'reference'
        
        # If starts with author name pattern and has a year, it's a reference
        if re.search(r'^[A-Z][a-z]+.*\(\d{4}\)', segment_text):
            return 'reference'
        
        # Long text without commentary patterns is likely reference (citations)
        if len(segment_text) > 50:
            return 'reference'
        
        # Short text without patterns defaults to commentary
        if len(segment_text) < 20:
            return 'commentary'
        
        # Default: treat longer text as reference
        return 'reference'
