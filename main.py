from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
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


class ParagraphInput(BaseModel):
    """Input model for paragraph parsing"""
    text: str


class ParagraphOutput(BaseModel):
    """Output model for classified paragraph"""
    classified_paragraph: str


def extract_text_only(xml_text: str) -> str:
    """Extract plain text from XML"""
    return re.sub(r'<[^>]+>', '', xml_text)


def split_commentary_phrases(segments):
    result = []
    
    commentary_phrase_pattern = re.compile(
        r'^(See\s+also:?|For\s+an?\s+in-depth\s+discussion.*?)(\s+.+)$',
        re.IGNORECASE
    )
    
    for text, start, end, classification in segments:
        
        if classification == 'commentary':
            match = commentary_phrase_pattern.match(text)
            
            if match:
                phrase = match.group(1).strip()
                remaining = match.group(2).strip()
                
                split_offset = text.find(remaining)
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


def classify_paragraph(paragraph_text: str) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Classify a paragraph into reference and commentary sections
    Returns: (wrapped_xml, segment_classifications)
    """
    # Extract plain text
    text_only = extract_text_only(paragraph_text)
    
    # Tokenize into segments based on citations and boundaries
    tokenizer = CitationAwareTokenizer(text_only)
    segments = tokenizer.get_segments()
    
    # Classify each segment
    segment_classifications = []
    for segment in segments:
        classification = classifier.classify(segment.text)
        segment_classifications.append((
            segment.text,
            segment.start_pos,
            segment.end_pos,
            classification
        ))
    
    # Post-process: split commentary phrases from following references
    segment_classifications = split_commentary_phrases(segment_classifications)
    
    # Wrap with tags
    wrapper = SmartTagWrapper(paragraph_text, segment_classifications)
    wrapped_xml = wrapper.get_wrapped_xml()
    
    return wrapped_xml, segment_classifications


@app.post("/parse-paragraph", response_model=ParagraphOutput)
async def parse_paragraph(input_data: ParagraphInput) -> ParagraphOutput:
    """
    Parse a paragraph and classify content as reference or commentary.
    
    Args:
        input_data: JSON object with 'text' field containing the paragraph
    
    Returns:
        JSON object with 'classified_paragraph' field containing the paragraph
        with <reference> and <commentary> tags inserted
    """
    if not input_data.text or not input_data.text.strip():
        raise HTTPException(status_code=400, detail="Paragraph text cannot be empty")
    
    try:
        wrapped_paragraph, classifications = classify_paragraph(input_data.text)
        return ParagraphOutput(classified_paragraph=wrapped_paragraph)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing paragraph: {str(e)}")


@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "ok",
        "message": "Deanta API is running",
        "endpoints": {
            "parse_paragraph": "POST /parse-paragraph",
            "health": "GET /"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
