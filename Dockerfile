# Dockerfile untuk Hugging Face Spaces (Docker SDK) -- hanya backend API.
# HF Spaces: container jalan sebagai user UID 1000 dan mengekspos port 7860.
FROM python:3.12-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY --chown=user backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# main.py membaca model dari <root>/model, jadi struktur folder dipertahankan
COPY --chown=user backend/ backend/
COPY --chown=user model/ model/

EXPOSE 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
