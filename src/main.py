import os
import json
from extractor import PDFOutlineExtractor

# Use absolute paths based on the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, "app", "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "output")

# Ensure output folder exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize extractor
extractor = PDFOutlineExtractor()

# Loop through all PDFs in input folder
for filename in os.listdir(INPUT_DIR):
    if filename.lower().endswith(".pdf"):
        pdf_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".json"))

        # Extract the structure
        result = extractor.extract_outline(pdf_path)

        # Save JSON output
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        print(f"Processed: {filename}")
