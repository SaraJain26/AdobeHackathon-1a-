# Adobe Hackathon Outline Extractor

## How It Works
- Place PDF files in `/app/input`.
- Run the container.
- Extracted outlines appear in `/app/output`.

## Features
- Detects headings (title, H1, H2, H3) using multiple cues, not just font size.
- Runs fully offline, fast and memory-efficient.
- Compatible with complex documents.

## Approach
This tool **does not rely on machine learning**. Instead, it combines a rule-based system using:
- Text span extraction from PDF using PyMuPDF (fitz)
- Analysis of font size distribution:
  - `avg`, `q75` , `q90` thresholds across first 50 pages.
- Regex-based patterns to match structural headings:
  - Examples: 1. Introduction, 3.1 Scope, Appendix, 第1章, etc.
- Filters out repetitive boilerplate:
  - Footers, headers like Page X of Y, dates, and publisher info
- Post-processing:
  - De-duplication, hierarchy correction (e.g., avoid skipping from H1 → H3)

## Models or Libraries Used
| Tool / Library                                | Purpose                                                  |
| --------------------------------------------- | -------------------------------------------------------- |
| `PyMuPDF (fitz)`                              | PDF parsing, text span extraction                        |
| `re` (Regex)                                  | Structural pattern matching                              |
| `logging`, `os`, `json`, `concurrent.futures` | Core logic, I/O, concurrency                             |
| ❌ **No ML models used**                       | Ensures fast, deterministic output without training data |


## 🐳 Run via Docker (Recommended)
### Build the Docker Image
```bash
docker build -t adobe-outline-extractor .
```
###  Run the Container
```bash
docker run --rm --network none \
  -v "$PWD/app/input":/project/app/input \
  -v "$PWD/app/output":/project/app/output \
  adobe-outline-extractor
```
> Output is saved in app/output. You can add multiple PDFs in app/input.

## Run Manually (Local Python)
### 1. Install Python Dependencies
> Make sure you have Python 3.10+ installed.
```bash
pip install PyMuPDF
```
### 2. Run the Script
From the root directory:
```bash
python src/main.py
```

## Project Structure
```
project-root/
│
├── Dockerfile
├── app/
│   ├── input/         # Put PDFs here
│   └── output/        # JSON results appear here
│
└── src/
    ├── main.py        # Main runner
    └── extractor.py   # Core logic
```

## Requirements
- Python 3.10
- Docker (AMD64 platform)
