# Base image with CUDA 12.8 and PyTorch compatible drivers
FROM runpod/pytorch:1.0.2-cu1281-torch271-ubuntu2204

# Prepare model directories
ENV MODELS_DIR=/models 
ENV HF_HOME=${MODELS_DIR} \
    HF_HUB_CACHE=${MODELS_DIR} \
    TRANSFORMERS_OFFLINE=1 \
    HF_HUB_ENABLE_HF_TRANSFER=1 \
    HF_HUB_OFFLINE=1

# Install Python dependencies first (leverage layer cache)
WORKDIR /app

# Copy application code
COPY requirements.txt ./
COPY handler.py ./
COPY download_models.py ./
COPY models/ ${MODELS_DIR}/

# Install dependencies and download Flux Kontext model
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel \
 && python -m pip install --no-cache-dir --no-compile -r requirements.txt \
 && python download_models.py ${MODELS_DIR} \
 && rm -rf /root/.cache/pip \
 && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
 && (find /usr/local/lib/python3.12 -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true) \
 && (find /usr/local/lib/python3.12 -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true) \
 && (find /usr/local/lib/python3.10 -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true) \
 && (find /usr/local/lib/python3.10 -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true) \
 && rm -rf /root/.cache /tmp/* /var/tmp/*

# Expose server port
ENV RP_HANDLER=handler \
    RP_NUM_WORKERS=1 \
    RP_PORT=3000 \
    RP_HTTP=1

EXPOSE 3000

# Health check and start
CMD ["python", "handler.py"]
