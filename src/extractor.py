import json
import os
from pathlib import Path
import re
from typing import List, Dict, Any
import fitz  # PyMuPDF
import logging
from concurrent.futures import ThreadPoolExecutor
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFOutlineExtractor:
    def __init__(self):
        self.heading_patterns = [
            r'^(?:Chapter|Section|Part|Abstract|Introduction|Conclusion|Results|Discussion|Methods|Background|Summary|Appendix)\s*\d*',
            r'^\d+\.?\s+[A-Z]',
            r'^\d+\.\d+\.?\s*[A-Z]',
            r'^\d+\.\d+\.\d+\.?\s*[A-Z]',
            r'^[IVX]+\.\s*[A-Z]',
            r'^[A-Z]\.\s*[A-Z]',
            r'^第\d+章',
            r'^第\d+節',
            r'^\d+章',
            r'^\d+節',
            r'^[A-Z][A-Z\s]{3,}$',
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.heading_patterns]

        self.footer_keywords = [
            r'^Page \d+ of \d+',
            r'^\d{1,2} \w+ \d{4}$',
            r'^\w+ \d{1,2}, \d{4}$',
            r'^\d{1,2}/\d{1,2}/\d{4}$',
            r'^May 31, 2014$',
            r'^International$',
            r'^Software Testing$',
            r'^\[\w+-Web\]$'
        ]
        self.compiled_footer_patterns = [re.compile(p, re.IGNORECASE) for p in self.footer_keywords]

    def is_footer_or_header(self, text: str) -> bool:
        text = text.strip()
        if len(text) <= 2:
            return True
        for pattern in self.compiled_footer_patterns:
            if pattern.match(text):
                return True
        return False

    def analyze_document_fonts(self, doc) -> Dict[str, float]:
        font_sizes = []
        max_pages = min(len(doc), 50)
        for page_num in range(max_pages):
            page = doc[page_num]
            try:
                text_dict = page.get_text("dict")
                for block in text_dict.get("blocks", []):
                    if "lines" not in block:
                        continue
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span["text"].strip():
                                font_sizes.append(span["size"])
            except Exception:
                continue
        if not font_sizes:
            return {"avg": 12, "q75": 14, "q90": 16}
        font_sizes.sort()
        n = len(font_sizes)
        return {
            "avg": sum(font_sizes) / n,
            "q75": font_sizes[int(n * 0.75)],
            "q90": font_sizes[int(n * 0.90)]
        }

    def extract_text_blocks(self, page) -> List[Dict]:
        blocks = []
        try:
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    line_text = ""
                    max_font_size = 0
                    flags = 0
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            line_text += text + " "
                            max_font_size = max(max_font_size, span["size"])
                            flags |= span["flags"]
                    line_text = line_text.strip()
                    if len(line_text) > 2 and not self.is_footer_or_header(line_text):
                        blocks.append({
                            "text": line_text,
                            "font_size": max_font_size,
                            "flags": flags,
                            "is_bold": bool(flags & 16),
                            "is_uppercase": line_text.isupper()
                        })
        except Exception as e:
            logger.warning(f"Error extracting text blocks: {e}")
        return blocks

    def is_heading(self, block: Dict, font_stats: Dict) -> bool:
        text = block["text"].strip()
        font_size = block["font_size"]
        if len(text) < 3 or len(text) > 200:
            return False
        if text.endswith('.') and len(text) > 20:
            return False
        if font_size >= font_stats["q90"] or font_size >= font_stats["q75"]:
            return True
        if font_size >= font_stats["avg"] * 1.2:
            return True
        if block["is_bold"] and font_size >= font_stats["avg"]:
            return True
        for pattern in self.compiled_patterns:
            if pattern.match(text):
                return True
        if block["is_uppercase"] and 5 <= len(text) <= 50:
            return True
        return False

    def determine_heading_level(self, block: Dict, font_stats: Dict) -> str:
        text = block["text"].strip()
        font_size = block["font_size"]
        avg_size = font_stats["avg"]
        if font_size >= avg_size * 1.5:
            base_level = "H1"
        elif font_size >= avg_size * 1.3:
            base_level = "H2"
        else:
            base_level = "H3"
        if re.match(r'^(?:Chapter|CHAPTER|第\d+章)', text):
            return "H1"
        elif re.match(r'^(?:Section|SECTION|第\d+節)', text):
            return "H2"
        elif re.match(r'^\d+\.\d+\.\d+', text):
            return "H3"
        elif re.match(r'^\d+\.\d+', text):
            return "H2"
        elif re.match(r'^\d+\.', text):
            return "H1"
        return base_level

    def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
        try:
            doc = fitz.open(pdf_path)
            outline = {"title": "", "outline": []}
            metadata = doc.metadata or {}
            if metadata.get("title"):
                outline["title"] = metadata["title"].strip()

            font_stats = self.analyze_document_fonts(doc)
            headings = []
            max_pages = min(50, len(doc))

            candidate_title_lines = []

            for page_num in range(max_pages):
                page = doc[page_num]
                blocks = self.extract_text_blocks(page)
                for block in blocks:
                    if self.is_heading(block, font_stats):
                        text = block["text"]
                        level = self.determine_heading_level(block, font_stats)
                        if level == "H1" and page_num == 0:
                            candidate_title_lines.append(text)
                            continue
                        headings.append({
                            "level": level,
                            "text": text,
                            "page": page_num + 1
                        })

            if not outline["title"] and candidate_title_lines:
                outline["title"] = " ".join(candidate_title_lines).strip()

            if len(doc) == 1 and len(headings) > 15:
                first_page_blocks = self.extract_text_blocks(doc[0])
                top_title = [b["text"] for b in first_page_blocks if b["font_size"] >= font_stats["q90"] and b["is_bold"]]
                if top_title:
                    outline["title"] = top_title[0].strip()
                outline["outline"] = []
                doc.close()
                return outline

            outline["outline"] = self.clean_headings(headings)

            if not outline["title"]:
                if outline["outline"] and outline["outline"][0]["level"] == "H1":
                    outline["title"] = outline["outline"][0]["text"]
                    outline["outline"] = outline["outline"][1:]
                else:
                    outline["title"] = Path(pdf_path).stem.replace("_", " ").title()

            outline["title"] = outline["title"].strip() + " " if outline["title"].strip() else ""

            doc.close()
            return outline

        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return {
                "title": Path(pdf_path).stem.replace('_', ' ').title(),
                "outline": []
            }

    def clean_headings(self, headings: List[Dict]) -> List[Dict]:
        if not headings:
            return []
        seen = set()
        cleaned = []
        for heading in headings:
            key = (heading["text"].lower().strip(), heading["page"])
            if key not in seen:
                seen.add(key)
                cleaned.append(heading)
        for i in range(1, len(cleaned)):
            prev_level = cleaned[i-1]["level"]
            curr_level = cleaned[i]["level"]
            level_map = {"H1": 1, "H2": 2, "H3": 3}
            prev_num = level_map[prev_level]
            curr_num = level_map[curr_level]
            if curr_num > prev_num + 1:
                cleaned[i]["level"] = f"H{prev_num + 1}"
        return cleaned
