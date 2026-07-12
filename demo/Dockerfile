# Cloud Run contingency -- the Hugging Face Space (gradio SDK) ignores this file.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py sentiment.joblib ./
COPY app ./app

RUN useradd --create-home appuser
USER appuser

ENV GRADIO_SERVER_NAME=0.0.0.0

EXPOSE 7860

HEALTHCHECK CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '7860') + '/')" || exit 1

CMD ["sh", "-c", "GRADIO_SERVER_PORT=${PORT:-7860} python main.py"]
