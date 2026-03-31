from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Tuple
import re

from .tokenizer import CitationAwareTokenizer
from .classifier import EnhancedClassifier
from .wrapper import SmartTagWrapper


# ---------- APP ----------

app = FastAPI(
    title="Deanta API",
    description="Reference vs Commentary classifier (XML output)",
    version="2.0.0"
)

classifier = EnhancedClassifier()


# ---------- MODELS ----------

class ParagraphInput(BaseModel):
    text: str


# ---------- SPLITTING ----------

REFERENCE_TRIGGERS = re.compile(
    r'\b(see|cf\.|compare|e\.g\.)\b',
    re.IGNORECASE
)

TRAILING_COMMENTARY = re.compile(
    r'(.*?)(,\s*(for\s+.+))$',
    re.IGNORECASE
)


def split_commentary_phrases(
    segments: List[Tuple[str, int, int, str]]
) -> List[Tuple[str, int, int, str]]:

    result = []

    for text, start, end, label in segments:
        # CRITICAL: DO NOT strip text - it breaks position tracking!
        # Work with original text to preserve all whitespace

        # ---------- CASE 1: split if it STARTS with trigger ----------
        # Use lstrip to find the trigger at the beginning (ignoring leading whitespace)
        text_lstripped = text.lstrip()
        match = re.match(r'^(see|cf\.|compare|e\.g\.)\b', text_lstripped, re.IGNORECASE)

        if label == "commentary" and match:
            # Find how much whitespace was stripped
            ws_prefix_len = len(text) - len(text_lstripped)
            
            # The trigger starts after the whitespace
            trigger_start = ws_prefix_len + match.start()
            trigger_end = ws_prefix_len + match.end()
            
            before = text[:trigger_start]  # Keep original (with whitespace)
            after = text[trigger_start:]   # Keep original (with whitespace)

            split_pos = start + trigger_start

            if before.strip():  # Only append if non-empty after stripping
                result.append((before, start, split_pos, "commentary"))

            # After extraction, check the extracted reference for trailing commentary
            ref_text = after
            ref_start = split_pos
            tail = re.match(r'^(.*?,\s+)(for\s+.+)$', ref_text, re.IGNORECASE)
            if tail:
                ref_part = tail.group(1)
                comment_part = tail.group(2)
                split_idx_2 = ref_text.lower().find(comment_part.lower())
                split_pos_2 = ref_start + split_idx_2
                result.append((ref_part, ref_start, split_pos_2, "reference"))
                result.append((comment_part, split_pos_2, end, "commentary"))
            else:
                result.append((after, split_pos, end, "reference"))
            continue

        # ---------- CASE 2: trailing commentary ----------
        if label == "reference":
            tail = re.match(r'^(.*?,\s+)(for\s+.+)$', text, re.IGNORECASE)

            if tail:
                ref_part = tail.group(1)
                comment_part = tail.group(2)

                split_idx = text.lower().find(comment_part.lower())
                split_pos = start + split_idx

                result.append((ref_part, start, split_pos, "reference"))
                result.append((comment_part, split_pos, end, "commentary"))
                continue

        result.append((text, start, end, label))

    return result


# ---------- PIPELINE ----------

def classify_paragraph(
    paragraph_text: str
) -> Tuple[str, List[Tuple[str, int, int, str]]]:

    tokenizer = CitationAwareTokenizer(paragraph_text)
    segments = tokenizer.get_segments()

    classified_segments = []

    for seg in segments:
        label = classifier.classify(seg.text)

        classified_segments.append((
            seg.text,
            seg.start_pos,
            seg.end_pos,
            label
        ))

    # ---------- SPLIT MIXED SEGMENTS ----------
    classified_segments = split_commentary_phrases(classified_segments)

    # ---------- WRAP XML ----------
    wrapper = SmartTagWrapper(
        paragraph_text,
        classified_segments,
        tokenizer.text,
        tokenizer.position_map
    )
    wrapped_xml = wrapper.get_wrapped_xml()

    return wrapped_xml, classified_segments


# ---------- API ----------

@app.post("/parse-paragraph")
async def parse_paragraph(input_data: ParagraphInput):

    if not input_data.text or not input_data.text.strip():
        raise HTTPException(status_code=400, detail="Paragraph text cannot be empty")

    try:
        wrapped_xml, _ = classify_paragraph(input_data.text)

        return Response(
            content=wrapped_xml,
            media_type="application/xml",
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing paragraph: {str(e)}"
        )


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Deanta API is running",
        "output": "XML"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ---------- LOCAL RUN ----------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)