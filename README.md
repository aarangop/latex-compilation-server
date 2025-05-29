# LaTeX Compilation Server

A Docker-based HTTP server for compiling LaTeX documents to PDF without
requiring local LaTeX installation.

This project was motivated by my need to compile LaTeX documents without relying
on a local LaTeX installation for my
[CV Tailoring MCP server](https://github.com/aarangop/resume-mcp).

This microservice now offers the narrow functionality of compiling LaTeX docs to
PDF.

## Quick Start

1. **Clone/Download the files:**

   ```bash
   git clone https://github.com/aarangop/latex-compilation-server && cd latex-compilation-server
   ```

2. **Build and start the server:**

   ```bash
   # Option 1: Using docker-compose (recommended)
   docker-compose up -d

   # Option 2: Using Docker directly
   docker build -t latex-server .
   docker run -d -p 7474:8000 --name latex-server latex-server
   ```

Since this container has LaTeX dependencies, the first build may take a while as
it downloads and installs the necessary packages. But since we're using a staged
build, subsequent builds should be much faster.

3. **Verify it's running:**
   ```bash
   curl http://localhost:7474/health
   ```

## Usage

### From Python (MCP Tool)

The MCP tool automatically communicates with the server via HTTP requests.

### Manual Testing

```bash
# Test compilation
curl -X POST http://localhost:7474/compile \
  -H "Content-Type: application/json" \
  -d '{"content": "\\documentclass{article}\\begin{document}Hello World!\\end{document}", "filename": "test"}' \
  --output test.pdf
```

### API Endpoints

- `GET /health` - Check server health
- `POST /compile` - Compile LaTeX to PDF (returns PDF bytes)
- `POST /compile-status` - Compile and return status/logs (for debugging)

## Management Commands

```bash
# Start server
docker-compose up -d

# Stop server
docker-compose down

# View logs
docker-compose logs -f latex-server

# Restart server
docker-compose restart latex-server

# Update server
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### Server not starting

```bash
# Check logs
docker-compose logs latex-server

# Check if port is in use
lsof -i :7474
```

### LaTeX compilation errors

```bash
# Use the debug endpoint
curl -X POST http://localhost:7474/compile-status \
  -H "Content-Type: application/json" \
  -d '{"content": "your-latex-content", "filename": "debug"}'
```

### Reset everything

```bash
docker-compose down
docker system prune -f
docker-compose up -d --build
```

## Security Notes

- Server runs on localhost only by default
- LaTeX compilation happens in isolated container
- Temporary files are cleaned up automatically
- No persistent storage of user documents

## Customization

### Add more LaTeX packages

Edit the Dockerfile to install additional packages:

```dockerfile
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-science \
    texlive-math-extra \
    && rm -rf /var/lib/apt/lists/*
```

### Change port

Edit docker-compose.yml:

```yaml
ports:
  - "9000:8000" # Use port 9000 instead
```

### Enable remote access (not recommended)

Edit main.py:

```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # Already set for container
```

Then expose the port in docker-compose.yml appropriately.
