# Usage Examples and Tutorials

This guide provides practical examples and step-by-step tutorials for using Transcriber v2.0 effectively.

## 📋 Table of Contents

- [Quick Start Examples](#quick-start-examples)
- [Individual Module Usage](#individual-module-usage)
- [Common Workflows](#common-workflows)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)

## 🚀 Quick Start Examples

### Example 1: Basic Video Transcription

Convert a single video file to a readable transcript:

```bash
# Step 1: Place your video file
cp my_video.mp4 input/

# Step 2: Run the unified pipeline
python run_transcription_pipeline_v2.py

# Follow the interactive prompts:
# - Choose format: Markdown
# - Select files: my_video.mp4
# - Enable preprocessing: Yes
# - Skip AI features for now

# Result: output/my_video.md with readable transcript
```

### Example 2: Professional Subtitles for Video Editing

Create FCPXML subtitles for Final Cut Pro:

```bash
# Step 1: Set up API key (optional but recommended)
cp .env.template .env
# Edit .env and add: OPENAI_API_KEY=sk-your_key_here

# Step 2: Run with context correction
python run_transcription_pipeline_v2.py

# Interactive choices:
# - Format: FCPXML
# - Files: interview.mp4
# - Preprocessing: Yes
# - Context correction: Yes
# - Speaker diarization: No (single speaker)

# Result: output/interview.fcpxml ready for Final Cut Pro
```

### Example 3: Multi-Speaker Interview Analysis

Analyze an interview with multiple speakers:

```bash
# Set up both API keys in .env:
# OPENAI_API_KEY=sk-your_key
# HUGGINGFACE_TOKEN=hf_your_token

python run_transcription_pipeline_v2.py

# Choices:
# - Format: Markdown
# - Files: interview.mp4
# - Preprocessing: Yes
# - Speaker diarization: Yes (advanced)
# - Context correction: Yes
# - Include speakers: Yes
# - Include timecodes: Yes

# Result: Clean transcript with speaker labels and timestamps
```

## 🔧 Individual Module Usage

### Module 1: Transcription

Basic audio-to-text conversion using Whisper:

```bash
# Transcribe with different model sizes
python scripts/transcribe.py \
  --input-dir input \
  --output-dir transcripts \
  --model base \
  --preprocessing

# Available models: tiny, base, small, medium, large
# - tiny: Fastest, least accurate (~1min for 10min audio)
# - base: Good balance (~3min for 10min audio)
# - large: Most accurate (~10min for 10min audio)
```

**Example Output Structure:**
```json
[
  {
    "start": 0.0,
    "end": 3.5,
    "text": "Hello and welcome to our podcast today."
  },
  {
    "start": 3.5,
    "end": 7.2,
    "text": "We're discussing artificial intelligence in education."
  }
]
```

### Module 2: Speaker Diarization

Add speaker labels to existing transcripts:

```bash
# Advanced diarization (requires Hugging Face token)
python scripts/diarize_transcript.py \
  --input-dir transcripts \
  --output-dir diarized \
  --hf-token $HUGGINGFACE_TOKEN

# Simple diarization (no token required)
python scripts/diarize_transcript.py \
  --input-dir transcripts \
  --output-dir diarized \
  --simple-only

# Force specific number of speakers
python scripts/diarize_transcript.py \
  --input-dir transcripts \
  --output-dir diarized \
  --num-speakers 2
```

**Example Output with Speakers:**
```json
[
  {
    "start": 0.0,
    "end": 3.5,
    "text": "Hello and welcome to our podcast today.",
    "speaker": "SPEAKER_00"
  },
  {
    "start": 3.5,
    "end": 7.2,
    "text": "Thanks for having me on the show.",
    "speaker": "SPEAKER_01"
  }
]
```

### Module 3: AI Context Correction

Clean up transcripts with AI assistance:

```bash
# Standard cleanup (recommended)
python scripts/context_correct_transcript.py \
  --input-dir transcripts \
  --output-dir corrected \
  --api-key $OPENAI_API_KEY \
  --cleanup-level standard

# Minimal cleanup (preserve natural speech)
python scripts/context_correct_transcript.py \
  --input-dir transcripts \
  --output-dir corrected \
  --api-key $OPENAI_API_KEY \
  --cleanup-level minimal

# Aggressive cleanup (publication-ready)
python scripts/context_correct_transcript.py \
  --input-dir transcripts \
  --output-dir corrected \
  --api-key $OPENAI_API_KEY \
  --cleanup-level aggressive
```

**Before vs After Examples:**

*Original:* "Um, so like, there systems are there to help students learn better, you know?"

*Minimal:* "Um, so like, these systems are there to help students learn better, you know?"

*Standard:* "So these systems are there to help students learn better."

*Aggressive:* "These systems are designed to help students learn more effectively."

### Module 4: Translation

Translate transcripts while preserving timing:

```bash
# Translate to Spanish
python scripts/translate_transcript.py \
  --transcript-dir corrected \
  --output-dir translated \
  --target-language Spanish \
  --api-key $OPENAI_API_KEY

# Supported languages: Spanish, French, German, Italian, 
# Portuguese, Dutch, Russian, Japanese, Chinese, Korean
```

### Module 5: Output Generation

Create final output formats:

```bash
# Generate FCPXML for Final Cut Pro
python scripts/generate_fcpxml.py \
  --input-dir corrected \
  --output-dir final_fcpxml

# Generate ITT subtitles
python scripts/generate_itt.py \
  --input-dir corrected \
  --output-dir final_itt

# Generate Markdown with all features
python scripts/generate_markdown.py \
  --input-dir diarized \
  --output-dir final_markdown \
  --include-speakers \
  --include-timecodes \
  --speaker-names "Host,Guest"
```

## 🎯 Common Workflows

### Workflow 1: Podcast Processing Pipeline

Complete pipeline for podcast episodes:

```bash
# 1. Basic transcription
python scripts/transcribe.py \
  --input-dir podcasts \
  --output-dir step1_transcripts \
  --model base \
  --preprocessing

# 2. Speaker diarization
python scripts/diarize_transcript.py \
  --input-dir step1_transcripts \
  --output-dir step2_diarized \
  --num-speakers 2

# 3. Context correction
python scripts/context_correct_transcript.py \
  --input-dir step2_diarized \
  --output-dir step3_corrected \
  --cleanup-level standard

# 4. Generate readable transcript
python scripts/generate_markdown.py \
  --input-dir step3_corrected \
  --output-dir final_podcasts \
  --include-speakers \
  --speaker-names "Host,Guest"
```

### Workflow 2: Interview Analysis

For research interviews and qualitative analysis:

```bash
# 1. High-quality transcription
python scripts/transcribe.py \
  --input-dir interviews \
  --output-dir step1_raw \
  --model large  # Most accurate

# 2. Advanced speaker diarization
python scripts/diarize_transcript.py \
  --input-dir step1_raw \
  --output-dir step2_speakers

# 3. Minimal cleanup (preserve authentic speech)
python scripts/context_correct_transcript.py \
  --input-dir step2_speakers \
  --output-dir step3_clean \
  --cleanup-level minimal

# 4. Generate analysis-ready format
python scripts/generate_markdown.py \
  --input-dir step3_clean \
  --output-dir final_interviews \
  --include-speakers \
  --include-timecodes
```

### Workflow 3: Video Production Subtitles

Professional subtitles for video content:

```bash
# 1. Transcribe with preprocessing
python scripts/transcribe.py \
  --input-dir videos \
  --output-dir step1_transcripts \
  --model base \
  --preprocessing \
  --enhancement-level standard

# 2. AI cleanup for readability
python scripts/context_correct_transcript.py \
  --input-dir step1_transcripts \
  --output-dir step2_clean \
  --cleanup-level aggressive

# 3. Generate professional formats
python scripts/generate_fcpxml.py \
  --input-dir step2_clean \
  --output-dir fcpxml_subtitles

python scripts/generate_itt.py \
  --input-dir step2_clean \
  --output-dir itt_subtitles
```

## 🔬 Advanced Usage

### Batch Processing Multiple Files

Process entire directories of media files:

```bash
# Process all videos in subdirectories
python scripts/transcribe.py \
  --input-dir media_archive \
  --output-dir batch_transcripts \
  --model base \
  --recursive \
  --preprocessing

# Results organized by original directory structure
```

### Custom Cleanup Instructions

Use custom AI instructions for specialized content:

```bash
# Custom prompt for technical content
python scripts/context_correct_transcript.py \
  --input-dir technical_talks \
  --output-dir cleaned_technical \
  --cleanup-level custom \
  --custom-prompt "Fix transcription errors while preserving technical terminology. Do not simplify technical concepts. Maintain speaker's expertise level."
```

### Multi-language Workflows

Handle content in different languages:

```bash
# 1. Transcribe in original language
python scripts/transcribe.py \
  --input-dir spanish_videos \
  --output-dir spanish_transcripts \
  --model base

# 2. Translate to English
python scripts/translate_transcript.py \
  --transcript-dir spanish_transcripts \
  --output-dir english_versions \
  --target-language English

# 3. Generate bilingual outputs
python scripts/generate_markdown.py \
  --input-dir spanish_transcripts \
  --output-dir bilingual_output \
  --include-timecodes
```

### Performance Optimization

Tips for handling large files efficiently:

```bash
# Use smaller model for initial pass
python scripts/transcribe.py \
  --model tiny \
  --input-dir large_files \
  --output-dir quick_drafts

# Then upgrade important files
python scripts/transcribe.py \
  --model large \
  --input-dir selected_files \
  --output-dir final_transcripts
```

## 🛠 Troubleshooting Common Issues

### Issue 1: Audio Quality Problems

**Problem:** Poor transcription accuracy

**Solutions:**
```bash
# Try different audio enhancement levels
python scripts/transcribe.py \
  --enhancement-level aggressive \
  --model medium

# Or skip preprocessing for high-quality audio
python scripts/transcribe.py \
  --model large  # No --preprocessing flag
```

### Issue 2: Speaker Diarization Errors

**Problem:** Speakers not correctly identified

**Solutions:**
```bash
# Specify exact number of speakers
python scripts/diarize_transcript.py \
  --num-speakers 3

# Try simple mode for difficult audio
python scripts/diarize_transcript.py \
  --simple-only
```

### Issue 3: Memory Issues

**Problem:** Out of memory errors with large files

**Solutions:**
```bash
# Use smaller Whisper model
python scripts/transcribe.py --model tiny

# Process shorter segments
# Split large files into 30-minute chunks first
```

### Issue 4: API Rate Limits

**Problem:** OpenAI API rate limiting

**Solutions:**
- Use smaller batch sizes in context correction
- Add delays between requests
- Upgrade OpenAI API tier for higher limits

### Issue 5: File Format Issues

**Problem:** Unsupported media formats

**Solutions:**
```bash
# Convert to supported format first
ffmpeg -i input.mov -c copy output.mp4

# Supported formats: mp4, wav, m4a, flac, mp3
```

## 📊 Expected Processing Times

Reference times for planning (10-minute audio file):

| Process | Model/Level | Time | Quality |
|---------|-------------|------|---------|
| Transcription | tiny | ~1 min | Basic |
| Transcription | base | ~3 min | Good |
| Transcription | large | ~8 min | Excellent |
| Diarization | simple | ~30 sec | Basic |
| Diarization | advanced | ~2 min | Excellent |
| Context Correction | standard | ~1 min | - |
| Translation | - | ~1 min | - |
| Output Generation | - | ~10 sec | - |

**Total pipeline time:** 5-15 minutes depending on options selected.

---

These examples should help you get the most out of Transcriber v2.0. For additional help, see the [troubleshooting section](README.md#troubleshooting) in the main README.
