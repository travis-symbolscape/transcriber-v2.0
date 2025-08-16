# Changelog

All notable changes to the Transcriber v2.0 project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1-dev] - 2025-08-15

### Added
- Comprehensive dependency documentation in README
- Detailed system requirements (Python 3.8+, disk space, RAM)
- Troubleshooting section for common installation issues
- Hugging Face token setup documentation for speaker diarization
- Platform-specific installation instructions (macOS, Ubuntu, Windows)

### Documentation
- Enhanced README with detailed API key setup instructions
- Added PyTorch installation alternatives (CPU/GPU)
- Documented all core dependencies with descriptions and sizes
- Added memory optimization guidance for different hardware
- Improved install.sh script messaging for API tokens

### Security
- Verified no API tokens committed to repository
- Enhanced .gitignore to prevent credential leaks
- Documented proper API key management practices

## [2.0.0] - 2025-07-03

### Added
- Initial release of Transcriber v2.0
- Modular transcription pipeline with Whisper integration
- AI-powered context correction and cleanup with iterative refinement
- Speaker diarization support using pyannote.audio
- Multi-language translation capabilities
- Multiple output formats (FCPXML, ITT, Markdown, JSON)
- Comprehensive existing transcript reuse and processing
- Interactive prompts for AI optimization
- Smart directory management with metadata extraction
- Full test suite and documentation

### Features
- **Transcription**: OpenAI Whisper with multiple model sizes
- **Diarization**: Advanced AI-based and simple timing-based speaker identification
- **Context Correction**: GPT-4 powered grammar and homophone fixes
- **Translation**: Multi-language support with timing preservation
- **Output Formats**: Professional-grade subtitle generation
- **Modular Architecture**: Each script does one thing well
- **User-Friendly Interface**: Clear explanations and smart defaults

### Technical
- Python 3.8+ support
- FFmpeg integration for audio preprocessing
- Environment variable management with .env support
- Comprehensive error handling and graceful fallbacks
- Professional logging and progress tracking

## [1.0.x] - Previous Version
- Legacy transcription pipeline (deprecated)
- Monolithic architecture
- Limited output format support

---

## Migration Guide

### From v1.0 to v2.0
- **Breaking Changes**: Complete architecture rewrite
- **New Requirements**: Additional Python packages (see requirements.txt)
- **Configuration**: New .env file structure for API keys
- **Usage**: New modular command structure

### API Changes
- Individual modules can now be used independently
- Unified pipeline interface: `run_transcription_pipeline_v2.py`
- New command-line arguments for enhanced functionality

### Dependencies
- Added: pyannote.audio, whisperx, huggingface_hub
- Updated: openai-whisper, torch, torchaudio
- New: python-dotenv for environment management
