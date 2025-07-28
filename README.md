# Adobe Hackathon Outline Extractor

## How It Works
- Place PDF files in `/app/input`.
- Run the container.
- Extracted outlines appear in `/app/output`.

## Features
- Detects headings (title, H1, H2, H3) using multiple cues, not just font size.
- Runs fully offline, fast and memory-efficient.
- Compatible with complex documents.

## 🐳 Run via Docker (Recommended)
### Build the Docker Image
```bash
docker build -t adobe-outline-extractor .
```
###  Run the Container
```bash
docker run --rm \
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
