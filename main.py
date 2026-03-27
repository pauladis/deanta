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
    """
    Splits phrases like:
    "See also: Author..." → commentary + reference
    """

    result = []

    pattern = re.compile(
        r'^(See\s+also:?|For\s+an?\s+in-depth\s+discussion.*?)(\s+.+)$',
        re.IGNORECASE
    )

    for text, start, end, classification in segments:

        if classification == 'commentary':
            match = pattern.match(text)

            if match:
                phrase = match.group(1).strip()
                remaining = match.group(2).strip()

                split_offset = text.find(remaining)

                if split_offset == -1:
                    result.append((text, start, end, classification))
                    continue

                split_pos = start + split_offset

                # commentary part
                result.append((phrase, start, split_pos, 'commentary'))

                # remaining part
                remaining_class = classifier.classify(remaining)
                result.append((remaining, split_pos, end, remaining_class))

            else:
                result.append((text, start, end, classification))

        else:
            result.append((text, start, end, classification))

    return result


# ---------- CORE PIPELINE ----------

def classify_paragraph(
    paragraph_text: str
) -> Tuple[str, List[Tuple[str, int, int, str]]]:
    """
    Full pipeline:
    XML → Tokenize → Classify → Post-process → Wrap
    """

    # Tokenize directly from XML (handles ins/del internally)
    tokenizer = CitationAwareTokenizer(paragraph_text)
    segments = tokenizer.get_segments()

    # Classify segments
    classified_segments = []
    for segment in segments:
        classification = classifier.classify(segment.text)

        classified_segments.append((
            segment.text,
            segment.start_pos,
            segment.end_pos,
            classification
        ))

    # Split commentary phrases
    classified_segments = split_commentary_phrases(classified_segments)

    # Wrap results back into original XML
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