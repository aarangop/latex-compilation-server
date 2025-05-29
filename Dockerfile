# Stage 1: Base system with LaTeX (rarely changes)
FROM python:3.11-slim AS latex-base

RUN apt-get update && apt-get install -y \
    curl \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    && rm -rf /var/lib/apt/lists/*

# For a full latex installation use RUN apt-get update && apt-get install -y texlive-full

# Install uv (separate layer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Stage 2: Python dependencies (changes less frequently)
FROM latex-base AS python-deps

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.in .
RUN /root/.local/bin/uv pip install --no-cache-dir -r requirements.in --system

# Stage 3: Application code (changes most frequently)  
FROM python-deps AS final

# Copy application code last
COPY main.py .

EXPOSE 8000

CMD ["python", "main.py"]