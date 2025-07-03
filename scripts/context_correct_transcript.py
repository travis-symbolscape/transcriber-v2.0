#!/usr/bin/env python3
"""
Transcript Cleanup Module

Stage 2: Apply AI cleanup to transcripts with configurable levels.

Usage:
  python context_correct_transcript.py --input-dir "transcripts" --output-dir "cleaned" --api-key "key" --cleanup-level standard

Features:
- Multiple cleanup levels: minimal, standard, aggressive, custom
- AI-powered homophone and grammar correction
- Configurable filler word removal
- Custom cleanup instructions support
- Preserves timing information
"""

import os
import sys
import json
import argparse
import time
from glob import glob
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import openai
except ImportError:
    print("Error: install openai (`pip install openai`)", file=sys.stderr)
    sys.exit(1)


def get_cleanup_prompt(cleanup_level: str, custom_prompt: str = None) -> str:
    """Get the appropriate cleanup prompt based on level."""
    
    if cleanup_level == "custom" and custom_prompt:
        return f"""You are a transcript cleanup assistant. Follow these specific instructions:

{custom_prompt}

Always preserve timing information and return only the cleaned text with no explanations."""
    
    prompts = {
        "minimal": """You are a transcript correction assistant. Fix only obvious transcription errors while preserving authentic speech.

WHAT TO FIX:
- Clear homophone errors: there/their/they're, your/you're, its/it's, to/too/two, bees/these, etc.
- Obvious word misrecognitions where context makes the intended word clear
- Basic contraction errors (cant/can't, wont/won't)

WHAT TO PRESERVE:
- All filler words ("um", "uh", "like")
- Informal grammar and casual speech patterns
- Speaker's exact style, pace, and personality
- Repetitions, false starts, and natural speech disfluencies

NEVER add words, topics, or information not in the original speech.

Return ONLY the corrected text with no explanations.""",
        
        "standard": """You are a transcript cleanup assistant. Improve readability while preserving the speaker's authentic voice and meaning.

WHAT TO FIX:
- Homophone and grammar errors (there/their, your/you're, etc.)
- Word misrecognitions where context clearly indicates the intended word
- Basic punctuation and capitalization
- Some excessive filler words ("um", "uh") but preserve some for natural flow

WHAT TO PRESERVE:
- Speaker's intended meaning and core message
- Informal language and personal speaking style
- Meaningful uses of "like", "you know", etc.
- The speaker's level of formality and personality

NEVER:
- Add topics, facts, or details not mentioned by the speaker
- Change the speaker's intended meaning or opinions
- Make assumptions about what they "meant to say"

Return ONLY the cleaned text with no explanations.""",
        
        "aggressive": """You are a transcript cleanup assistant. Create a polished, publication-ready transcript while preserving the speaker's core message.

WHAT TO ENHANCE:
- Fix all grammar, punctuation, and word recognition errors
- Remove most filler words and speech disfluencies
- Improve sentence structure and flow for readability
- Fix run-on sentences and sentence fragments
- Standardize formatting and capitalization

WHAT TO PRESERVE:
- The speaker's actual ideas, opinions, and key points
- Technical terms, names, and specific details mentioned
- The logical flow and structure of their argument
- Their level of expertise and knowledge demonstrated

NEVER:
- Add information, examples, or details the speaker didn't provide
- Change their conclusions, opinions, or factual claims
- Assume knowledge or context beyond what was spoken
- Insert explanations or clarifications not in the original

Return ONLY the enhanced text with no explanations."""
    }
    
    return prompts.get(cleanup_level, prompts["standard"])

def apply_transcript_cleanup(segments: List[Dict], api_key: str, cleanup_level: str = "standard", custom_prompt: str = None, language: str = "en") -> List[Dict]:
    """Apply AI cleanup to transcript segments based on specified level."""
    client = openai.OpenAI(api_key=api_key)
    
    # Skip AI cleanup for translated content to avoid retranslation
    sample_text = " ".join([seg.get('text', '').strip() for seg in segments[:3]])
    
    # Simple heuristic: if we have mostly non-ASCII characters, likely translated
    non_ascii_ratio = sum(1 for c in sample_text if ord(c) > 127) / max(len(sample_text), 1)
    
    if non_ascii_ratio > 0.3 or language != "en":
        print(f"  → Skipping AI cleanup for translated content (language: {language})")
        return segments
    
    print(f"  → Applying {cleanup_level} level cleanup")
    if custom_prompt:
        print(f"  → Using custom instructions")
    
    # Get appropriate cleanup prompt
    system_prompt = get_cleanup_prompt(cleanup_level, custom_prompt)
    
    # Group segments into chunks for efficient processing
    chunk_size = 10
    cleaned_segments = []
    
    for i in range(0, len(segments), chunk_size):
        chunk = segments[i:i + chunk_size]
        
        # Extract text from chunk
        texts = [seg.get('text', '').strip() for seg in chunk]
        if not any(texts):
            cleaned_segments.extend(chunk)
            continue
        
        # Create context for AI
        combined_text = " ".join(texts)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": f"Clean up this transcript segment:\n\n{combined_text}"
                    }
                ],
                temperature=0.1,
                max_tokens=len(combined_text.split()) * 2
            )
            
            cleaned_text = response.choices[0].message.content.strip()
            
            # Split cleaned text back into individual segments
            cleaned_words = cleaned_text.split()
            original_words = combined_text.split()
            
            # Apply corrections back to individual segments
            word_index = 0
            for j, seg in enumerate(chunk):
                original_seg_text = seg.get('text', '').strip()
                if not original_seg_text:
                    cleaned_segments.append(seg)
                    continue
                
                seg_word_count = len(original_seg_text.split())
                
                # Extract corresponding cleaned words
                if word_index + seg_word_count <= len(cleaned_words):
                    cleaned_seg_text = " ".join(cleaned_words[word_index:word_index + seg_word_count])
                else:
                    # Fallback to original if mismatch
                    cleaned_seg_text = original_seg_text
                
                # Create cleaned segment
                cleaned_seg = seg.copy()
                cleaned_seg['text'] = cleaned_seg_text
                cleaned_segments.append(cleaned_seg)
                
                word_index += seg_word_count
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Warning: AI cleanup failed for chunk {i//chunk_size + 1}: {e}")
            print("Using original text for this chunk.")
            cleaned_segments.extend(chunk)
            continue
    
    return cleaned_segments

def create_cleanup_readme(output_dir: str, cleanup_level: str, custom_prompt: str = None, files_processed: int = 0):
    """Create README.md file documenting the cleanup process"""
    readme_path = os.path.join(output_dir, "README.md")
    
    cleanup_descriptions = {
        'minimal': 'Minimal cleanup - Fix obvious homophone and grammar errors only',
        'standard': 'Standard cleanup - Light cleanup with some filler word removal',
        'aggressive': 'Aggressive cleanup - Comprehensive cleanup for maximum readability',
        'custom': f'Custom cleanup - {custom_prompt}' if custom_prompt else 'Custom cleanup instructions'
    }
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(f"# AI Transcript Cleanup: {cleanup_level.title()}\n\n")
        f.write(f"This directory contains AI-enhanced transcripts processed using {cleanup_level} cleanup level.\n\n")
        
        f.write(f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Processing:** cleanup\n")
        f.write(f"**Cleanup Level:** {cleanup_level}\n")
        if custom_prompt:
            f.write(f"**Custom Instructions:** {custom_prompt}\n")
        f.write(f"**Files Processed:** {files_processed}\n\n")
        
        f.write("## Cleanup Details\n\n")
        f.write(f"**Description:** {cleanup_descriptions.get(cleanup_level, 'Custom cleanup')}\n\n")
        f.write("**What was enhanced:**\n")
        
        if cleanup_level == 'minimal':
            f.write("- Fixed obvious homophone errors (there/their, your/you're, etc.)\n")
            f.write("- Corrected basic grammar mistakes\n")
            f.write("- Preserved all filler words and informal speech\n")
            f.write("- Maintained speaker's exact style and tone\n")
        elif cleanup_level == 'standard':
            f.write("- Fixed homophone and grammar errors\n")
            f.write("- Removed some filler words (um, uh) while preserving authenticity\n")
            f.write("- Improved basic punctuation and capitalization\n")
            f.write("- Preserved informal language and speaking style\n")
        elif cleanup_level == 'aggressive':
            f.write("- Fixed all grammar, punctuation, and homophone errors\n")
            f.write("- Removed most filler words and speech disfluencies\n")
            f.write("- Improved sentence structure for readability\n")
            f.write("- Enhanced text for publication-ready quality\n")
        elif cleanup_level == 'custom':
            f.write(f"- Applied custom instructions: {custom_prompt}\n")
        
        f.write("\n**What was preserved:**\n")
        f.write("- Original timing information (start/end times)\n")
        f.write("- Speaker's core message and meaning\n")
        f.write("- Segment structure and organization\n")
        f.write("- Speaker identification (if present)\n\n")
        
        f.write("## Technical Details\n\n")
        f.write("- **AI Model:** OpenAI GPT-4\n")
        f.write("- **Processing:** Contextual cleanup with semantic preservation\n")
        f.write("- **Quality:** Professional-grade transcript enhancement\n")
        f.write("- **Language Support:** Optimized for English content\n\n")
        
        f.write("## Usage\n\n")
        f.write("These enhanced transcripts can be used with:\n")
        f.write("- FCPXML generator for Final Cut Pro subtitles\n")
        f.write("- ITT generator for standard subtitle files\n")
        f.write("- Markdown generator for readable transcripts\n")
        f.write("- Translation scripts for multilingual content\n")
        f.write("- Any application expecting transcript JSON format\n")

def main():
    parser = argparse.ArgumentParser(
        description="Apply AI cleanup to transcripts with configurable levels."
    )
    parser.add_argument('--input-dir', '-i', required=True,
                        help='Directory containing JSON transcripts')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='Directory to save cleaned transcripts')
    parser.add_argument('--api-key', required=True,
                        help='OpenAI API key')
    parser.add_argument('--cleanup-level', choices=['minimal', 'standard', 'aggressive', 'custom'], 
                        default='standard', help='Level of cleanup to apply')
    parser.add_argument('--custom-cleanup-prompt', '--custom-prompt', help='Custom cleanup instructions (for custom level)')
    parser.add_argument('--language', default='en',
                        help='Language code (skip cleanup for non-English)')
    args = parser.parse_args()

    # Validate custom level requirements
    if args.cleanup_level == 'custom' and not args.custom_cleanup_prompt:
        print("Error: --custom-cleanup-prompt is required when using --cleanup-level custom")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    
    json_files = glob(os.path.join(args.input_dir, "*.json"))
    print(f"Found {len(json_files)} transcript files to clean.")
    print(f"Cleanup level: {args.cleanup_level}")
    if args.custom_cleanup_prompt:
        print(f"Custom instructions: {args.custom_cleanup_prompt}")
    print()
    
    # Create README for this cleanup stage
    create_cleanup_readme(args.output_dir, args.cleanup_level, args.custom_cleanup_prompt, len(json_files))

    for json_file in json_files:
        print(f"Processing: {os.path.basename(json_file)}")
        
        with open(json_file, 'r') as f:
            segments = json.load(f)
        
        cleaned_segments = apply_transcript_cleanup(
            segments, 
            args.api_key, 
            args.cleanup_level, 
            args.custom_cleanup_prompt,
            args.language
        )
        
        stem = os.path.splitext(os.path.basename(json_file))[0]
        output_file = os.path.join(args.output_dir, f"{stem}_cleaned.json")
        
        with open(output_file, 'w') as f:
            json.dump(cleaned_segments, f, ensure_ascii=False, indent=2)
        
        print(f"  → Saved: {output_file}")


if __name__ == '__main__':
    main()
