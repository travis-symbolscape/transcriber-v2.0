#!/usr/bin/env python3
"""
Automated Test Runner for v2.0 Modular Pipeline

This script tests all combinations of the modular pipeline:
- Different routes (FCPXML, ITT, Markdown, JSON)
- Different processing options (context correction, translation, diarization)
- Different output formats
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Configuration
BASE_DIR = os.path.expanduser("~/Desktop/transcriber_v2_tests")
VIDEO_FILE = f"{BASE_DIR}/sample_inputs/sample_video.mp4"
API_KEY = os.getenv("OPENAI_API_KEY")

def run_command(cmd, description, timeout=120):  # 2 minute timeout
    """Run a command with a timeout and return success status"""
    """Run a command and return success status"""
    print(f"\n🔄 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)
        print(f"✅ Success: {description}")
        return True
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout: {description} (took longer than {timeout}s)")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description}")
        print(f"Error: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def test_basic_transcription():
    """Test 1: Basic transcription"""
    print("\n" + "="*60)
    print("TEST 1: BASIC TRANSCRIPTION")
    print("="*60)
    
    input_dir = f"{BASE_DIR}/sample_inputs"
    output_dir = f"{BASE_DIR}/test_outputs/json/raw_whisper_output"
    
    os.makedirs(output_dir, exist_ok=True)
    
    cmd = [
        "python", f"{BASE_DIR}/scripts/transcribe.py",
        "--input-dir", input_dir,
        "--output-dir", output_dir,
        "--model", "base"
    ]
    
    return run_command(cmd, "Basic Whisper transcription")


def test_context_correction():
    """Test 2: Context correction"""
    print("\n" + "="*60)
    print("TEST 2: CONTEXT CORRECTION")
    print("="*60)
    
    if not API_KEY:
        print("❌ Skipping: No OpenAI API key found")
        return False
    
    input_dir = f"{BASE_DIR}/test_outputs/json/raw_whisper_output"
    output_dir = f"{BASE_DIR}/test_outputs/json/context_corrected"
    
    os.makedirs(output_dir, exist_ok=True)
    
    cmd = [
        "python", f"{BASE_DIR}/scripts/context_correct_transcript.py",
        "--input-dir", input_dir,
        "--output-dir", output_dir,
        "--api-key", API_KEY
    ]
    
    return run_command(cmd, "Context correction")


def test_translation():
    """Test 3: Translation"""
    print("\n" + "="*60)
    print("TEST 3: TRANSLATION")
    print("="*60)
    
    if not API_KEY:
        print("❌ Skipping: No OpenAI API key found")
        return False
    
    input_dir = f"{BASE_DIR}/test_outputs/json/raw_whisper_output"
    output_dir = f"{BASE_DIR}/test_outputs/json/translated_versions"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Test Spanish translation
    cmd = [
        "python", f"{BASE_DIR}/scripts/translate_transcript.py",
        "--transcript-dir", input_dir,
        "--output-dir", output_dir,
        "--target-language", "Spanish",
        "--api-key", API_KEY,
        "--skip-confirm"  # Skip interactive confirmation for automated testing
    ]
    
    return run_command(cmd, "Translation to Spanish")


def test_diarization():
    """Test 4: Diarization"""
    print("\n" + "="*60)
    print("TEST 4: DIARIZATION")
    print("="*60)
    
    input_dir = f"{BASE_DIR}/test_outputs/json/raw_whisper_output"
    output_dir = f"{BASE_DIR}/test_outputs/json/diarized_content"
    
    os.makedirs(output_dir, exist_ok=True)
    
    cmd = [
        "python", f"{BASE_DIR}/scripts/diarize_transcript.py",
        "--input-dir", input_dir,
        "--output-dir", output_dir
    ]
    
    return run_command(cmd, "Speaker diarization")


def test_fcpxml_generation():
    """Test 5: FCPXML generation variations"""
    print("\n" + "="*60)
    print("TEST 5: FCPXML GENERATION")
    print("="*60)
    
    tests = [
        ("basic_english", f"{BASE_DIR}/test_outputs/json/raw_whisper_output"),
        ("corrected_english", f"{BASE_DIR}/test_outputs/json/context_corrected"),
        ("translated_spanish", f"{BASE_DIR}/test_outputs/json/translated_versions"),
    ]
    
    results = []
    for test_name, input_dir in tests:
        if not os.path.exists(input_dir):
            print(f"❌ Skipping {test_name}: Input directory doesn't exist")
            results.append(False)
            continue
            
        output_dir = f"{BASE_DIR}/test_outputs/fcpxml/{test_name}"
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            "python", f"{BASE_DIR}/scripts/generate_fcpxml.py",
            "--input-dir", input_dir,
            "--output-dir", output_dir,
            "--project-name", f"{test_name} Subtitles"
        ]
        
        results.append(run_command(cmd, f"FCPXML generation - {test_name}"))
    
    return all(results)


def test_itt_generation():
    """Test 6: ITT generation variations"""
    print("\n" + "="*60)
    print("TEST 6: ITT GENERATION")
    print("="*60)
    
    tests = [
        ("basic_english", f"{BASE_DIR}/test_outputs/json/raw_whisper_output"),
        ("corrected_english", f"{BASE_DIR}/test_outputs/json/context_corrected"),
        ("translated_spanish", f"{BASE_DIR}/test_outputs/json/translated_versions"),
    ]
    
    results = []
    for test_name, input_dir in tests:
        if not os.path.exists(input_dir):
            print(f"❌ Skipping {test_name}: Input directory doesn't exist")
            results.append(False)
            continue
            
        output_dir = f"{BASE_DIR}/test_outputs/itt/{test_name}"
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            "python", f"{BASE_DIR}/scripts/generate_itt.py",
            "--input-dir", input_dir,
            "--output-dir", output_dir
        ]
        
        results.append(run_command(cmd, f"ITT generation - {test_name}"))
    
    return all(results)


def test_markdown_generation():
    """Test 7: Markdown generation variations"""
    print("\n" + "="*60)
    print("TEST 7: MARKDOWN GENERATION")
    print("="*60)
    
    tests = [
        ("basic_transcript", f"{BASE_DIR}/test_outputs/json/raw_whisper_output", [], "Basic transcript"),
        ("with_timecodes", f"{BASE_DIR}/test_outputs/json/raw_whisper_output", ["--include-timecodes"], "With timecodes"),
        ("with_speakers", f"{BASE_DIR}/test_outputs/json/diarized_content", ["--include-speakers"], "With speakers"),
        ("full_featured", f"{BASE_DIR}/test_outputs/json/diarized_content", ["--include-timecodes", "--include-speakers"], "Full featured"),
    ]
    
    results = []
    for test_name, input_dir, extra_args, description in tests:
        if not os.path.exists(input_dir):
            print(f"❌ Skipping {test_name}: Input directory doesn't exist")
            results.append(False)
            continue
            
        output_dir = f"{BASE_DIR}/test_outputs/markdown/{test_name}"
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            "python", f"{BASE_DIR}/scripts/generate_markdown.py",
            "--input-dir", input_dir,
            "--output-dir", output_dir
        ] + extra_args
        
        results.append(run_command(cmd, f"Markdown generation - {description}"))
    
    return all(results)


def generate_test_report():
    """Generate a test report"""
    print("\n" + "="*60)
    print("GENERATING TEST REPORT")
    print("="*60)
    
    report_path = f"{BASE_DIR}/test_reports/test_summary.md"
    os.makedirs(f"{BASE_DIR}/test_reports", exist_ok=True)
    
    # Count generated files
    output_counts = {}
    for route in ['fcpxml', 'itt', 'markdown', 'json']:
        route_dir = f"{BASE_DIR}/test_outputs/{route}"
        if os.path.exists(route_dir):
            file_count = len([f for f in Path(route_dir).rglob('*') if f.is_file()])
            output_counts[route] = file_count
        else:
            output_counts[route] = 0
    
    # Generate report
    report_content = f"""# Transcriber v2.0 Test Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Summary

### Files Generated
- **FCPXML files**: {output_counts['fcpxml']}
- **ITT files**: {output_counts['itt']}
- **Markdown files**: {output_counts['markdown']}
- **JSON files**: {output_counts['json']}

### Test Video
- File: `sample_video.mp4`
- Used for all test scenarios

### Routes Tested
1. **Basic Transcription** → JSON output
2. **Context Correction** → Improved English transcripts
3. **Translation** → Spanish language versions
4. **Diarization** → Speaker-labeled transcripts
5. **FCPXML Generation** → Final Cut Pro subtitle files
6. **ITT Generation** → Standard subtitle files
7. **Markdown Generation** → Human-readable transcripts

### Output Structure
```
test_outputs/
├── fcpxml/
│   ├── basic_english/
│   ├── corrected_english/
│   └── translated_spanish/
├── itt/
│   ├── basic_english/
│   ├── corrected_english/
│   └── translated_spanish/
├── markdown/
│   ├── basic_transcript/
│   ├── with_timecodes/
│   ├── with_speakers/
│   └── full_featured/
└── json/
    ├── raw_whisper_output/
    ├── context_corrected/
    ├── translated_versions/
    └── diarized_content/
```

## How to Test Results

### FCPXML Files
1. Open Final Cut Pro
2. File → Import → Media
3. Select any .fcpxml file from `test_outputs/fcpxml/`
4. The subtitles will appear as a compound clip

### ITT Files
- Compatible with most video players
- Can be used with VLC, QuickTime, etc.

### Markdown Files
- Open any .md file from `test_outputs/markdown/`
- Compare different formatting options

### JSON Files
- Raw transcript data
- Can be processed by other tools or reimported
"""

    with open(report_path, 'w') as f:
        f.write(report_content)
    
    print(f"✅ Test report generated: {report_path}")


def main():
    """Run all tests"""
    print("🚀 TRANSCRIBER V2.0 AUTOMATED TESTING")
    print("=====================================")
    
    if not os.path.exists(VIDEO_FILE):
        print(f"❌ Test video not found: {VIDEO_FILE}")
        sys.exit(1)
    
    print(f"📹 Test video: {os.path.basename(VIDEO_FILE)}")
    if API_KEY:
        print("🔑 OpenAI API key found - AI features will be tested")
    else:
        print("⚠️  No OpenAI API key - skipping AI features")
    
    # Run all tests
    tests = [
        test_basic_transcription,
        test_context_correction,
        test_translation,
        test_diarization,
        test_fcpxml_generation,
        test_itt_generation,
        test_markdown_generation,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Generate report
    generate_test_report()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check output above")
    
    print(f"\n📁 All outputs saved to: {BASE_DIR}/test_outputs/")
    print(f"📊 Test report: {BASE_DIR}/test_reports/test_summary.md")


if __name__ == '__main__':
    main()
