# Stage 1: Base system with LaTeX (rarely changes)
FROM python:3.11-slim AS latex-base

RUN apt-get update && apt-get install -y \
    curl \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Stage 2: Python dependencies (changes less frequently)
FROM latex-base AS python-deps

WORKDIR /app

# Install uv (separate layer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy and install Python dependencies
COPY requirements.in .
RUN /root/.cargo/bin/uv pip install --no-cache-dir -r requirements.in

# Stage 3: Application code (changes most frequently)  
FROM python-deps AS final

# Copy application code last
COPY main.py .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "main.py"]