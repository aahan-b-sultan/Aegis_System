# 1. Base Image: Official Python 3.10 (Stable & Compatible)
FROM python:3.10-slim

# 2. Set Environment Variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# 3. Set Work Directory inside the container
WORKDIR /app

# 4. Install System Dependencies
# 'libgl1' is often needed for graphical libraries like Matplotlib/OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python Dependencies
# We copy requirements first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the Application Code
COPY . .

# 7. Expose the Port (FastAPI default)
EXPOSE 8000

# 8. Command to run the application
# We use '0.0.0.0' to allow external access (e.g., from browser)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]