import re


class EnhancedClassifier:
    """
    Heuristic classifier for reference vs commentary.
    Returns ONLY label (no confidence).
    """

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
        r'\(\d{4}\)',
        r'pp?\.\s*\d+',
        r'https?://',
        r'(?:Cambridge|Oxford|Press|Routledge|Palgrave)',
        r'(?:Journal|Conference)',
    ]

    AUTHOR_PATTERN = re.compile(
        r'\b[A-Z][a-z]+(?:\s+[A-Z]\.){1,2}'
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
        self.reference = [re.compile(p, re.IGNORECASE) for p in self.REFERENCE_PATTERNS]

    def classify(self, text: str) -> str:
        text = text.strip()

        if not text:
            return "commentary"

        # ---------- HARD RULES ----------

        # "See also:" must be commentary (so it can be split later)
        if re.match(r'^\s*See\s+also:', text, re.IGNORECASE):
            return "commentary"

        # DO NOT classify "see X" as reference here
        # → let splitter handle it
        if re.match(r'^\s*see\s+', text, re.IGNORECASE):
            return "commentary"

        # ---------- SCORING ----------
        reference_score = 0
        commentary_score = 0

        # Commentary signals
        for p in self.commentary:
            if p.search(text):
                commentary_score += 2

        if self.COMMENTARY_VERBS.search(text):
            commentary_score += 1

        # Reference signals
        for p in self.reference:
            if p.search(text):
                reference_score += 2

        if self.AUTHOR_PATTERN.search(text):
            reference_score += 2

        # IMPORTANT: "see" should NOT push to reference
        # (splitter handles it instead)

        # Length heuristic
        if len(text) > 120:
            reference_score += 1

        if len(text) < 25:
            commentary_score += 1

        # ---------- DECISION ----------
        if reference_score > commentary_score:
            return "reference"

        return "commentary"