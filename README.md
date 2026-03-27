# Deanta – Reference vs Commentary Parser

## Overview

This service identifies **reference content** and **commentary** within paragraphs containing HTML/XML-like markup, and returns the same paragraph with semantic tags applied.

## API


POST /parse-paragraph


### Input
```json
{
  "text": "<para>...</para>"
}
```
### Output
```json
{
  "classified_paragraph": "<para>...</para>"
}
```


### Requirements

Preserve all existing tags (<span>, <i>, etc.)
Preserve all attributes exactly
Do not modify structure or ordering
Only add:
<reference>
<commentary>

Output must be identical to input except for wrapper tags.

### Approach
Tokenizer: splits content using citation-aware rules (; as primary delimiter)
Classifier: detects reference vs commentary (e.g., "See also")
Post-processing: separates mixed segments (e.g., "See also: Author")
Wrapper: inserts tags using position-based mapping without breaking XML


### How to run

docker-compose build
docker-compose up