"""Integration tests for LaTeX compilation server."""
import os
import pytest
import tempfile
import subprocess
from fastapi.testclient import TestClient

from main import app, check_pdflatex

# Skip integration tests if pdflatex is not available
pytestmark = pytest.mark.skipif(
    not check_pdflatex(),
    reason="pdflatex is not available on this system"
)

client = TestClient(app)

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')


def read_test_file(filename):
    """Read content from a test LaTeX file."""
    file_path = os.path.join(TEST_DATA_DIR, filename)
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def test_integration_compile_simple():
    """Integration test for compiling a simple LaTeX document."""
    content = read_test_file('simple.tex')

    response = client.post(
        "/compile",
        json={"content": content, "filename": "simple_test"}
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert response.headers["Content-Disposition"] == "attachment; filename=simple_test.pdf"

    # Save the PDF to verify it's valid
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = os.path.join(temp_dir, "simple_test.pdf")
        with open(pdf_path, "wb") as f:
            f.write(response.content)

        # Verify PDF exists and has content
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 0


def test_integration_compile_with_references():
    """Integration test for compiling a LaTeX document with references."""
    content = read_test_file('with_references.tex')

    response = client.post(
        "/compile",
        json={"content": content, "filename": "references_test"}
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"

    # Save the PDF to verify it's valid
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = os.path.join(temp_dir, "references_test.pdf")
        with open(pdf_path, "wb") as f:
            f.write(response.content)

        # Verify PDF exists and has content
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 0


def test_integration_compile_invalid_latex():
    """Integration test for compiling an invalid LaTeX document."""
    content = read_test_file('invalid.tex')

    response = client.post(
        "/compile",
        json={"content": content, "filename": "invalid_test"}
    )

    assert response.status_code == 400
    assert "LaTeX compilation failed" in response.text


def test_integration_compile_status_simple():
    """Integration test for compile-status endpoint with simple document."""
    content = read_test_file('simple.tex')

    response = client.post(
        "/compile-status",
        json={"content": content, "filename": "simple_test"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Compilation successful"
    assert len(data["log"]) > 0


def test_integration_compile_status_invalid():
    """Integration test for compile-status endpoint with invalid document."""
    content = read_test_file('invalid.tex')

    response = client.post(
        "/compile-status",
        json={"content": content, "filename": "invalid_test"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Compilation failed"
    assert len(data["log"]) > 0
    # Error should be mentioned in the log
    assert "error" in data["log"].lower()


def test_integration_large_document():
    """Integration test with a larger document to test timeouts."""
    # Generate a larger LaTeX document
    large_content = r"""\documentclass{article}
\title{Large Test Document}
\author{LaTeX Compilation Server}
\date{\today}

\begin{document}

\maketitle

\section{Introduction}
This is a test document with repeated content to make it larger.

"""

    # Add multiple sections to make the document larger
    for i in range(1, 21):
        large_content += f"""
\\section{{Section {i}}}
This is section {i} of the test document. It contains some text that will be repeated
to make the document larger and test the compilation performance.

\\begin{{itemize}}
\\item Item 1 in section {i}
\\item Item 2 in section {i}
\\item Item 3 in section {i}
\\end{{itemize}}

"""

    large_content += r"\end{document}"

    response = client.post(
        "/compile",
        json={"content": large_content, "filename": "large_test"}
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"

    # Save the PDF to verify it's valid
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = os.path.join(temp_dir, "large_test.pdf")
        with open(pdf_path, "wb") as f:
            f.write(response.content)

        # Verify PDF exists and has content
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 0
