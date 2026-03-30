from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
from typing import List, Tuple

from tokenizer import CitationAwareTokenizer
from classifier import EnhancedClassifier
from wrapper import SmartTagWrapper


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


# ---------- POST-PROCESSING ----------

def split_commentary_phrases(
    segments: List[Tuple[str, int, int, str]]
) -> List[Tuple[str, int, int, str]]:

    result = []

    see_pattern = re.compile(r'^(.*?)(\bsee\b\s+.+)$', re.IGNORECASE)
    tail_pattern = re.compile(r'^(.*?,)(\s+for\s+.+)$', re.IGNORECASE)

    for text, start, end, classification in segments:

        # ---------- CASE 1: commentary → see → reference ----------
        if classification == 'commentary':
            match = see_pattern.match(text)

            if match:
                before = match.group(1).strip()
                after = match.group(2).strip()

                split_offset = text.lower().find(after.lower())
                if split_offset != -1:
                    split_pos = start + split_offset

                    if before:
                        result.append((before, start, split_pos, 'commentary'))

                    result.append((after, split_pos, end, 'reference'))
                    continue

        # ---------- CASE 2: reference → trailing commentary ----------
        if classification == 'reference':
            match = tail_pattern.match(text)

            if match:
                before = match.group(1).strip()
                after = match.group(2).strip()

                split_offset = text.lower().find(after.lower())
                if split_offset != -1:
                    split_pos = start + split_offset

                    result.append((before, start, split_pos, 'reference'))
                    result.append((after, split_pos, end, 'commentary'))
                    continue

        result.append((text, start, end, classification))

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

    # 🔥 critical step (now generic + correct)
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