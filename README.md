# Deanta – Reference vs Commentary Parser

## Overview

This service identifies **reference content** and **commentary** within paragraphs containing HTML/XML-like markup, and returns the same paragraph with semantic tags applied.

## Prerequisites

- Python 3.10+ (for local development)
- Docker & Docker Compose (for containerized deployment)
- pip (Python package manager)
- Git (optional, for version control)

## API Endpoints

- `POST /parse-paragraph` - Classify and tag paragraph content (returns XML)
- `GET /health` - Health check
- `GET /` - API info

## Usage Examples

### Request

Send the paragraph text as JSON:

```json
{
  "text": "<para ...>This topic has been widely discussed in recent scholarship. See John Brewer, <i>The Sinews of Power</i> (London: Routledge, 1989), p. 45, for further details.</para>"
}
```

### Response

The API returns **raw XML** (not JSON) with `Content-Type: application/xml; charset=utf-8`:

```xml
<para ...><commentary>This topic has been widely discussed in recent scholarship.</commentary> <reference>See John Brewer, <i>The Sinews of Power</i> (London: Routledge, 1989), p. 45, </reference><commentary>for further details.</commentary></para>
```

The response is valid XML that can be directly parsed and validated by XML tools.

### Requirements

- Preserve all existing tags (<span>, <i>, etc.)
- Preserve all attributes exactly
- Do not modify structure or ordering
- Only add:
  - `<reference>`
  - `<commentary>`

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

## Architecture

The service implements a **Pipeline** design pattern:

1. **Tokenization** - Splits XML/HTML paragraphs into semantic segments
2. **Classification** - Identifies each segment as reference or commentary
3. **Post-processing** - Refines classifications for mixed segments
4. **Wrapping** - Inserts XML tags while preserving structure


## Design decisions

- I initially explored DOM-based approaches with lxml, but due to the requirement of preserving exact byte-level structure and aligning with tokenizer offsets, I moved to a string-based insertion strategy. This avoids structural mutation issues and guarantees deterministic, non-destructive transformations.