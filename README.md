# 🎯 Transcriber v2.0 - Modular Transcription Pipeline

A comprehensive, modular transcription pipeline featuring AI-enhanced accuracy, flexible output formats, and professional-grade subtitle generation.

## ✨ Features

- **🔊 Advanced Audio Processing** - Noise reduction and optimization for better transcription
- **🧠 Multiple Whisper Models** - From fast (tiny) to most accurate (large)
- **🤖 AI Context Correction** - GPT-4 powered grammar and homophone fixes
- **🌐 Multi-language Translation** - Translate transcripts while preserving timing
- **🎭 Speaker Diarization** - Automatic speaker identification
- **📄 Multiple Output Formats** - FCPXML, ITT, Markdown, JSON
- **🔧 Modular Architecture** - Use individual modules or the unified pipeline
- **💡 User-Friendly Interface** - Clear explanations and smart defaults

## 🚀 Quick Start

### 1. Installation
```bash
# Clone or download the project
cd transcriber-v2.0

# Run the installation script
./install.sh

# Or install manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Setup API Keys (Optional)
```bash
# Copy the template and add your OpenAI API key
cp .env.template .env
# Edit .env and add your OpenAI API key for AI features
```

### 3. Run the Pipeline
```bash
# Start the interactive pipeline
python run_transcription_pipeline_v2.py

# Follow the guided interface to:
# 1. Choose output format (FCPXML, ITT, Markdown, JSON)
# 2. Select input files
# 3. Configure processing options
# 4. Generate results
```

## 📋 Requirements

- **Python 3.8+**
- **FFmpeg** (for audio preprocessing - recommended)
- **OpenAI API Key** (optional - for AI features)

## 🏗 Architecture

The v2.0 system is built on modular principles:
- **Modularity**: Each script does one thing well
- **User Choice**: Maximum flexibility at each decision point
- **Transparency**: Clear cost estimates and feature explanations
- **Quality**: Professional-grade outputs for video production workflows

## 🔧 Individual Modules

Each module can be used independently:

```bash
# 1. Basic transcription
python scripts/transcribe.py --input-dir input --output-dir output --model base --preprocessing

# 2. Speaker diarization
python scripts/diarize_transcript.py --input-dir transcripts --output-dir diarized

# 3. AI context correction
python scripts/context_correct_transcript.py --input-dir transcripts --output-dir corrected --api-key $OPENAI_API_KEY

# 4. Translation
python scripts/translate_transcript.py --transcript-dir transcripts --output-dir translated --target-language Spanish --api-key $OPENAI_API_KEY

# 5. Generate outputs
python scripts/generate_fcpxml.py --input-dir transcripts --output-dir fcpxml
python scripts/generate_itt.py --input-dir transcripts --output-dir itt
python scripts/generate_markdown.py --input-dir transcripts --output-dir markdown --include-timecodes --include-speakers
```

## Modular Architecture

1. **Transcription (Whisper)**
   - Script: `transcribe.py`
   - Function: Convert audio to text with timestamps.
   - Options: Select model size (tiny, base, small, medium, large).

2. **Diarization**
   - Script: `diarize_transcript.py`
   - Function: Add speaker labels to transcript.
   - Options: Enable/disable speaker labeling.

3. **Context Correction (AI)**
   - Script: `context_correct_transcript.py`
   - Function: Automatic homophone/grammar correction.
   - Options: Enable/disable context correction.

4. **Translation (OpenAI)**
   - Script: `translate_transcript.py`
   - Function: Translate text to selected language.
   - Options: Enable/disable translation, select target language.

5. **Subtitle Generation (FCPXML, ITT)**
   - Scripts: `generate_fcpxml.py`, `generate_itt.py`
   - Function: Convert transcript to subtitle files.
   - Options: Include timecodes, speaker names.
   
6. **Markdown Generation**
   - Script: `generate_markdown.py`
   - Function: Output readable transcripts.
   - Options: Include timecodes, speaker names.

7. **JSON Export**
   - Script: `export_json.py`
   - Function: Output raw transcription data.
   - Options: Enable/disable preprocessing.

## Detailed Testing Matrix

### Source Files
**Primary Test Video**: `PXL_20231202_083328497 copy.mp4` (provided in this directory)
- Size: ~64MB
- Previously tested successfully in v1.0
- Contains clear English speech suitable for transcription, translation, and diarization testing
- Will be used for ALL test scenarios to ensure consistent comparison across routes

### Test Scenarios

#### 1. FCPXML Route Tests
```
fcpxml/
├── basic_english/                    # Raw transcription → FCPXML
├── corrected_english/               # Transcription → Context Correct → FCPXML  
├── translated_spanish/              # Transcription → Translate(Spanish) → FCPXML
├── corrected_translated_mandarin/   # Transcription → Context Correct → Translate(Mandarin) → FCPXML
└── model_comparison/                # Same file with different Whisper models
```

#### 2. ITT Route Tests
```
itt/
├── basic_english/                   # Raw transcription → ITT
├── corrected_english/              # Transcription → Context Correct → ITT
├── translated_french/              # Transcription → Translate(French) → ITT
└── multilanguage_comparison/       # Same content in multiple target languages
```

#### 3. Markdown Route Tests
```
markdown/
├── basic_transcript/               # Raw transcription → Markdown (no speakers, no timecodes)
├── with_timecodes/                 # Raw transcription → Markdown (timecodes only)
├── with_speakers/                  # Transcription → Diarize → Markdown (speakers, no timecodes)
├── full_featured/                  # Transcription → Diarize → Markdown (speakers + timecodes)
├── corrected_content/              # Transcription → Context Correct → Markdown
├── translated_content/             # Transcription → Translate → Markdown
└── complete_pipeline/              # Transcription → Diarize → Context Correct → Translate → Markdown
```

#### 4. JSON Route Tests
```
json/
├── raw_whisper_output/             # Pure Whisper transcription
├── diarized_content/               # Transcription → Diarize → JSON
├── context_corrected/              # Transcription → Context Correct → JSON
├── translated_versions/            # Transcription → Translate → JSON
└── full_processing/                # All processing steps → JSON
```

### Implementation Roadmap

#### Phase 1: Extract Core Modules (from existing v1.0 codebase)
1. Extract `transcribe.py` from existing transcription logic
2. Extract `context_correct_transcript.py` from context correction functions
3. Copy and adapt `translate_transcript.py` (already modular)
4. Extract `generate_fcpxml.py` from FCPXML generation logic
5. Extract `generate_itt.py` from ITT generation logic
6. Create new `generate_markdown.py` with flexible options
7. Create `diarize_transcript.py` from existing diarization logic

#### Phase 2: Build New Unified Interface
1. Create `run_transcription_pipeline_v2.py` that orchestrates modules
2. Implement decision tree with all user choices
3. Preserve existing features: cost estimation, video metadata, JSON reuse
4. Add new features: flexible markdown options, module selection

#### Phase 3: Autonomous Testing
1. Create test runner script
2. Execute all test scenarios automatically
3. Generate outputs in organized directory structure
4. Create validation reports

## 📁 Project Structure

```
transcriber-v2.0/
├── README.md                        # Project documentation
├── LICENSE                          # MIT License
├── requirements.txt                 # Python dependencies
├── setup.py                         # Package setup
├── install.sh                       # Installation script
├── .env.template                    # Environment template
├── .gitignore                       # Git ignore rules
├── run_transcription_pipeline_v2.py # Unified pipeline interface
├── scripts/                         # Modular scripts
│   ├── transcribe.py                # Whisper transcription
│   ├── diarize_transcript.py        # Speaker identification
│   ├── context_correct_transcript.py # AI grammar correction
│   ├── translate_transcript.py      # Multi-language translation
│   ├── generate_fcpxml.py           # Final Cut Pro XML
│   ├── generate_itt.py              # ITT subtitles
│   ├── generate_markdown.py         # Readable transcripts
│   └── run_all_tests.py             # Automated testing
├── input/                           # Input media files
├── output/                          # Generated results
├── tests/                           # Unit tests
├── docs/                            # Documentation
└── sample_inputs/                   # Sample files
```

## 🎛 Processing Options

### Audio Preprocessing (Recommended)
- **Noise reduction** using bandpass filtering
- **16kHz resampling** for optimal Whisper performance
- **Automatic fallback** if FFmpeg unavailable

### AI Enhancements (Optional)
- **Context Correction**: Fixes grammar and homophones using GPT-4
- **Translation**: Supports 8+ languages with natural translation
- **Cost transparent**: Clear estimates before processing

### Output Formats
- **FCPXML**: Professional subtitles for Final Cut Pro
- **ITT**: Standard subtitles for video players
- **Markdown**: Human-readable transcripts with speakers/timecodes
- **JSON**: Raw data for custom processing

## 🧪 Testing

```bash
# Run all automated tests
python scripts/run_all_tests.py

# Run unit tests
python -m pytest tests/

# Test individual modules
python scripts/transcribe.py --help
```

## 📖 Documentation

- **Interactive Pipeline**: Run `python run_transcription_pipeline_v2.py` for guided setup
- **Module Help**: Each script has `--help` for detailed options
- **Cost Estimation**: AI features show cost estimates before processing
- **Error Handling**: Graceful fallbacks and clear error messages

## 🤝 Contributing

The modular architecture makes it easy to:
- Add new output formats
- Integrate different AI models
- Customize processing steps
- Add new languages

## 📄 License

MIT License - see LICENSE file for details.

---

**Transcriber v2.0** - Professional transcription made simple and modular.
