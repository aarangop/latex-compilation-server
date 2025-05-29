# latex_server.py - FastAPI server for LaTeX compilation
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import subprocess
import tempfile
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LaTeX Compilation Server", version="1.0.0")


class LaTeXRequest(BaseModel):
    content: str
    filename: str = "document"


class CompilationResult(BaseModel):
    success: bool
    message: str
    log: str = ""


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "pdflatex_available": check_pdflatex()}


def check_pdflatex():
    """Check if pdflatex is available"""
    try:
        result = subprocess.run(['pdflatex', '--version'],
                                capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False


@app.post("/compile", response_class=Response)
async def compile_latex(request: LaTeXRequest):
    """
    Compile LaTeX content to PDF
    Returns the PDF file directly as bytes
    """
    if not check_pdflatex():
        raise HTTPException(status_code=500, detail="pdflatex not available")

    # Create temporary directory for compilation
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file = os.path.join(temp_dir, f"{request.filename}.tex")
        pdf_file = os.path.join(temp_dir, f"{request.filename}.pdf")

        try:
            # Write LaTeX content to file
            logger.info(f"Writing LaTeX content to {tex_file}")
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(request.content)

            # Compile LaTeX (run twice for references)
            logger.info("Running pdflatex (first pass)")
            result1 = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode",
                    "-output-directory", temp_dir, tex_file],
                capture_output=True, text=True, timeout=30
            )

            if result1.returncode != 0:
                logger.error(f"First pdflatex pass failed: {result1.stderr}")
                raise HTTPException(
                    status_code=400,
                    detail=f"LaTeX compilation failed: {result1.stderr[:500]}"
                )

            # Second pass for references
            logger.info("Running pdflatex (second pass)")
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode",
                    "-output-directory", temp_dir, tex_file],
                capture_output=True, text=True, timeout=30
            )

            # Check if PDF was created
            if not os.path.exists(pdf_file):
                raise HTTPException(
                    status_code=500, detail="PDF file was not created")

            # Read and return PDF
            logger.info(f"Reading compiled PDF: {pdf_file}")
            with open(pdf_file, "rb") as f:
                pdf_content = f.read()

            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={request.filename}.pdf"}
            )

        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=408, detail="LaTeX compilation timeout")
        except Exception as e:
            logger.error(f"Compilation error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Compilation error: {str(e)}")


@app.post("/compile-status")
async def compile_latex_with_status(request: LaTeXRequest):
    """
    Compile LaTeX and return status/logs instead of PDF file
    Useful for debugging
    """
    if not check_pdflatex():
        return CompilationResult(success=False, message="pdflatex not available")

    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file = os.path.join(temp_dir, f"{request.filename}.tex")
        pdf_file = os.path.join(temp_dir, f"{request.filename}.pdf")

        try:
            # Write LaTeX content
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(request.content)

            # Compile
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode",
                    "-output-directory", temp_dir, tex_file],
                capture_output=True, text=True, timeout=30
            )

            pdf_exists = os.path.exists(pdf_file)

            return CompilationResult(
                success=result.returncode == 0 and pdf_exists,
                message=f"Compilation {'successful' if result.returncode == 0 and pdf_exists else 'failed'}",
                log=result.stdout + "\n" + result.stderr
            )

        except Exception as e:
            return CompilationResult(success=False, message=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
