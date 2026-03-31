import re


class EnhancedClassifier:
    """
    Scoring-based classifier for reference vs commentary.
    More robust for academic text and mixed structures.
    """

    # ---------- PATTERNS ----------

    COMMENTARY_PATTERNS = [
        r'^See\s+also:?',
        r'^In\s+addition',
        r'^Furthermore',
        r'^Moreover',
        r'^Additionally',

        r'^For\s+(?:an?\s+)?(?:in-depth|detailed|full|further)\s+(?:discussion|analysis)',
        r'^For\s+(?:a\s+)?(?:revised|different|alternative)\s+(?:interpretation|view)',
        r'^For\s+(?:discussion|analysis)',
        r'^As\s+(?:discussed|noted|argued)',
        r'^Compare',
        r'^Cf\.',

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

    REFERENCE_PATTERNS = [
        r'\(\d{4}\)',                 # year
        r'pp?\.\s*\d+',               # pages
        r'https?://',
        r'(?:Cambridge|Oxford|Press|Routledge|Palgrave)',
        r'(?:Journal|Conference)',
    ]

    AUTHOR_PATTERN = re.compile(
        r'\b[A-Z][a-z]+(?:\s+[A-Z]\.){1,2}',  # e.g. John D., E. P.
    )

    COMMENTARY_VERBS = re.compile(
        r'\b(argue|suggest|indicate|highlight|provide|examine|explore|discuss|debate|analyze|show|demonstrate)\b',
        re.IGNORECASE
    )

    REFERENCE_TRIGGER = re.compile(
        r'\b(see|cf\.|compare|e\.g\.)\b',
        re.IGNORECASE
    )

    def __init__(self):
        self.commentary = [re.compile(p, re.IGNORECASE) for p in self.COMMENTARY_PATTERNS]
        self.reference = [re.compile(p) for p in self.REFERENCE_PATTERNS]

    # ---------- CLASSIFIER ----------

    def classify(self, segment_text: str) -> str:
        text = segment_text.strip()

        if not text:
            return "commentary"

        reference_score = 0
        commentary_score = 0

        # ---------- HARD RULES ----------

        # "See also:" must be commentary
        if re.match(r'^\s*See\s+also:', text, re.IGNORECASE):
            return "commentary"

        # "see Author" → strong reference
        if re.match(r'^\s*see\s+[A-Z]', text, re.IGNORECASE):
            return "reference"

        # ---------- COMMENTARY SIGNALS ----------

        for pattern in self.commentary:
            if pattern.search(text):
                commentary_score += 2

        if self.COMMENTARY_VERBS.search(text):
            commentary_score += 1

        # ---------- REFERENCE SIGNALS ----------

        for pattern in self.reference:
            if pattern.search(text):
                reference_score += 2

        if self.AUTHOR_PATTERN.search(text):
            reference_score += 2

        if self.REFERENCE_TRIGGER.search(text):
            reference_score += 1

        # ---------- LENGTH HEURISTICS ----------

        if len(text) > 120:
            reference_score += 1  # long citation block

        if len(text) < 25:
            commentary_score += 1

        # ---------- FINAL DECISION ----------

        if reference_score > commentary_score:
            return "reference"

        return "commentary"