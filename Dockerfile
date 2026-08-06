FROM python:3.11-slim

# Install system dependencies for Bluetooth & Crypto
RUN apt-get update && apt-get install -y --no-install-recommends \
    bluez \
    dbus \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV PORT=5000

CMD ["python", "app.py"]
