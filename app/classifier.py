import re


class EnhancedClassifier:
    """
    Classifies segments as 'reference' or 'commentary'
    using semantic + citation-aware heuristics.
    """

    # ---------- COMMENTARY PATTERNS ----------
    COMMENTARY_PATTERNS = [
        # Explicit discourse markers
        r'^See\s+also:?',
        r'^In\s+addition',
        r'^Furthermore',
        r'^Moreover',
        r'^Additionally',

        # Academic framing
        r'^For\s+(?:an?\s+)?(?:in-depth|detailed|full|further)\s+(?:discussion|analysis)',
        r'^For\s+(?:a\s+)?(?:revised|different|alternative)\s+(?:interpretation|view)',
        r'^For\s+(?:discussion|analysis)',
        r'^As\s+(?:discussed|noted|argued)',
        r'^Compare',
        r'^Cf\.',

        # Inferred commentary
        r'^Building\s+on',
        r'^It\s+is\s+(?:also\s+)?argued',
        r'^It\s+should\s+be\s+noted',
        r'^Recent\s+(?:studies|scholarship)',
        r'^archival\s+evidence',
        r'^Taken\s+together',
        r'^This\s+(?:topic|has)',
        r'^These\s+works',
        r'^The\s+(?:role|evidence)',
    ]

    # ---------- REFERENCE PATTERNS ----------
    REFERENCE_PATTERNS = [
        r'[A-Z][a-z]+(?:,\s+[A-Z]\.)+',   # Author names
        r'\(\d{4}\)',                    # Year
        r'pp?\.\s*\d+',                  # Page numbers
        r'https?://',                    # URLs
        r'(?:IMF|UNESCO|OECD|Cambridge|Oxford|Palgrave)',
        r'(?:Working Papers?|Journal|Conference)',
    ]

    # ---------- NARRATIVE VERBS ----------
    COMMENTARY_VERBS = re.compile(
        r'\b(argue|suggest|indicate|highlight|provide|examine|explore|discuss|debate|debated|analyze|analyse|show|demonstrate)\b',
        re.IGNORECASE
    )

    # ---------- REFERENCE TRIGGERS ----------
    # These indicate "reference is coming next"
    REFERENCE_INTRO = re.compile(
        r'\b(see|cf\.|compare|e\.g\.)\b',
        re.IGNORECASE
    )

    def __init__(self):
        self.commentary = [re.compile(p, re.IGNORECASE) for p in self.COMMENTARY_PATTERNS]
        self.reference = [re.compile(p) for p in self.REFERENCE_PATTERNS]

    def classify(self, segment_text: str) -> str:
        segment_text = segment_text.strip()

        # ---------- SPECIAL CASES ----------

        # "See also: ..." → commentary (must be split later)
        if re.match(r'^\s*See\s+also:', segment_text, re.IGNORECASE):
            return 'commentary'

        # "see Author..." → reference
        if re.match(r'^\s*see\s+[A-Z]', segment_text, re.IGNORECASE):
            return 'reference'

        # ---------- COMMENTARY (explicit patterns) ----------
        for pattern in self.commentary:
            if pattern.search(segment_text):
                return 'commentary'

        # ---------- COMMENTARY (semantic narrative) ----------
        if self.COMMENTARY_VERBS.search(segment_text):
            return 'commentary'

        # ---------- MIXED CASE DETECTION ----------
        # e.g. "For a revised interpretation, see X"
        if self.REFERENCE_INTRO.search(segment_text):
            # If it starts like a sentence → commentary intro
            if re.match(r'^[A-Z]', segment_text):
                return 'commentary'

        # ---------- REFERENCE ----------
        reference_matches = sum(1 for p in self.reference if p.search(segment_text))

        if reference_matches >= 2:
            return 'reference'

        if re.search(r'^[A-Z][a-z]+.*\(\d{4}\)', segment_text):
            return 'reference'

        # ---------- FALLBACK ----------
        if len(segment_text) < 20 and reference_matches == 0:
            return 'commentary'

        return 'reference'