#!/usr/bin/env python3
"""
ITT Generation Module

Stage: Generate ITT subtitle files from JSON transcripts.

Usage:
  python generate_itt.py --input-dir "transcripts" --output-dir "itt"

Features:
- Standard ITT format for wide compatibility
- Video metadata integration for proper timing
"""

import os
import sys
import argparse
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from glob import glob
import subprocess
from typing import List, Dict


def get_video_metadata(video_path):
    """Extract video metadata using ffprobe"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in metadata.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            return None
        
        # Extract properties
        width = int(video_stream.get('width', 1920))
        height = int(video_stream.get('height', 1080))
        avg_frame_rate = video_stream.get('avg_frame_rate', '30/1')
        if avg_frame_rate and '/' in avg_frame_rate:
            num, den = map(int, avg_frame_rate.split('/'))
            fps = num / den
        else:
            fps = 30.0
        duration = float(video_stream.get('duration', 0))
        if duration == 0:
            format_info = metadata.get('format', {})
            duration = float(format_info.get('duration', 0))
        
        return {
            'width': width,
            'height': height,
            'fps': fps,
            'duration': duration
        }
        
    except Exception as e:
        print(f"Warning: Error reading video metadata: {e}")
        return None


def seconds_to_itt_time(seconds, fps=None):
    """Convert seconds to ITT XML timecode format with framerate awareness"""
    adjusted_seconds = seconds
    if fps and abs(fps - 29.97) < 0.1:
        frames = round(seconds * 29.97)
        adjusted_seconds = frames / 29.97
    elif fps and abs(fps - 23.976) < 0.1:
        frames = round(seconds * 23.976)
        adjusted_seconds = frames / 23.976
    
    hours = int(adjusted_seconds // 3600)
    minutes = int((adjusted_seconds % 3600) // 60)
    secs = int(adjusted_seconds % 60)
    milliseconds = int((adjusted_seconds - int(adjusted_seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{milliseconds:03}"


def find_video_file(json_path):
    """Find the corresponding video file for a transcript"""
    base_name = os.path.splitext(os.path.basename(json_path))[0]
    base_name = base_name.replace('_corrected', '').replace('_translated', '').replace('_traditional_mandarin', '')
    
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4v']
    
    # Search directories
    search_dirs = [
        os.path.dirname(json_path),
        os.path.dirname(os.path.dirname(json_path)),
        os.path.join(os.path.dirname(os.path.dirname(json_path)), 'sample_inputs')
    ]
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for ext in video_extensions:
                video_path = os.path.join(search_dir, base_name + ext)
                if os.path.exists(video_path):
                    return video_path
    
    return None


def convert_to_itt(segments: List[Dict], output_path: str, fps=None):
    """Convert segments to ITT subtitles and save to file"""
    root = ET.Element('tt', xmlns="http://www.w3.org/ns/ttml")
    body = ET.SubElement(root, 'body')
    div = ET.SubElement(body, 'div')
    
    for i, segment in enumerate(segments):
        begin = seconds_to_itt_time(segment['start'], fps)
        end = seconds_to_itt_time(segment['end'], fps)
        p = ET.SubElement(div, 'p', begin=begin, end=end)
        p.text = segment['text'].strip()
    
    # Convert to pretty XML
    rough_string = ET.tostring(root, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    itt_content = '\n'.join(lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(itt_content)


def main():
    parser = argparse.ArgumentParser(
        description="Generate ITT subtitle files from JSON transcripts"
    )
    parser.add_argument('--input-dir', '-i', required=True,
                        help='Directory containing transcript JSON files')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='Directory for ITT output files')
    
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    
    json_files = glob(os.path.join(args.input_dir, '*.json'))
    
    if not json_files:
        print(f"No JSON files found in {args.input_dir}")
        return
    
    print(f"Found {len(json_files)} transcript file(s)")
    
    for json_path in json_files:
        print(f"Processing: {os.path.basename(json_path)}")
        with open(json_path, 'r', encoding='utf-8') as f:
            segments = json.load(f)
        
        video_file = find_video_file(json_path)
        video_metadata = None
        if video_file:
            print(f"  → Found video: {os.path.basename(video_file)}")
            video_metadata = get_video_metadata(video_file)
        
        output_path = os.path.join(args.output_dir, os.path.basename(json_path).replace('.json', '.itt'))
        convert_to_itt(segments, output_path, fps=video_metadata['fps'] if video_metadata else None)
        
        print(f"  → Created: {output_path}")


if __name__ == '__main__':
    main()
