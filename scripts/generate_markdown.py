#!/usr/bin/env python3
"""
Markdown Generation Module

Stage: Generate readable Markdown transcripts from JSON.

Usage:
  python generate_markdown.py --input-dir "transcripts" --output-dir "markdown" --include-timecodes --include-speakers

Features:
- Flexible formatting options
- Speaker identification support
- Optional timecode inclusion
"""

import os
import sys
import argparse
import json
from glob import glob
from typing import List, Dict


def format_timecode(seconds):
    """Convert seconds to readable timecode format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02}:{minutes:02}:{secs:02}"
    else:
        return f"{minutes:02}:{secs:02}"


def has_speaker_info(segments):
    """Check if segments contain speaker information"""
    return any('speaker' in seg for seg in segments)


def generate_markdown(segments: List[Dict], include_timecodes=True, include_speakers=True, title="Transcript"):
    """Generate markdown content from transcript segments"""
    
    # Check if speaker info is available
    speaker_available = has_speaker_info(segments) and include_speakers
    
    lines = [f"# {title}\n"]
    
    # Add metadata section
    if segments:
        duration = max(seg.get('end', 0) for seg in segments)
        lines.append(f"**Duration:** {format_timecode(duration)}")
        lines.append(f"**Segments:** {len(segments)}")
        if speaker_available:
            speakers = set(seg.get('speaker', 'Unknown') for seg in segments if 'speaker' in seg)
            lines.append(f"**Speakers:** {len(speakers)}")
        lines.append("")
    
    # Add transcript content
    for segment in segments:
        text = segment.get('text', '').strip()
        if not text:
            continue
        
        # Build line parts
        line_parts = []
        
        # Add timecode if requested
        if include_timecodes:
            timecode = format_timecode(segment.get('start', 0))
            line_parts.append(f"**{timecode}**")
        
        # Add speaker if available and requested
        if speaker_available and 'speaker' in segment:
            speaker = segment['speaker']
            line_parts.append(f"**{speaker}**")
        
        # Combine parts and add text
        if line_parts:
            prefix = " ".join(line_parts) + ": "
        else:
            prefix = ""
        
        lines.append(f"{prefix}{text}")
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Markdown transcripts from JSON files"
    )
    parser.add_argument('--input-dir', '-i', required=True,
                        help='Directory containing transcript JSON files')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='Directory for Markdown output files')
    parser.add_argument('--include-timecodes', action='store_true',
                        help='Include timecodes in output')
    parser.add_argument('--include-speakers', action='store_true',
                        help='Include speaker names in output (if available)')
    parser.add_argument('--title',
                        help='Custom title for transcripts')
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    json_files = glob(os.path.join(args.input_dir, '*.json'))
    
    if not json_files:
        print(f"No JSON files found in {args.input_dir}")
        return
    
    print(f"Found {len(json_files)} transcript file(s)")
    print(f"Options: timecodes={args.include_timecodes}, speakers={args.include_speakers}")
    
    for json_path in json_files:
        print(f"Processing: {os.path.basename(json_path)}")
        
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
        
        # Generate title
        base_name = os.path.splitext(os.path.basename(json_path))[0]
        title = args.title or f"{base_name} Transcript"
        
        # Check for speaker info
        speaker_available = has_speaker_info(segments)
        if args.include_speakers and not speaker_available:
            print(f"  → No speaker information found")
        elif speaker_available:
            print(f"  → Speaker information detected")
        
        # Generate markdown
        markdown_content = generate_markdown(
            segments, 
            include_timecodes=args.include_timecodes,
            include_speakers=args.include_speakers and speaker_available,
            title=title
        )
        
        # Save file
        output_path = os.path.join(args.output_dir, f"{base_name}.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"  → Created: {output_path}")


if __name__ == '__main__':
    main()
