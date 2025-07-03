#!/usr/bin/env python3
"""
FCPXML Generation Module

Stage: Generate FCPXML subtitle files from JSON transcripts.

Usage:
  python generate_fcpxml.py --input-dir "transcripts" --output-dir "fcpxml"

Features:
- Professional FCPXML format for Final Cut Pro
- Video metadata integration for proper timing
- Text wrapping for optimal subtitle display
"""

import os
import sys
import argparse
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from glob import glob
import subprocess
from typing import List, Dict, Any


def merge_segments_by_timing(segments, max_duration=5.0, max_chars=60):
    """Merge transcript segments into subtitle-appropriate chunks."""
    if not segments:
        return []
    
    merged = []
    current_group = []
    current_start = segments[0]['start']
    current_text = ""
    
    for segment in segments:
        segment_text = segment.get('text', '').strip()
        if not segment_text:
            continue
            
        new_text = (current_text + " " + segment_text).strip()
        duration = segment['end'] - current_start
        
        if (len(new_text) > max_chars or 
            duration > max_duration) and current_text:
            merged.append({
                'start': current_start,
                'end': current_group[-1]['end'],
                'text': current_text
            })
            current_group = [segment]
            current_start = segment['start']
            current_text = segment_text
        else:
            current_group.append(segment)
            current_text = new_text
    
    if current_text and current_group:
        merged.append({
            'start': current_start,
            'end': current_group[-1]['end'],
            'text': current_text
        })
    
    return merged


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
        
        # Extract key properties
        width = int(video_stream.get('width', 1920))
        height = int(video_stream.get('height', 1080))
        
        # Parse frame rate
        avg_frame_rate = video_stream.get('avg_frame_rate', '30/1')
        if avg_frame_rate and '/' in avg_frame_rate:
            num, den = map(int, avg_frame_rate.split('/'))
            fps = num / den
        else:
            fps = 30.0
        
        # Get duration
        duration = float(video_stream.get('duration', 0))
        if duration == 0:
            format_info = metadata.get('format', {})
            duration = float(format_info.get('duration', 0))
        
        # Determine format settings
        format_name, frame_duration, timebase = get_fcp_format_settings(width, height, fps)
        
        return {
            'width': width,
            'height': height,
            'fps': fps,
            'duration': duration,
            'format_name': format_name,
            'frame_duration': frame_duration,
            'timebase': timebase
        }
        
    except Exception as e:
        print(f"Warning: Error reading video metadata: {e}")
        return None


def get_fcp_format_settings(width, height, fps):
    """Get Final Cut Pro format settings based on video properties"""
    
    if width == 1920 and height == 1080:
        if abs(fps - 29.97) < 0.1:
            return "FFVideoFormat1080p2997", "1001/30000", 30000
        elif abs(fps - 30.0) < 0.1:
            return "FFVideoFormat1080p30", "1/30", 30
        elif abs(fps - 25.0) < 0.1:
            return "FFVideoFormat1080p25", "1/25", 25
        elif abs(fps - 24.0) < 0.1:
            return "FFVideoFormat1080p24", "1/24", 24
    
    # Default fallback
    return "FFVideoFormat1080p2997", "1001/30000", 30000


def seconds_to_rational_time(seconds, frame_duration="1001/30000", timebase=30000):
    """Convert seconds to Final Cut Pro rational time format"""
    
    if frame_duration == "1001/30000":
        frames = round(seconds * 30000 / 1001)
        return f"{frames * 1001}/30000s"
    else:
        rational_value = int(round(seconds * timebase))
        return f"{rational_value}/{timebase}s"


def wrap_text_for_subtitles(text, max_chars_per_line=35):
    """Wrap text to multiple lines for better subtitle formatting."""
    import textwrap
    
    # Split into sentences first
    sentences = text.replace('.', '. ').replace('?', '? ').replace('!', '! ').split()
    
    # Rejoin and wrap
    rejoined = ' '.join(sentences)
    wrapped_lines = textwrap.fill(rejoined, width=max_chars_per_line).split('\n')
    
    # Limit to 2 lines
    if len(wrapped_lines) > 2:
        wrapped_lines = textwrap.fill(rejoined, width=max_chars_per_line + 10).split('\n')
        if len(wrapped_lines) > 2:
            wrapped_lines = wrapped_lines[:2]
            wrapped_lines[1] = wrapped_lines[1][:max_chars_per_line-3] + "..."
    
    return '\n'.join(wrapped_lines)


def create_fcpxml_content(segments, project_name="Subtitles", video_metadata=None):
    """Create FCPXML content with proper structure for Final Cut Pro"""
    
    merged_segments = merge_segments_by_timing(segments)
    
    if not merged_segments:
        raise ValueError("No segments to process")
    
    # Use video metadata if available
    if video_metadata:
        format_name = video_metadata['format_name']
        frame_duration = video_metadata['frame_duration']
        timebase = video_metadata['timebase']
        width = video_metadata['width']
        height = video_metadata['height']
        video_duration = video_metadata['duration']
    else:
        format_name = "FFVideoFormat1080p2997"
        frame_duration = "1001/30000"
        timebase = 30000
        width = 1920
        height = 1080
        video_duration = max(seg['end'] for seg in merged_segments)
    
    # Calculate total duration
    subtitle_duration = max(seg['end'] for seg in merged_segments)
    total_duration = max(video_duration, subtitle_duration)
    total_duration_rational = seconds_to_rational_time(total_duration, frame_duration, timebase)
    
    # Create FCPXML structure
    fcpxml = ET.Element("fcpxml", version="1.8")
    
    # Resources
    resources = ET.SubElement(fcpxml, "resources")
    
    # Format
    format_elem = ET.SubElement(resources, "format",
                               id="r1",
                               name=format_name,
                               frameDuration=frame_duration,
                               width=str(width),
                               height=str(height))
    
    # Effect resource for titles
    effect = ET.SubElement(resources, "effect",
                          id="r2",
                          name="Custom",
                          uid=".../Titles.localized/Build In:Out.localized/Custom.localized/Custom.moti")
    
    # Library
    library = ET.SubElement(fcpxml, "library", location="")
    
    # Event
    event = ET.SubElement(library, "event", name="Subtitle Event")
    
    # Project
    project = ET.SubElement(event, "project", name=project_name)
    
    # Sequence
    sequence = ET.SubElement(project, "sequence",
                           duration=total_duration_rational,
                           format="r1",
                           tcStart="0/1s",
                           tcFormat="NDF",
                           audioLayout="stereo",
                           audioRate="48k")
    
    # Spine
    spine = ET.SubElement(sequence, "spine")
    
    # Gap
    gap = ET.SubElement(spine, "gap",
                       name="Gap",
                       offset="0/1s",
                       duration=total_duration_rational,
                       start="0/1s")
    
    # Add title elements for each subtitle
    for i, segment in enumerate(merged_segments):
        start_time = seconds_to_rational_time(segment['start'], frame_duration, timebase)
        duration_time = seconds_to_rational_time(segment['end'] - segment['start'], frame_duration, timebase)
        
        # Clean and wrap text
        text = segment['text'].strip()
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        wrapped_text = wrap_text_for_subtitles(text)
        
        # Create title element
        title = ET.SubElement(gap, "title",
                            ref="r2",
                            name=f"Title {i+1}",
                            lane="1",
                            offset=start_time,
                            duration=duration_time,
                            start="0/1s")
        
        # Add text element
        text_elem = ET.SubElement(title, "text")
        text_elem.text = wrapped_text
    
    # Convert to pretty XML
    rough_string = ET.tostring(fcpxml, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Clean up XML formatting
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    return '\n'.join(lines)


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


def main():
    parser = argparse.ArgumentParser(
        description="Generate FCPXML subtitle files from JSON transcripts"
    )
    parser.add_argument('--input-dir', '-i', required=True,
                        help='Directory containing transcript JSON files')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='Directory for FCPXML output files')
    parser.add_argument('--project-name',
                        help='Project name for FCPXML (auto-generated if not provided)')
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    json_files = glob(os.path.join(args.input_dir, '*.json'))
    
    if not json_files:
        print(f"No JSON files found in {args.input_dir}")
        return
    
    print(f"Found {len(json_files)} transcript file(s)")
    print("Generating FCPXML files...\n")
    
    for json_path in json_files:
        print(f"Processing: {os.path.basename(json_path)}")
        
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
        
        print(f"  → Loaded {len(segments)} segments")
        
        # Find video file and get metadata
        video_file = find_video_file(json_path)
        video_metadata = None
        
        if video_file:
            print(f"  → Found video: {os.path.basename(video_file)}")
            video_metadata = get_video_metadata(video_file)
        else:
            print(f"  → No video file found, using defaults")
        
        # Generate project name
        filename = os.path.basename(json_path)
        base_name = os.path.splitext(filename)[0]
        project_name = args.project_name or f"{base_name} Subtitles"
        
        # Create FCPXML
        fcpxml_content = create_fcpxml_content(segments, project_name, video_metadata)
        
        # Save file
        output_path = os.path.join(args.output_dir, f"{base_name}.fcpxml")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(fcpxml_content)
        
        print(f"  → Created: {output_path}")
        print()


if __name__ == '__main__':
    main()
