FROM python:3.11-slim

WORKDIR /app

# ffmpeg: video transcoding for playback/events clip endpoints
# libgl1/libglib2.0-0/libsm6/libxext6: OpenCV (cv2) runtime shared libs
# (no compiler toolchain needed -- every Python dependency here ships a
# prebuilt manylinux wheel, confirmed via `pip download --only-binary=:all:`)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libgl1 libglib2.0-0 libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

COPY . .

# Plain (non-editable) install for the built image -- editable installs
# need the source tree present at install time for package discovery,
# which a separate "COPY pyproject.toml only" caching layer would break.
RUN pip install --no-cache-dir "."

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
