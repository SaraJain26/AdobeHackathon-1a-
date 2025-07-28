FROM python:3.10-slim

WORKDIR /app

COPY src /src
COPY app /app

RUN pip install --no-cache-dir PyMuPDF

CMD ["python", "/src/main.py"]
