# Contributing to Transcriber v2.0

Thank you for your interest in contributing to Transcriber v2.0! This document provides guidelines for contributing to the project.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)

## 🚀 Getting Started

### Prerequisites

- Python 3.8+ (Python 3.9+ recommended)
- Git for version control
- FFmpeg for audio processing
- 4GB+ disk space for dependencies

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/transcriber-v2.0.git
   cd transcriber-v2.0
   ```

3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/travis-symbolscape/transcriber-v2.0.git
   ```

## ⚙️ Development Setup

### 1. Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Copy environment template
cp .env.template .env
# Edit .env with your API keys (optional for development)
```

### 2. Verify Installation

```bash
# Run basic tests
python -m pytest tests/

# Test individual modules
python scripts/transcribe.py --help
python scripts/diarize_transcript.py --help
```

## 📝 Code Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) for Python code style
- Use [Black](https://black.readthedocs.io/) for code formatting
- Maximum line length: 88 characters (Black default)

### Formatting Tools

```bash
# Format code with Black
black scripts/ tests/ *.py

# Check style with flake8
flake8 scripts/ tests/ *.py --max-line-length=88
```

### Code Organization

#### Modular Architecture
- Each script should have a single, well-defined purpose
- Functions should be small and focused
- Use type hints for function parameters and return values

#### Error Handling
- Use try/catch blocks for expected failures
- Provide helpful error messages to users
- Log errors appropriately for debugging

#### Documentation Requirements
- All functions must have docstrings following the format:
  ```python
  def function_name(param1: str, param2: int = 10) -> str:
      \"\"\"
      Brief description of function.
      
      Args:
          param1: Description of parameter
          param2: Description with default value
          
      Returns:
          Description of return value
          
      Raises:
          ValueError: When parameter is invalid
      \"\"\"
  ```

### File Structure
```
scripts/
├── module_name.py          # Main module logic
├── README.md              # Module-specific documentation
tests/
├── test_module_name.py    # Unit tests for module
docs/
├── module_name.md         # Detailed documentation
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run tests with coverage
python -m pytest tests/ --cov=scripts --cov-report=html

# Run specific test file
python -m pytest tests/test_specific_module.py

# Run tests in verbose mode
python -m pytest tests/ -v
```

### Writing Tests

- Write unit tests for all new functions
- Test both success and failure cases
- Use descriptive test names
- Mock external dependencies (API calls, file operations)

Example test structure:
```python
import pytest
from scripts.module_name import function_name

def test_function_success():
    \"\"\"Test function with valid input\"\"\"
    result = function_name("valid_input")
    assert result == "expected_output"

def test_function_failure():
    \"\"\"Test function with invalid input\"\"\"
    with pytest.raises(ValueError):
        function_name("invalid_input")
```

## 📤 Submitting Changes

### Commit Guidelines

- Use clear, descriptive commit messages
- Follow the format: `type: description`
- Types: feat, fix, docs, style, refactor, test, chore

Examples:
```bash
feat: add speaker confidence scoring to diarization
fix: handle empty audio files gracefully
docs: update API documentation for transcribe module
test: add unit tests for context correction
```

### Pull Request Process

1. **Update from upstream**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes and test**:
   ```bash
   # Make your changes
   python -m pytest tests/  # Ensure tests pass
   black scripts/ tests/    # Format code
   ```

4. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: your descriptive message"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**:
   - Use descriptive title and description
   - Reference any related issues
   - Include testing instructions
   - Add screenshots/examples if applicable

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code is formatted with Black
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if applicable)
- [ ] No API keys or sensitive data in commits
- [ ] Descriptive commit messages

## 📖 Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings, inline comments
2. **User Documentation**: README.md, usage guides
3. **API Documentation**: Function signatures and examples
4. **Developer Documentation**: Architecture, contributing guides

### Documentation Standards

- Use clear, concise language
- Provide practical examples
- Keep documentation up-to-date with code changes
- Include troubleshooting sections for common issues

### Building Documentation

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve

# Build static documentation
mkdocs build
```

## 🎯 Areas for Contribution

### High Priority
- **Performance optimizations** for large audio files
- **Additional output formats** (SRT, VTT, etc.)
- **Enhanced error recovery** and graceful degradation
- **UI improvements** for better user experience

### Medium Priority
- **Additional language support** for AI features
- **Batch processing capabilities** for multiple files
- **Configuration file support** for common settings
- **Docker containerization** for easy deployment

### Lower Priority
- **Web interface** for non-technical users
- **Real-time transcription** capabilities
- **Cloud storage integration** (AWS S3, Google Drive)
- **Advanced analytics** and reporting features

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professional communication

### Getting Help
- Check existing issues and documentation first
- Ask questions in GitHub Discussions
- Provide minimal reproducible examples
- Be patient and respectful

### Recognition
Contributors will be acknowledged in:
- README.md contributors section
- CHANGELOG.md for significant contributions
- GitHub contributors page

---

Thank you for contributing to Transcriber v2.0! Your efforts help make AI-powered transcription accessible to everyone.
