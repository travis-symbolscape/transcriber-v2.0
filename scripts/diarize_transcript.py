#!/usr/bin/env python3
"""
Diarization Module

Stage: Add speaker labels to transcripts using pyannote.audio.

Usage:
  python diarize_transcript.py --input-dir "transcripts" --output-dir "diarized" --hf-token YOUR_TOKEN

Features:
- Professional speaker identification using pyannote.audio
- WhisperX alignment for word-level accuracy
- Automatic speaker detection or manual override
- Requires Hugging Face token for pyannote models
"""

import os
import sys
import argparse
import json
import subprocess
import tempfile
from glob import glob
from typing import List, Dict
from pathlib import Path
from datetime import datetime

try:
    import torch
    import torchaudio
    import whisperx
    from pyannote.audio import Pipeline
    from tqdm import tqdm
except ImportError as e:
    print(f"Error: Missing required packages for diarization: {e}")
    print("Install with: pip install pyannote.audio whisperx")
    sys.exit(1)


def find_media_file(json_path: str) -> str:
    """
    Find the corresponding media file for a JSON transcript.
    Searches in common locations relative to the JSON file.
    """
    base_name = Path(json_path).stem
    search_dirs = [
        Path(json_path).parent,  # Same directory as JSON
        Path(json_path).parent.parent / "input",  # ../input
        Path(json_path).parent.parent / "sample_inputs",  # ../sample_inputs
        Path(json_path).parent.parent,  # Parent directory
    ]
    
    media_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.wav', '.mp3', '.m4a', '.flac']
    
    for search_dir in search_dirs:
        if search_dir.exists():
            for ext in media_extensions:
                media_file = search_dir / f"{base_name}{ext}"
                if media_file.exists():
                    return str(media_file)
    
    return None


def convert_to_wav(media_path: str, output_path: str) -> bool:
    """
    Convert media file to mono 16kHz WAV using ffmpeg.
    """
    cmd = [
        "ffmpeg", "-y", "-i", media_path,
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Warning: FFmpeg conversion failed: {e}")
        print("Make sure FFmpeg is installed and accessible")
        return False


def assign_speakers(word_segments: List[Dict], diarization_segments: List[Dict]) -> List[Dict]:
    """
    Assign speaker labels to word segments based on diarization results.
    """
    for word in word_segments:
        word_start = word.get('start', 0)
        # Find which diarization segment contains this word
        assigned_speaker = 'SPEAKER_UNKNOWN'
        for diar_seg in diarization_segments:
            if diar_seg['start'] <= word_start < diar_seg['end']:
                assigned_speaker = diar_seg['speaker']
                break
        word['speaker'] = assigned_speaker
    
    return word_segments


def group_by_speaker(word_segments: List[Dict]) -> List[Dict]:
    """
    Group consecutive words by the same speaker into utterances.
    Returns segments compatible with the original format but with speaker labels.
    """
    if not word_segments:
        return []
    
    grouped_segments = []
    current_speaker = None
    current_text = []
    current_start = None
    current_end = None
    
    for word in word_segments:
        speaker = word.get('speaker', 'SPEAKER_UNKNOWN')
        text = word.get('word', word.get('text', '')).strip()
        start = word.get('start', 0)
        end = word.get('end', 0)
        
        if speaker != current_speaker:
            # Save previous segment if exists
            if current_text and current_speaker:
                grouped_segments.append({
                    'start': current_start,
                    'end': current_end,
                    'text': ' '.join(current_text),
                    'speaker': current_speaker
                })
            
            # Start new segment
            current_speaker = speaker
            current_text = [text] if text else []
            current_start = start
            current_end = end
        else:
            # Continue current segment
            if text:
                current_text.append(text)
            current_end = end
    
    # Add final segment
    if current_text and current_speaker:
        grouped_segments.append({
            'start': current_start,
            'end': current_end,
            'text': ' '.join(current_text),
            'speaker': current_speaker
        })
    
    return grouped_segments


def diarize_transcript(json_path: str, pipeline, align_model, metadata, device: str, num_speakers: int = None) -> List[Dict]:
    """
    Apply speaker diarization to a transcript using pyannote.audio.
    """
    # Load transcript segments
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both formats (list or dict with segments)
    if isinstance(data, list):
        segments = data
    else:
        segments = data.get('segments', [])
    
    if not segments:
        print(f"  → No segments found in {json_path}")
        return []
    
    # Find corresponding media file
    media_path = find_media_file(json_path)
    if not media_path:
        print(f"  → Warning: No media file found for {Path(json_path).name}")
        print(f"  → Using simple speaker detection based on timing gaps")
        return add_simple_speaker_labels(segments)
    
    print(f"  → Found media file: {Path(media_path).name}")
    
    # Convert to WAV for processing
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
        temp_wav_path = temp_wav.name
    
    try:
        if not convert_to_wav(media_path, temp_wav_path):
            print(f"  → Falling back to simple speaker detection")
            return add_simple_speaker_labels(segments)
        
        # Run diarization
        print(f"  → Running speaker diarization...")
        diarization_kwargs = {}
        if num_speakers:
            diarization_kwargs['num_speakers'] = num_speakers
        
        diarization = pipeline(temp_wav_path, **diarization_kwargs)
        
        # Convert diarization to segments
        diar_segments = [
            {
                'start': turn.start,
                'end': turn.end,
                'speaker': speaker
            }
            for turn, _, speaker in diarization.itertracks(yield_label=True)
        ]
        
        print(f"  → Detected {len(set(seg['speaker'] for seg in diar_segments))} speakers")
        
        # Align transcript with audio for word-level timestamps
        print(f"  → Aligning transcript with audio...")
        try:
            aligned_result = whisperx.align(
                segments, align_model, metadata, temp_wav_path, device
            )
            word_segments = aligned_result.get('word_segments', aligned_result.get('segments', []))
        except Exception as e:
            print(f"  → Warning: Alignment failed: {e}")
            print(f"  → Using original segments with speaker assignment")
            # Fallback: assign speakers to original segments
            return assign_speakers_to_segments(segments, diar_segments)
        
        # Assign speakers to words
        word_segments = assign_speakers(word_segments, diar_segments)
        
        # Group words back into segments by speaker
        diarized_segments = group_by_speaker(word_segments)
        
        return diarized_segments
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_wav_path):
            os.unlink(temp_wav_path)


def assign_speakers_to_segments(segments: List[Dict], diar_segments: List[Dict]) -> List[Dict]:
    """
    Fallback method: assign speakers to original segments based on overlap.
    """
    result = []
    
    for segment in segments:
        seg_start = segment.get('start', 0)
        seg_end = segment.get('end', 0)
        
        # Find best matching diarization segment
        best_speaker = 'SPEAKER_UNKNOWN'
        best_overlap = 0
        
        for diar_seg in diar_segments:
            # Calculate overlap
            overlap_start = max(seg_start, diar_seg['start'])
            overlap_end = min(seg_end, diar_seg['end'])
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = diar_seg['speaker']
        
        # Create new segment with speaker label
        new_segment = segment.copy()
        new_segment['speaker'] = best_speaker
        result.append(new_segment)
    
    return result


def add_simple_speaker_labels(segments: List[Dict]) -> List[Dict]:
    """
    Fallback method: Simple speaker detection based on timing gaps.
    """
    diarized_segments = []
    current_speaker = "SPEAKER_00"
    speaker_count = 0
    
    for i, segment in enumerate(segments):
        # Simple heuristic: new speaker after gaps > 2 seconds
        if i > 0:
            gap = segment['start'] - segments[i-1]['end']
            if gap > 2.0:  # 2 second gap suggests speaker change
                speaker_count += 1
                current_speaker = f"SPEAKER_{speaker_count:02d}"
        
        # Add speaker label
        segment_copy = segment.copy()
        segment_copy['speaker'] = current_speaker
        diarized_segments.append(segment_copy)
    
    return diarized_segments

def create_diarization_readme(output_dir: str, method: str, files_processed: int, hf_token_used: bool = False):
    """Create README.md file documenting the diarization process"""
    readme_path = os.path.join(output_dir, "README.md")
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(f"# Speaker Diarization: {method.title()}\n\n")
        f.write(f"This directory contains transcripts with speaker identification applied.\n\n")
        
        f.write(f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Processing:** diarization\n")
        f.write(f"**Method:** {method}\n")
        f.write(f"**Files Processed:** {files_processed}\n")
        if hf_token_used:
            f.write(f"**Model:** pyannote.audio speaker-diarization-3.1\n")
        f.write("\n")
        
        f.write("## Diarization Details\n\n")
        if method == "advanced":
            f.write("**Method:** Advanced AI-based speaker diarization\n\n")
            f.write("**What was applied:**\n")
            f.write("- Professional speaker identification using pyannote.audio\n")
            f.write("- WhisperX alignment for word-level accuracy\n")
            f.write("- Automatic speaker detection and labeling\n")
            f.write("- Audio analysis for voice characteristic differences\n\n")
            
            f.write("**Technical Details:**\n")
            f.write("- **Model:** pyannote.audio speaker-diarization-3.1\n")
            f.write("- **Alignment:** WhisperX for precise word timing\n")
            f.write("- **Quality:** State-of-the-art speaker separation\n")
            f.write("- **Accuracy:** Professional-grade speaker identification\n")
        else:
            f.write("**Method:** Simple timing-based speaker detection\n\n")
            f.write("**What was applied:**\n")
            f.write("- Speaker changes detected based on timing gaps\n")
            f.write("- Automatic speaker labeling (SPEAKER_00, SPEAKER_01, etc.)\n")
            f.write("- Fallback method when advanced models unavailable\n")
            f.write("- Gap threshold: 2+ seconds indicates speaker change\n\n")
            
            f.write("**Technical Details:**\n")
            f.write("- **Method:** Timing gap analysis\n")
            f.write("- **Detection:** 2+ second gaps suggest speaker changes\n")
            f.write("- **Limitations:** Less accurate than AI-based methods\n")
            f.write("- **Best for:** Single speaker or clear speaker transitions\n")
        
        f.write("\n**What was preserved:**\n")
        f.write("- Original timing information (start/end times)\n")
        f.write("- Original transcript text content\n")
        f.write("- Segment structure and organization\n")
        f.write("- All existing metadata\n\n")
        
        f.write("## Speaker Labels\n\n")
        f.write("Speakers are labeled as:\n")
        f.write("- SPEAKER_00: First speaker detected\n")
        f.write("- SPEAKER_01: Second speaker detected\n")
        f.write("- And so on...\n\n")
        f.write("**Note:** Speaker labels are consistent within each file but may vary between files.\n\n")
        
        f.write("## Usage\n\n")
        f.write("These diarized transcripts can be used with:\n")
        f.write("- FCPXML generator for speaker-labeled subtitles\n")
        f.write("- ITT generator for speaker-aware subtitle files\n")
        f.write("- Markdown generator for conversation-style transcripts\n")
        f.write("- Any application expecting transcript JSON with speaker data\n")

def main():
    parser = argparse.ArgumentParser(
        description="Add speaker labels to transcripts using pyannote.audio"
    )
    parser.add_argument('--input-dir', '-i', required=True,
                        help='Directory containing transcript JSON files')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='Directory to save diarized transcripts')
    parser.add_argument('--hf-token', 
                        help='Hugging Face token (or set HUGGINGFACE_TOKEN env var)')
    parser.add_argument('--num-speakers', type=int,
                        help='Expected number of speakers (optional)')
    parser.add_argument('--device', default='auto',
                        help='Device to use: auto, cpu, cuda, mps (default: auto)')
    parser.add_argument('--simple-only', action='store_true',
                        help='Use only simple timing-based speaker detection')
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get Hugging Face token
    hf_token = args.hf_token or os.getenv('HUGGINGFACE_TOKEN')
    
    # Determine device
    if args.device == 'auto':
        if torch.cuda.is_available():
            device = 'cuda'
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = 'mps'
        else:
            device = 'cpu'
    else:
        device = args.device
    
    print(f"Using device: {device}")
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    json_files = glob(os.path.join(args.input_dir, '*.json'))
    
    if not json_files:
        print(f"No JSON files found in {args.input_dir}")
        return
    
    print(f"Found {len(json_files)} transcript file(s)")
    
    # Initialize models if not using simple-only mode
    pipeline = None
    align_model = None
    metadata = None
    
    if not args.simple_only:
        if not hf_token:
            print("Warning: No Hugging Face token provided. Using simple speaker detection.")
            print("To use advanced diarization, provide --hf-token or set HUGGINGFACE_TOKEN environment variable.")
            args.simple_only = True
        else:
            try:
                print("Loading diarization models...")
                
                # Load pyannote diarization pipeline
                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=hf_token
                )
                pipeline.to(torch.device(device))
                
                # Load WhisperX alignment model
                align_model, metadata = whisperx.load_align_model(
                    language_code="en", device=device
                )
                
                print("Models loaded successfully!")
                
            except Exception as e:
                print(f"Error loading models: {e}")
                print("Falling back to simple speaker detection")
                args.simple_only = True
    
    if args.simple_only:
        print("Using simple speaker detection based on timing gaps")
    
    # Create README for this diarization stage
    method = "simple" if args.simple_only else "advanced"
    create_diarization_readme(args.output_dir, method, len(json_files), hf_token is not None)
    
    # Process files
    for json_path in json_files:
        print(f"\nProcessing: {os.path.basename(json_path)}")
        
        try:
            if args.simple_only:
                # Load transcript
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle both formats
                if isinstance(data, list):
                    segments = data
                else:
                    segments = data.get('segments', [])
                
                if not segments:
                    print(f"  → No segments found")
                    continue
                
                # Add simple speaker labels
                diarized_segments = add_simple_speaker_labels(segments)
            else:
                # Use advanced diarization
                diarized_segments = diarize_transcript(
                    json_path, pipeline, align_model, metadata, device, args.num_speakers
                )
                
                if not diarized_segments:
                    print(f"  → No segments produced")
                    continue
            
            # Count speakers
            speakers = set(seg['speaker'] for seg in diarized_segments)
            print(f"  → Detected {len(speakers)} speakers: {', '.join(sorted(speakers))}")
            
            # Save file
            base_name = os.path.splitext(os.path.basename(json_path))[0]
            output_path = os.path.join(args.output_dir, f"{base_name}_diarized.json")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(diarized_segments, f, ensure_ascii=False, indent=2)
            
            print(f"  → Created: {output_path}")
            
        except Exception as e:
            print(f"  → Error processing {os.path.basename(json_path)}: {e}")
            continue
    
    print("\nDiarization complete!")


if __name__ == '__main__':
    main()
