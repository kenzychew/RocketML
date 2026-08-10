# Railway service image for the sentiment demo.
# Build context / root = demo-railway/ (self-contained, does not reach
# outside this folder).
FROM python:3.12-slim

WORKDIR /app

COPY requirements-demo.txt ./
RUN pip install --no-cache-dir -r requirements-demo.txt

COPY main.py ./
COPY app ./app
COPY static ./static
COPY model ./model

RUN useradd --create-home appuser
USER appuser

ENV PRED_MODEL_PATH=/app/model/sentiment.joblib

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
