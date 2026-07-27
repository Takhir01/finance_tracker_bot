FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for matplotlib and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create volume directories
RUN mkdir -p downloads/receipts

CMD ["python", "main.py"]
