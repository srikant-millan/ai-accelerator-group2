# ---------- Base image ----------
FROM python:3.11-slim

# ---------- System setup ----------
RUN apt-get update && apt-get install -y curl && \
    apt-get clean

# ---------- Install Ollama ----------
RUN curl -fsSL https://ollama.com/install.sh | bash

# ---------- Add your app ----------
WORKDIR /app
COPY . .

# ---------- Install dependencies ----------
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Start Ollama and download small model ----------
# Use smaller 1B model (~600 MB)
RUN /bin/bash -c "ollama serve & sleep 15 && ollama pull llama3.2:1b"

# ---------- Expose FastAPI port ----------
EXPOSE 8000

# ---------- Run FastAPI ----------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
