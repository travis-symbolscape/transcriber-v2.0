#!/usr/bin/env python3
"""
Transcription Module

Stage 1: Transcribe media files to JSON using Whisper.

Usage:
  python transcribe.py --input-dir "input" --output-dir "output" --model base

Features:
- Local Whisper model transcription
- JSON output with timestamped segments
- Handles multiple media formats
"""

import os
import sys
import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from glob import glob
from tqdm import tqdm
import torchaudio

try:
    import whisper
except ImportError:
    print("Error: install openai-whisper (`pip install openai-whisper`)", file=sys.stderr)
    sys.exit(1)


def preprocess_audio(video_path, temp_dir, enhancement_level="standard"):
    """
    Preprocess audio from video file using comprehensive FFmpeg filters
    Returns path to processed audio file or None if failed
    
    enhancement_level options:
    - "minimal": Basic cleanup only
    - "standard": Good balance of enhancement vs artifacts
    - "aggressive": Maximum enhancement for difficult audio
    """
    video_name = Path(video_path).stem
    processed_audio_path = os.path.join(temp_dir, f"{video_name}_processed.wav")
    
    print(f"  → Preprocessing audio: {os.path.basename(video_path)} ({enhancement_level} enhancement)")
    
    # Define filter chains based on enhancement level
    if enhancement_level == "minimal":
        # Basic cleanup only
        audio_filter = (
            "highpass=f=80,"
            "lowpass=f=8000,"
            "loudnorm=I=-16:TP=-1.5:LRA=11"
        )
    elif enhancement_level == "aggressive":
        # Maximum enhancement for difficult audio
        audio_filter = (
            "highpass=f=80,"
            "lowpass=f=8000,"
            "afftdn=nf=-25,"
            "dynaudnorm=f=75:g=25:p=0.95:m=10:r=0.9:n=1:c=1,"
            "compand=attacks=0.3:decays=1.5:points=-80/-80|-45/-15|-27/-9|-5/-5|0/-3|20/-3,"
            "equalizer=f=3000:t=h:w=500:g=2,"
            "loudnorm=I=-16:TP=-1.5:LRA=11"
        )
    else:  # "standard"
        # Balanced enhancement - good for most audio
        audio_filter = (
            "highpass=f=80,"
            "lowpass=f=8000,"
            "afftdn=nf=-20,"
            "dynaudnorm=f=75:g=15:p=0.95:m=10:r=0.9:n=1:c=1,"
            "equalizer=f=3000:t=h:w=500:g=1,"
            "loudnorm=I=-16:TP=-1.5:LRA=11"
        )
    
    # FFmpeg command with comprehensive audio enhancement
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-af', audio_filter,
        '-ar', '16000',  # Resample to 16kHz (optimal for Whisper)
        '-ac', '1',      # Convert to mono for better processing
        '-acodec', 'pcm_s16le',  # Uncompressed audio for best quality
        '-y',  # Overwrite output file
        processed_audio_path
    ]
    
    try:
        # Run FFmpeg with suppressed output
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return processed_audio_path
    except subprocess.CalledProcessError:
        print(f"  → Warning: Audio preprocessing failed for {os.path.basename(video_path)}")
        print(f"  → Using original file (make sure FFmpeg is installed)")
        return None
    except FileNotFoundError:
        print(f"  → Warning: FFmpeg not found. Install FFmpeg for audio preprocessing.")
        print(f"  → Using original file")
        return None


def transcribe_with_local(model, input_path, output_json_path, initial_prompt=None, use_preprocessing=False, enhancement_level="standard"):
    """
    Transcribe audio/video file with optional preprocessing
    """
    transcribe_path = input_path
    temp_dir = None
    
    # Apply preprocessing if requested
    if use_preprocessing:
        temp_dir = tempfile.mkdtemp()
        processed_path = preprocess_audio(input_path, temp_dir, enhancement_level)
        if processed_path:
            transcribe_path = processed_path
    
    # Transcribe the audio
    transcribe_params = {}
    if initial_prompt:
        transcribe_params["initial_prompt"] = initial_prompt
    
    result = model.transcribe(transcribe_path, **transcribe_params)
    segments = result.get("segments", [])
    
    # Save results
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
    
    # Cleanup temporary files
    if temp_dir and os.path.exists(temp_dir):
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception:
            pass  # Ignore cleanup errors



def find_media_files(input_dir, recursive=False):
    patterns = ['*.mp4', '*.wav', '*.m4a', '*.flac', '*.mp3']
    files = []
    if recursive:
        for root, _, _ in os.walk(input_dir):
            for pat in patterns:
                files.extend(glob(os.path.join(root, pat)))
    else:
        for pat in patterns:
            files.extend(glob(os.path.join(input_dir, pat)))
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe media to JSON using Whisper."
    )
    parser.add_argument('--input-dir', '-i', required=True,
                        help='Directory containing media files')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='Directory to save JSON transcripts')
    parser.add_argument('--model', '-m', default='base',
                        help='Whisper model to use: tiny, base, small, medium, large')
    parser.add_argument('--recursive', '-r', action='store_true',
                        help='Recurse into subdirectories')
    parser.add_argument('--preprocessing', action='store_true',
                        help='Apply audio preprocessing (noise reduction, resampling)')
    parser.add_argument('--enhancement-level', choices=['minimal', 'standard', 'aggressive'], 
                        default='standard',
                        help='Audio enhancement level (minimal/standard/aggressive)')
    parser.add_argument('--initial-prompt',
                        help='Initial prompt to guide Whisper transcription')
    args = parser.parse_args()

    # Load Whisper model
    print(f"Loading Whisper model: {args.model}")
    model = whisper.load_model(args.model)

    # Find media files
    media_files = find_media_files(args.input_dir, recursive=args.recursive)
    print(f"Found {len(media_files)} media files to transcribe.")
    
    if args.preprocessing:
        print("Audio preprocessing enabled (noise reduction + 16kHz resampling)")
    
    if not media_files:
        print("No files to transcribe.")
        return

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Transcribe each file
    for path in tqdm(media_files, desc="Transcribing", unit="file"):
        stem = os.path.splitext(os.path.basename(path))[0]
        out_json = os.path.join(args.output_dir, f"{stem}.json")
        
        # Skip if output already exists
        if os.path.exists(out_json):
            print(f"Skipping {stem} (output already exists)")
            continue
        
        transcribe_with_local(
            model, 
            path, 
            out_json, 
            initial_prompt=args.initial_prompt,
            use_preprocessing=args.preprocessing,
            enhancement_level=args.enhancement_level
        )


if __name__ == '__main__':
    main()
