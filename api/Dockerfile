FROM python:3.11-slim

WORKDIR /app

# build-essential/libpq-dev: compiling C extensions + Postgres client headers
# ffmpeg: video transcoding for playback/events clip endpoints
# libgl1/libglib2.0-0/libsm6/libxext6: OpenCV (cv2) runtime shared libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev ffmpeg \
    libgl1 libglib2.0-0 libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
