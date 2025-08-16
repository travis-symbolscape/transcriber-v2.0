# Configuration Guide

This guide covers all configuration options, environment variables, command-line parameters, and advanced settings for Transcriber v2.0.

## 📋 Table of Contents

- [Environment Variables](#environment-variables)
- [Command-Line Options](#command-line-options)
- [Configuration Files](#configuration-files)
- [Performance Tuning](#performance-tuning)
- [Advanced Settings](#advanced-settings)

## 🌍 Environment Variables

Configure API keys and global settings using environment variables in your `.env` file.

### API Configuration

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your_openai_api_key_here
OPENAI_MODEL=gpt-4                    # Optional: specify model version
OPENAI_MAX_TOKENS=2000               # Optional: max tokens per request
OPENAI_TEMPERATURE=0.1               # Optional: response randomness (0.0-1.0)

# Hugging Face Configuration  
HUGGINGFACE_TOKEN=hf_your_token_here
HUGGINGFACE_MODEL=pyannote/speaker-diarization-3.1  # Optional: specify model

# Default Processing Settings
DEFAULT_WHISPER_MODEL=base           # tiny, base, small, medium, large
DEFAULT_OUTPUT_FORMAT=markdown       # fcpxml, itt, markdown, json
DEFAULT_PREPROCESSING=true           # Enable audio preprocessing by default
DEFAULT_DIARIZATION=false           # Enable speaker diarization by default
```

### Directory Configuration

```bash
# Default Directories
DEFAULT_INPUT_DIR=./input           # Where to look for media files
DEFAULT_OUTPUT_DIR=./output         # Where to save processed files
DEFAULT_TEMP_DIR=/tmp              # Temporary file storage

# Processing Directories
TRANSCRIPTS_DIR=./transcripts      # Intermediate transcription files
CORRECTED_DIR=./corrected          # AI-corrected transcripts
DIARIZED_DIR=./diarized           # Speaker-labeled transcripts
TRANSLATED_DIR=./translated       # Translated transcripts
```

### Processing Configuration

```bash
# Audio Processing
AUDIO_SAMPLE_RATE=16000           # Sample rate for audio processing
AUDIO_CHANNELS=1                  # Number of audio channels (1=mono)
ENHANCEMENT_LEVEL=standard        # minimal, standard, aggressive

# Performance Settings
MAX_WORKERS=4                     # Number of parallel processing threads
BATCH_SIZE=10                     # Number of segments to process at once
MEMORY_LIMIT=8GB                  # Maximum memory usage
GPU_ENABLED=auto                  # auto, true, false
```

### Logging and Debug

```bash
# Logging Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_FILE=./logs/transcriber.log   # Log file location
VERBOSE_OUTPUT=false              # Enable detailed console output

# Debug Settings
DEBUG_MODE=false                  # Enable debug features
SAVE_TEMP_FILES=false            # Keep temporary files for debugging
PROFILING=false                  # Enable performance profiling
```

## ⚙️ Command-Line Options

Detailed breakdown of all command-line parameters for each module.

### Unified Pipeline (`run_transcription_pipeline_v2.py`)

```bash
python run_transcription_pipeline_v2.py [OPTIONS]

Options:
  --input-dir PATH          Input directory (default: ./input)
  --output-dir PATH         Output directory (default: ./output)
  --format FORMAT           Output format: fcpxml, itt, markdown, json
  --model MODEL            Whisper model: tiny, base, small, medium, large
  --no-preprocessing       Disable audio preprocessing
  --cleanup-level LEVEL    AI cleanup: minimal, standard, aggressive
  --target-language LANG   Translation target language
  --num-speakers INT       Force specific number of speakers
  --simple-diarization     Use simple timing-based speaker detection
  --batch                  Non-interactive batch mode
  --config FILE            Configuration file path
  --verbose                Enable verbose output
  --help                   Show help message
```

### Transcription Module (`scripts/transcribe.py`)

```bash
python scripts/transcribe.py [OPTIONS]

Required:
  --input-dir, -i PATH      Directory containing media files
  --output-dir, -o PATH     Directory to save JSON transcripts

Optional:
  --model, -m MODEL         Whisper model (default: base)
                           Options: tiny, base, small, medium, large
  --recursive, -r           Process subdirectories recursively
  --preprocessing           Enable audio preprocessing
  --enhancement-level LEVEL Audio enhancement level
                           Options: minimal, standard, aggressive
  --initial-prompt TEXT     Initial prompt to guide Whisper
  --language LANG          Source language code (auto-detect if not set)
  --device DEVICE          Processing device: auto, cpu, cuda, mps
  --verbose                Enable verbose output
  --help                   Show help and exit

Examples:
  # Basic transcription
  python scripts/transcribe.py -i input -o transcripts
  
  # High-quality with preprocessing
  python scripts/transcribe.py -i input -o transcripts --model large --preprocessing
  
  # Recursive with custom enhancement
  python scripts/transcribe.py -i media_archive -o transcripts -r --enhancement-level aggressive
```

### Speaker Diarization (`scripts/diarize_transcript.py`)

```bash
python scripts/diarize_transcript.py [OPTIONS]

Required:
  --input-dir, -i PATH      Directory containing transcript JSON files
  --output-dir, -o PATH     Directory to save diarized transcripts

Optional:
  --hf-token TOKEN         Hugging Face token (or use HUGGINGFACE_TOKEN env var)
  --num-speakers INT       Expected number of speakers (auto-detect if not set)
  --device DEVICE          Processing device: auto, cpu, cuda, mps
  --simple-only            Use only simple timing-based detection
  --min-speakers INT       Minimum number of speakers to detect (default: 1)
  --max-speakers INT       Maximum number of speakers to detect (default: 10)
  --clustering-threshold FLOAT  Speaker clustering threshold (default: 0.5)
  --verbose                Enable verbose output
  --help                   Show help and exit

Examples:
  # Advanced diarization with HF token
  python scripts/diarize_transcript.py -i transcripts -o diarized --hf-token $HF_TOKEN
  
  # Simple diarization without token
  python scripts/diarize_transcript.py -i transcripts -o diarized --simple-only
  
  # Force specific speaker count
  python scripts/diarize_transcript.py -i transcripts -o diarized --num-speakers 3
```

### Context Correction (`scripts/context_correct_transcript.py`)

```bash
python scripts/context_correct_transcript.py [OPTIONS]

Required:
  --input-dir, -i PATH      Directory containing transcript JSON files
  --output-dir, -o PATH     Directory to save corrected transcripts
  --api-key KEY            OpenAI API key (or use OPENAI_API_KEY env var)

Optional:
  --cleanup-level LEVEL    Cleanup intensity level (default: standard)
                          Options: minimal, standard, aggressive, custom
  --custom-prompt TEXT     Custom cleanup instructions (use with --cleanup-level custom)
  --language LANG          Content language for language-specific corrections
  --batch-size INT         Number of segments to process together (default: 10)
  --model MODEL            OpenAI model to use (default: gpt-4)
  --temperature FLOAT      Response creativity level (default: 0.1)
  --max-tokens INT         Maximum tokens per request (default: 2000)
  --verbose                Enable verbose output
  --help                   Show help and exit

Examples:
  # Standard cleanup
  python scripts/context_correct_transcript.py -i transcripts -o corrected --api-key $OPENAI_KEY
  
  # Minimal cleanup preserving speech patterns
  python scripts/context_correct_transcript.py -i transcripts -o corrected --cleanup-level minimal
  
  # Custom cleanup with specific instructions
  python scripts/context_correct_transcript.py -i transcripts -o corrected --cleanup-level custom \
    --custom-prompt "Fix errors but preserve technical terminology and speaker expertise level"
```

### Translation (`scripts/translate_transcript.py`)

```bash
python scripts/translate_transcript.py [OPTIONS]

Required:
  --transcript-dir, -i PATH Directory containing transcript JSON files
  --output-dir, -o PATH     Directory to save translated transcripts
  --target-language LANG   Target language for translation
  --api-key KEY            OpenAI API key (or use OPENAI_API_KEY env var)

Optional:
  --batch-size INT         Segments to translate together (default: 5)
  --model MODEL            OpenAI model to use (default: gpt-4)
  --preserve-timing        Maintain original timing information (default: true)
  --context-window INT     Number of surrounding segments for context (default: 2)
  --formality LEVEL        Translation formality: formal, informal, auto (default: auto)
  --verbose                Enable verbose output
  --help                   Show help and exit

Supported Languages:
  English, Spanish, French, German, Italian, Portuguese, Dutch,
  Russian, Japanese, Chinese, Korean, Arabic, Hindi

Examples:
  # Translate to Spanish
  python scripts/translate_transcript.py -i corrected -o spanish --target-language Spanish
  
  # Formal translation with larger context
  python scripts/translate_transcript.py -i corrected -o formal_french \
    --target-language French --formality formal --context-window 5
```

### Output Generation

#### FCPXML Generation (`scripts/generate_fcpxml.py`)

```bash
python scripts/generate_fcpxml.py [OPTIONS]

Required:
  --input-dir, -i PATH      Directory containing transcript JSON files
  --output-dir, -o PATH     Directory to save FCPXML files

Optional:
  --project-name TEXT      FCPXML project name (default: "Subtitles")
  --max-duration FLOAT     Maximum subtitle duration in seconds (default: 5.0)
  --max-chars INT          Maximum characters per subtitle (default: 60)
  --include-speakers       Include speaker labels in subtitles
  --video-metadata         Use video metadata for timing (requires video files)
  --frame-rate FLOAT       Override frame rate (default: auto-detect)
  --resolution TEXT        Video resolution WIDTHxHEIGHT (default: 1920x1080)
  --verbose                Enable verbose output
  --help                   Show help and exit
```

#### ITT Generation (`scripts/generate_itt.py`)

```bash
python scripts/generate_itt.py [OPTIONS]

Required:
  --input-dir, -i PATH      Directory containing transcript JSON files
  --output-dir, -o PATH     Directory to save ITT files

Optional:
  --max-duration FLOAT     Maximum subtitle duration (default: 5.0)
  --max-chars INT          Maximum characters per subtitle (default: 50)
  --include-speakers       Include speaker labels
  --language-code LANG     ITT language code (default: en)
  --region-style STYLE     Subtitle region style: bottom, top, center
  --font-family FONT       Font family for subtitles
  --font-size SIZE         Font size (default: medium)
  --verbose                Enable verbose output
  --help                   Show help and exit
```

#### Markdown Generation (`scripts/generate_markdown.py`)

```bash
python scripts/generate_markdown.py [OPTIONS]

Required:
  --input-dir, -i PATH      Directory containing transcript JSON files
  --output-dir, -o PATH     Directory to save Markdown files

Optional:
  --include-timecodes      Include timestamp information
  --include-speakers       Include speaker identification
  --speaker-names TEXT     Comma-separated list of speaker names
  --format-style STYLE     Markdown style: standard, interview, meeting
  --paragraph-breaks       Add paragraph breaks for readability
  --summary                Generate content summary (requires OpenAI API)
  --word-count             Include word count statistics
  --verbose                Enable verbose output
  --help                   Show help and exit

Examples:
  # Full-featured transcript
  python scripts/generate_markdown.py -i diarized -o final \
    --include-timecodes --include-speakers --speaker-names "Host,Guest,Expert"
  
  # Interview format with summary
  python scripts/generate_markdown.py -i corrected -o interviews \
    --format-style interview --summary --paragraph-breaks
```

## 📁 Configuration Files

### Global Configuration File

Create a `config.yaml` file for project-wide settings:

```yaml
# Transcriber v2.0 Configuration

# Processing Settings
processing:
  whisper_model: "base"
  enhancement_level: "standard"
  enable_preprocessing: true
  enable_diarization: false
  cleanup_level: "standard"
  
# API Settings
api:
  openai:
    model: "gpt-4"
    temperature: 0.1
    max_tokens: 2000
  huggingface:
    model: "pyannote/speaker-diarization-3.1"

# Directories
directories:
  input: "./input"
  output: "./output"
  temp: "./temp"
  logs: "./logs"

# Output Formats
output:
  fcpxml:
    max_duration: 5.0
    max_chars: 60
    include_speakers: false
  itt:
    max_duration: 5.0
    max_chars: 50
    language_code: "en"
  markdown:
    include_timecodes: true
    include_speakers: true
    format_style: "standard"

# Performance
performance:
  max_workers: 4
  batch_size: 10
  gpu_enabled: "auto"
  memory_limit: "8GB"

# Logging
logging:
  level: "INFO"
  file: "./logs/transcriber.log"
  verbose: false
```

### Module-Specific Configuration

Create configuration files for individual modules:

**`transcribe_config.yaml`:**
```yaml
whisper:
  model: "base"
  device: "auto"
  preprocessing: true
  enhancement_level: "standard"
  initial_prompt: ""
  language: "auto"
  
audio:
  sample_rate: 16000
  channels: 1
  
performance:
  batch_size: 1
  parallel_jobs: 2
```

## ⚡ Performance Tuning

### Hardware Optimization

#### CPU Optimization
```bash
# Set CPU-specific settings
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

# Use CPU-only PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### GPU Optimization
```bash
# NVIDIA GPU settings
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Use GPU PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Apple Silicon (M1/M2) Optimization
```bash
# Use Metal Performance Shaders
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0

# Optimize for M1/M2
python scripts/transcribe.py --device mps
```

### Memory Management

#### For Large Files (>1GB)
```bash
# Use smaller models and batch sizes
python scripts/transcribe.py --model tiny --batch-size 5

# Process in chunks
python scripts/transcribe.py --max-duration 1800  # 30 minutes max
```

#### For Limited RAM (<8GB)
```bash
# Minimal memory configuration
DEFAULT_WHISPER_MODEL=tiny
BATCH_SIZE=1
MAX_WORKERS=1
MEMORY_LIMIT=4GB
```

### Network Optimization

#### API Rate Limiting
```bash
# Slower but more reliable processing
API_RATE_LIMIT=30         # Requests per minute
API_RETRY_ATTEMPTS=3      # Number of retries
API_RETRY_DELAY=5         # Seconds between retries
```

## 🔬 Advanced Settings

### Custom Model Configuration

#### Using Custom Whisper Models
```bash
# Local model path
WHISPER_MODEL_PATH=/path/to/custom/whisper/model

# Hugging Face model
WHISPER_MODEL_ID=openai/whisper-large-v3
```

#### Custom Diarization Models
```bash
# Alternative pyannote models
DIARIZATION_MODEL=pyannote/speaker-diarization-3.0
SEGMENTATION_MODEL=pyannote/segmentation-3.0
EMBEDDING_MODEL=pyannote/wespeaker-voxceleb-resnet34-LM
```

### Audio Processing Pipeline

#### Custom FFmpeg Filters
```yaml
audio_filters:
  noise_reduction:
    enabled: true
    strength: 0.5
  
  equalization:
    enabled: true
    frequencies:
      - {freq: 3000, gain: 2, width: 500}
  
  normalization:
    enabled: true
    target_lufs: -16
    peak_limit: -1.5
```

### Quality Control

#### Transcription Confidence
```bash
# Enable confidence scoring
CONFIDENCE_THRESHOLD=0.8     # Skip segments below threshold
CONFIDENCE_REPORTING=true    # Include confidence in output
QUALITY_METRICS=true         # Generate quality reports
```

#### Output Validation
```bash
# Validation settings
VALIDATE_TIMING=true         # Check timestamp consistency
VALIDATE_SPEAKERS=true       # Verify speaker labeling
VALIDATE_TEXT_LENGTH=true    # Check text length limits
MAX_SEGMENT_GAP=10.0        # Maximum gap between segments (seconds)
```

### Development and Debug

#### Debug Configuration
```bash
# Debug settings
DEBUG_MODE=true
SAVE_INTERMEDIATE_FILES=true
PROFILING=true
DETAILED_LOGS=true

# Debug output directories
DEBUG_AUDIO_DIR=./debug/audio
DEBUG_TRANSCRIPTS_DIR=./debug/transcripts
DEBUG_MODELS_DIR=./debug/models
```

#### Testing Configuration
```bash
# Test settings
TEST_MODE=true
USE_MOCK_APIS=true
MOCK_API_DELAY=0.1
SMALL_TEST_FILES=true
```

---

This configuration guide should help you optimize Transcriber v2.0 for your specific needs and hardware setup. For additional help with configuration issues, see the [troubleshooting guide](USAGE_EXAMPLES.md#troubleshooting-common-issues).
