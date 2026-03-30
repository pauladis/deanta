# Deanta – Reference vs Commentary Parser

## Overview

This service identifies **reference content** and **commentary** within paragraphs containing HTML/XML-like markup, and returns the same paragraph with semantic tags applied.

## Prerequisites

- Python 3.10+ (for local development)
- Docker & Docker Compose (for containerized deployment)
- pip (Python package manager)
- Git (optional, for version control)

## API Endpoints

- `POST /parse-paragraph` - Classify and tag paragraph content
- `GET /health` - Health check
- `GET /` - API info


### Usage examples
```json
{
"text": "<para er-custom-ele=\"true\" ele-id=\"254E136C\" store=\"635\" er_para_index_id=\"fe-1772171652046118-124\" contenteditable=\"true\" tabindex=\"-1\" translate=\"no\" data-alignment=\"left-justified\" data-indent-type=\"first-line\" data-left-indent=\"25pt\" data-right-indent=\"0pt\" data-special-indent=\"-19.5pt\" data-space-above=\"0pt\" data-space-below=\"0pt\" style=\"margin: calc(10px) 0px 0pt 25px; padding-left: 25px; text-indent: -19.5px;\" class=\"\" spellcheck=\"false\" data-gramm=\"false\">This topic has been widely discussed in recent scholarship. See John Brewer, <i ele-id=\"ds-C814AB4C\" store=\"636\" contenteditable=\"true\" tabindex=\"-1\" translate=\"no\" class=\"\" spellcheck=\"false\" data-gramm=\"false\">The Sinews of Power</i> (London: Routledge, <span class=\"refIcon\" tabindex=\"-1\" translate=\"no\" spellcheck=\"false\" data-gramm=\"false\" store=\"1774615713949816\"></span><link1 linkend=\"EUP_00_WREF_BIB_CIT000501\" role=\"bibr\" ele-id=\"ds-C8F97226\" store=\"638\" contenteditable=\"true\" tabindex=\"-1\" translate=\"no\" class=\"\" spellcheck=\"false\" data-gramm=\"false\">1989</link1>), p. 45, for further details.</para>"
}
```
### Output
```json
{
"classified_paragraph": "<para er-custom-ele=\"true\" ele-id=\"254E136C\" store=\"635\" er_para_index_id=\"fe-1772171652046118-124\" contenteditable=\"true\" tabindex=\"-1\" translate=\"no\" data-alignment=\"left-justified\" data-indent-type=\"first-line\" data-left-indent=\"25pt\" data-right-indent=\"0pt\" data-special-indent=\"-19.5pt\" data-space-above=\"0pt\" data-space-below=\"0pt\" style=\"margin: calc(10px) 0px 0pt 25px; padding-left: 25px; text-indent: -19.5px;\" class=\"\" spellcheck=\"false\" data-gramm=\"false\"><commentary>This topic has been widely discussed in recent scholarship.</commentary> <reference>See John Brewer, <i ele-id=\"ds-C814AB4C\" store=\"636\" contenteditable=\"true\" tabindex=\"-1\" translate=\"no\" class=\"\" spellcheck=\"false\" data-gramm=\"false\">The Sinews of Power</i> (London: Routledge, <span class=\"refIcon\" tabindex=\"-1\" translate=\"no\" spellcheck=\"false\" data-gramm=\"false\" store=\"1774615713949816\"></span><link1 linkend=\"EUP_00_WREF_BIB_CIT000501\" role=\"bibr\" ele-id=\"ds-C8F97226\" store=\"638\" contenteditable=\"true\" tabindex=\"-1\" translate=\"no\" class=\"\" spellcheck=\"false\" data-gramm=\"false\">1989</link1>), p. 45, </reference><commentary>for further details.</commentary></para>"
}
```


### Requirements

- Preserve all existing tags (<span>, <i>, etc.)
- Preserve all attributes exactly
- Do not modify structure or ordering
- Only add:
  - &lt;reference&gt;
  - &lt;commentary&gt;

Output must be identical to input except for wrapper tags.

### Approach
- Tokenizer: splits content using citation-aware rules (; as primary delimiter)
- Classifier: detects reference vs commentary (e.g., "See also")
- Post-processing: separates mixed segments (e.g., "See also: Author")
- Wrapper: inserts tags using position-based mapping without breaking XML


## Installation & Setup

### Option 1: Run with Docker (Recommended)

```bash
# Build and start the container
docker-compose build
docker-compose up
```

The API will be available at `http://localhost:8000`

### Option 2: Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -m nltk.downloader punkt

# Run the server
python app/main.py
```

The API will be available at `http://localhost:8000`

## Testing

```bash
# Run all tests (requires running server for endpoint tests)
pytest -v

# Run only unit tests (no server required)
pytest tests/test_parser.py -v

# Run only integration tests (requires running server)
pytest tests/test_endpoint.py -v
```
