#!/usr/bin/env python3
"""Test script to process sample paragraphs and generate output.json"""

import json
from main import classify_paragraph


def test_samples():
    """Process all sample paragraphs"""
    
    # Load samples
    with open('paragraphs-samples.json', 'r') as f:
        samples = json.load(f)
    
    results = []
    
    for paragraph in samples['paragraphs']:
        para_id = paragraph['id']
        original_text = paragraph['text']
        
        print(f"\nProcessing paragraph {para_id}...")
        
        try:
            # Classify the paragraph
            classified_text, segment_classifications = classify_paragraph(original_text)
            
            # Build result
            result = {
                "id": para_id,
                "original_text": original_text,
                "classified_text": classified_text,
                "classifications": [
                    {
                        "text": text,
                        "start": start,
                        "end": end,
                        "type": classification
                    }
                    for text, start, end, classification in segment_classifications
                ]
            }
            
            results.append(result)
            
            print(f"✓ Paragraph {para_id} processed successfully")
            print(f"  Segments classified: {len(segment_classifications)}")
            
        except Exception as e:
            print(f"✗ Error processing paragraph {para_id}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Write output
    output = {"paragraphs": results}
    
    with open('output.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Successfully processed {len(results)} paragraphs")
    print(f"Output written to output.json")
    print(f"{'='*60}")


if __name__ == "__main__":
    test_samples()