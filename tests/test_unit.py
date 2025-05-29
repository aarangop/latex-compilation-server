"""Unit tests for LaTeX compilation server endpoints."""
import os
import pytest
from fastapi.testclient import TestClient
import subprocess
from unittest.mock import patch, Mock

from main import app, check_pdflatex

# Create a test client for the FastAPI application
client = TestClient(app)


def test_health_check_with_pdflatex_available():
    """Test health check endpoint when pdflatex is available."""
    with patch('main.check_pdflatex', return_value=True):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy",
                                   "pdflatex_available": True}


def test_health_check_with_pdflatex_not_available():
    """Test health check endpoint when pdflatex is not available."""
    with patch('main.check_pdflatex', return_value=False):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy",
                                   "pdflatex_available": False}


def test_check_pdflatex_available():
    """Test check_pdflatex function when pdflatex is available."""
    mock_result = Mock()
    mock_result.returncode = 0
    with patch('subprocess.run', return_value=mock_result):
        assert check_pdflatex() is True


def test_check_pdflatex_not_available_returncode():
    """Test check_pdflatex function when pdflatex returns non-zero."""
    mock_result = Mock()
    mock_result.returncode = 1
    with patch('subprocess.run', return_value=mock_result):
        assert check_pdflatex() is False


def test_check_pdflatex_not_available_exception():
    """Test check_pdflatex function when subprocess.run raises exception."""
    with patch('subprocess.run', side_effect=Exception("Command not found")):
        assert check_pdflatex() is False


def test_compile_latex_no_pdflatex():
    """Test compile endpoint when pdflatex is not available."""
    with patch('main.check_pdflatex', return_value=False):
        response = client.post(
            "/compile",
            json={
                "content": "\\documentclass{article}\\begin{document}Test\\end{document}", "filename": "test"}
        )
        assert response.status_code == 500
        assert "pdflatex not available" in response.text


def test_compile_status_no_pdflatex():
    """Test compile-status endpoint when pdflatex is not available."""
    with patch('main.check_pdflatex', return_value=False):
        response = client.post(
            "/compile-status",
            json={
                "content": "\\documentclass{article}\\begin{document}Test\\end{document}", "filename": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "pdflatex not available"


def test_compile_latex_success():
    """Test successful LaTeX compilation."""
    # Mock the temporary directory and file paths
    mock_temp_dir = "/tmp/mock"
    mock_tex_file = os.path.join(mock_temp_dir, "test.tex")
    mock_pdf_file = os.path.join(mock_temp_dir, "test.pdf")

    # Mock subprocess and file operations
    with patch('tempfile.TemporaryDirectory') as mock_temp:
        mock_temp.return_value.__enter__.return_value = mock_temp_dir
        with patch('main.check_pdflatex', return_value=True), \
                patch('builtins.open'), \
                patch('os.path.exists', return_value=True), \
                patch('subprocess.run') as mock_run:

            # Mock successful compilation
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stderr = ""
            mock_run.return_value = mock_process

            # Mock file reading
            mock_open = Mock()
            mock_open.return_value.__enter__.return_value.read.return_value = b"PDF content"
            with patch('builtins.open', mock_open):
                response = client.post(
                    "/compile",
                    json={
                        "content": "\\documentclass{article}\\begin{document}Test\\end{document}",
                        "filename": "test"
                    }
                )

                assert response.status_code == 200
                assert response.headers["Content-Disposition"] == "attachment; filename=test.pdf"
                assert response.headers["Content-Type"] == "application/pdf"


def test_compile_latex_failure():
    """Test failed LaTeX compilation."""
    # Mock the temporary directory and file paths
    mock_temp_dir = "/tmp/mock"
    mock_tex_file = os.path.join(mock_temp_dir, "test.tex")

    # Mock subprocess and file operations
    with patch('tempfile.TemporaryDirectory') as mock_temp:
        mock_temp.return_value.__enter__.return_value = mock_temp_dir
        with patch('main.check_pdflatex', return_value=True), \
                patch('builtins.open'), \
                patch('subprocess.run') as mock_run:

            # Mock failed compilation
            mock_process = Mock()
            mock_process.returncode = 1
            mock_process.stderr = "LaTeX Error: Missing \\begin{document}"
            mock_run.return_value = mock_process

            response = client.post(
                "/compile",
                json={
                    "content": "\\documentclass{article}\\begin{document",
                    "filename": "test"
                }
            )

            assert response.status_code == 400
            assert "LaTeX compilation failed" in response.text


def test_compile_latex_timeout():
    """Test LaTeX compilation timeout."""
    # Mock the temporary directory
    mock_temp_dir = "/tmp/mock"

    # Mock subprocess and file operations
    with patch('tempfile.TemporaryDirectory') as mock_temp:
        mock_temp.return_value.__enter__.return_value = mock_temp_dir
        with patch('main.check_pdflatex', return_value=True), \
                patch('builtins.open'), \
                patch('subprocess.run', side_effect=subprocess.TimeoutExpired("pdflatex", 30)):

            response = client.post(
                "/compile",
                json={
                    "content": "\\documentclass{article}\\begin{document}Test\\end{document}",
                    "filename": "test"
                }
            )

            assert response.status_code == 408
            assert "LaTeX compilation timeout" in response.text


def test_compile_latex_pdf_not_created():
    """Test when PDF file is not created despite successful compilation."""
    # Mock the temporary directory
    mock_temp_dir = "/tmp/mock"

    # Mock subprocess and file operations
    with patch('tempfile.TemporaryDirectory') as mock_temp:
        mock_temp.return_value.__enter__.return_value = mock_temp_dir
        with patch('main.check_pdflatex', return_value=True), \
                patch('builtins.open'), \
                patch('os.path.exists', return_value=False), \
                patch('subprocess.run') as mock_run:

            # Mock successful compilation but PDF not created
            mock_process = Mock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            response = client.post(
                "/compile",
                json={
                    "content": "\\documentclass{article}\\begin{document}Test\\end{document}",
                    "filename": "test"
                }
            )

            assert response.status_code == 500
            assert "PDF file was not created" in response.text


def test_compile_status_success():
    """Test compile-status endpoint with successful compilation."""
    # Mock the temporary directory
    mock_temp_dir = "/tmp/mock"
    mock_pdf_file = os.path.join(mock_temp_dir, "test.pdf")

    # Mock subprocess and file operations
    with patch('tempfile.TemporaryDirectory') as mock_temp:
        mock_temp.return_value.__enter__.return_value = mock_temp_dir
        with patch('main.check_pdflatex', return_value=True), \
                patch('builtins.open'), \
                patch('os.path.exists', return_value=True), \
                patch('subprocess.run') as mock_run:

            # Mock successful compilation
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = "LaTeX output"
            mock_process.stderr = ""
            mock_run.return_value = mock_process

            response = client.post(
                "/compile-status",
                json={
                    "content": "\\documentclass{article}\\begin{document}Test\\end{document}",
                    "filename": "test"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Compilation successful"
            assert "LaTeX output" in data["log"]


def test_compile_status_failure():
    """Test compile-status endpoint with failed compilation."""
    # Mock the temporary directory
    mock_temp_dir = "/tmp/mock"

    # Mock subprocess and file operations
    with patch('tempfile.TemporaryDirectory') as mock_temp:
        mock_temp.return_value.__enter__.return_value = mock_temp_dir
        with patch('main.check_pdflatex', return_value=True), \
                patch('builtins.open'), \
                patch('os.path.exists', return_value=False), \
                patch('subprocess.run') as mock_run:

            # Mock failed compilation
            mock_process = Mock()
            mock_process.returncode = 1
            mock_process.stdout = ""
            mock_process.stderr = "LaTeX Error"
            mock_run.return_value = mock_process

            response = client.post(
                "/compile-status",
                json={
                    "content": "\\documentclass{article}\\begin{document",
                    "filename": "test"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["message"] == "Compilation failed"
            assert "LaTeX Error" in data["log"]


def test_compile_status_exception():
    """Test compile-status endpoint when an exception occurs."""
    # Mock the temporary directory
    with patch('tempfile.TemporaryDirectory') as mock_temp:
        mock_temp.return_value.__enter__.return_value = "/tmp/mock"
        with patch('main.check_pdflatex', return_value=True), \
                patch('builtins.open', side_effect=Exception("Mock error")):

            response = client.post(
                "/compile-status",
                json={
                    "content": "\\documentclass{article}\\begin{document}Test\\end{document}",
                    "filename": "test"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Error: Mock error" in data["message"]
