from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
from typing import List, Tuple

from .tokenizer import CitationAwareTokenizer
from .classifier import EnhancedClassifier
from .wrapper import SmartTagWrapper


app = FastAPI(
    title="Deanta API",
    description="API for classifying reference vs commentary content in paragraphs",
    version="1.0.0"
)

classifier = EnhancedClassifier()


# ---------- MODELS ----------

class ParagraphInput(BaseModel):
    text: str


class ParagraphOutput(BaseModel):
    classified_paragraph: str


# ---------- SPLITTING LOGIC ----------

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
    """
    Robust splitter that:
    - Handles multiple "see / cf. / compare"
    - Splits commentary → reference
    - Splits reference → trailing commentary
    """

    result = []

    for text, start, end, classification in segments:

        remaining_text = text
        offset_base = start

        while True:
            match = REFERENCE_TRIGGERS.search(remaining_text)

            # ---------- NO MORE SPLITS ----------
            if not match:
                result.append((remaining_text, offset_base, end, classification))
                break

            trigger_start = match.start()

            before = remaining_text[:trigger_start].strip()
            after = remaining_text[trigger_start:].strip()

            split_pos = offset_base + trigger_start

            # ---------- COMMENTARY → REFERENCE ----------
            if before:
                result.append((before, offset_base, split_pos, 'commentary'))

            # Now process the "after" part
            # Check trailing commentary inside reference
            tail_match = TRAILING_COMMENTARY.match(after)

            if tail_match:
                ref_part = tail_match.group(1).strip()
                comment_part = tail_match.group(2).strip()

                ref_end_pos = split_pos + len(ref_part)

                result.append((ref_part, split_pos, ref_end_pos, 'reference'))
                result.append((comment_part, ref_end_pos, end, 'commentary'))
                break

            else:
                result.append((after, split_pos, end, 'reference'))
                break

    return result


# ---------- CORE PIPELINE ----------

def classify_paragraph(
    paragraph_text: str
) -> Tuple[str, List[Tuple[str, int, int, str]]]:
    """
    Full pipeline:
    XML → Tokenize → Classify → Split → Wrap
    """

    tokenizer = CitationAwareTokenizer(paragraph_text)
    segments = tokenizer.get_segments()

    classified_segments = []

    for segment in segments:
        classification = classifier.classify(segment.text)

        classified_segments.append((
            segment.text,
            segment.start_pos,
            segment.end_pos,
            classification
        ))

    # 🔥 critical step
    classified_segments = split_commentary_phrases(classified_segments)

    wrapper = SmartTagWrapper(paragraph_text, classified_segments)
    wrapped_xml = wrapper.get_wrapped_xml()

    return wrapped_xml, classified_segments


# ---------- API ----------

@app.post("/parse-paragraph", response_model=ParagraphOutput)
async def parse_paragraph(input_data: ParagraphInput) -> ParagraphOutput:
    if not input_data.text or not input_data.text.strip():
        raise HTTPException(status_code=400, detail="Paragraph text cannot be empty")

    try:
        wrapped_paragraph, _ = classify_paragraph(input_data.text)
        return ParagraphOutput(classified_paragraph=wrapped_paragraph)

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
        "endpoints": {
            "parse_paragraph": "POST /parse-paragraph",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ---------- LOCAL RUN ----------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)