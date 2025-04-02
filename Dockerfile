# Use an official Python image (Debian-based)
FROM python:3.12

# Install system dependencies for eSpeak
RUN apt-get update && apt-get install -y espeak-ng libespeak-ng1

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the script
CMD ["python3", "app.py"]
