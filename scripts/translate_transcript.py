#!/usr/bin/env python3
"""
translate_transcript.py

Translate transcript JSON files to different languages using OpenAI API.
Preserves timing data while translating text content.

Usage:
  python scripts/translate_transcript.py \
    --transcript-dir "/path/to/transcripts" \
    --output-dir "/path/to/translated" \
    --target-language "Spanish" \
    --api-key "$OPENAI_API_KEY"

Features:
- Translates JSON transcript files while preserving timing
- Supports batch processing of multiple files
- Maintains original transcript structure
- Optimized chunking for API efficiency
- Error handling and fallback mechanisms
"""

import os
import sys
import json
import argparse
import time
from glob import glob
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from datetime import datetime

try:
    import openai
except ImportError:
    print("Error: install openai (`pip install openai`)", file=sys.stderr)
    sys.exit(1)

# Language mapping for better translation prompts
LANGUAGE_NAMES = {
    'es': 'Spanish',
    'fr': 'French', 
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'zh': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'ja': 'Japanese',
    'ko': 'Korean',
    'ru': 'Russian',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'nl': 'Dutch',
    'sv': 'Swedish',
    'no': 'Norwegian',
    'da': 'Danish',
    'fi': 'Finnish',
    'pl': 'Polish',
    'tr': 'Turkish',
    'he': 'Hebrew',
    'th': 'Thai',
    'vi': 'Vietnamese'
}

def get_language_name(code: str) -> str:
    """Get full language name from code, with fallback"""
    return LANGUAGE_NAMES.get(code.lower(), code.title())

def create_translation_prompt(target_language: str, source_language: str = "English") -> str:
    """Create optimized translation prompt for OpenAI"""
    return f"""You are a professional translator. Translate the following {source_language} text to {target_language}.

REQUIREMENTS:
1. Maintain the meaning and tone of the original text
2. Use natural, fluent {target_language} that sounds native
3. Preserve any technical terms appropriately
4. Keep punctuation and formatting consistent
5. Do NOT add explanations or notes - provide ONLY the translation
6. If translating speech, maintain conversational tone
7. For unclear segments, provide the best natural translation

Translate this text to {target_language}:"""

def translate_text_chunk(texts: List[str], target_language: str, api_key: str, 
                        source_language: str = "English") -> List[str]:
    """Translate a batch of text segments using OpenAI API"""
    client = openai.OpenAI(api_key=api_key)
    
    # Combine texts for efficient batch translation
    combined_text = "\n---SEGMENT---\n".join(texts)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": create_translation_prompt(target_language, source_language)
                },
                {
                    "role": "user", 
                    "content": combined_text
                }
            ],
            temperature=0.3,  # Low temperature for consistent translations
            max_tokens=len(combined_text.split()) * 2  # Allow for language expansion
        )
        
        translated_text = response.choices[0].message.content.strip()
        
        # Split back into individual segments
        # Try multiple possible separators (AI might translate the separator)
        possible_separators = [
            "\n---SEGMENT---\n",
            "\n---SEGMENTO---\n",  # Spanish
            "\n---SEGMENT---\n",
            "---SEGMENT---",
            "---SEGMENTO---"
        ]
        
        translated_segments = [translated_text]  # Start with full text
        for separator in possible_separators:
            if separator in translated_text:
                translated_segments = translated_text.split(separator)
                break
        
        # Clean up any remaining separators from segments
        translated_segments = [seg.strip().replace("---SEGMENT---", "").replace("---SEGMENTO---", "") for seg in translated_segments]
        
        # Ensure we have the same number of segments
        if len(translated_segments) != len(texts):
            print(f"Warning: Translation segment count mismatch. Expected {len(texts)}, got {len(translated_segments)}")
            print(f"Original texts: {texts}")
            print(f"Translated segments: {translated_segments}")
            # Fallback: if we have fewer segments, pad with originals
            if len(translated_segments) < len(texts):
                for i in range(len(translated_segments), len(texts)):
                    translated_segments.append(texts[i])
            # If we have more segments, truncate
            translated_segments = translated_segments[:len(texts)]
        
        return [seg.strip() for seg in translated_segments]
        
    except Exception as e:
        print(f"Translation API error: {e}")
        print("Falling back to original text for this chunk")
        return texts

def translate_transcript_file(json_path: str, output_path: str, target_language: str, 
                            api_key: str, batch_size: int = 10) -> bool:
    """Translate a single transcript file"""
    
    print(f"Translating: {os.path.basename(json_path)}")
    
    # Load transcript
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  → Error loading file: {e}")
        return False
    
    # Handle both data formats:
    # 1. Wrapped format: {"segments": [...], "language": "en", ...}
    # 2. Flat format: [{"start": ..., "end": ..., "text": ...}, ...]
    if isinstance(data, dict) and 'segments' in data:
        segments = data['segments']
        metadata = {k: v for k, v in data.items() if k != 'segments'}
    elif isinstance(data, list):
        segments = data
        metadata = {}
    else:
        print(f"  → Invalid data format")
        return False
    
    if not segments:
        print(f"  → No segments found")
        return False
    
    print(f"  → {len(segments)} segments to translate")
    
    # Extract texts for translation
    texts_to_translate = []
    segment_indices = []
    
    for i, segment in enumerate(segments):
        text = segment.get('text', '').strip()
        if text:
            texts_to_translate.append(text)
            segment_indices.append(i)
    
    if not texts_to_translate:
        print(f"  → No text content to translate")
        return False
    
    print(f"  → Translating to {target_language}...")
    
    # Translate in batches
    translated_texts = []
    total_batches = (len(texts_to_translate) + batch_size - 1) // batch_size
    
    for batch_idx in range(0, len(texts_to_translate), batch_size):
        batch_texts = texts_to_translate[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        
        print(f"    Batch {batch_num}/{total_batches} ({len(batch_texts)} segments)")
        
        translated_batch = translate_text_chunk(
            batch_texts, target_language, api_key
        )
        translated_texts.extend(translated_batch)
        
        # Rate limiting
        if batch_idx + batch_size < len(texts_to_translate):
            time.sleep(1)  # Pause between batches
    
    # Create translated segments
    translated_segments = []
    translated_idx = 0
    
    for i, original_segment in enumerate(segments):
        new_segment = original_segment.copy()
        
        if i in segment_indices and translated_idx < len(translated_texts):
            new_segment['text'] = translated_texts[translated_idx]
            translated_idx += 1
        
        translated_segments.append(new_segment)
    
    # Create output data structure
    if metadata:
        # Wrapped format - preserve metadata and update language
        output_data = metadata.copy()
        output_data['segments'] = translated_segments
        output_data['language'] = target_language
        output_data['translation_info'] = {
            'original_language': metadata.get('language', 'unknown'),
            'target_language': target_language,
            'translated_segments': len(translated_texts),
            'total_segments': len(segments)
        }
    else:
        # Flat format
        output_data = translated_segments
    
    # Save translated transcript
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"  → Saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"  → Error saving file: {e}")
        return False

def estimate_translation_cost(transcript_dir: str, target_language: str) -> dict:
    """Estimate translation cost based on text content"""
    
    json_files = glob(os.path.join(transcript_dir, '*.json'))
    
    total_words = 0
    total_segments = 0
    file_count = len(json_files)
    
    for json_path in json_files[:5]:  # Sample first 5 files for estimation
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both data formats
            if isinstance(data, dict) and 'segments' in data:
                segments = data['segments']
            elif isinstance(data, list):
                segments = data
            else:
                continue
            
            for segment in segments:
                text = segment.get('text', '').strip()
                if text:
                    total_words += len(text.split())
                    total_segments += 1
                    
        except Exception:
            continue
    
    # Estimate for all files
    if file_count > 5:
        avg_words_per_file = total_words / min(5, file_count)
        total_words = avg_words_per_file * file_count
        
        avg_segments_per_file = total_segments / min(5, file_count)
        total_segments = avg_segments_per_file * file_count
    
    # Cost estimation (rough)
    # GPT-4 input: ~$0.03/1K tokens, output: ~$0.06/1K tokens
    # Assume ~1.3 tokens per word, translation roughly doubles token count
    input_tokens = total_words * 1.3
    output_tokens = total_words * 1.3 * 1.5  # Translation expansion factor
    
    estimated_cost = (input_tokens / 1000 * 0.03) + (output_tokens / 1000 * 0.06)
    
    return {
        'files': file_count,
        'estimated_segments': int(total_segments),
        'estimated_words': int(total_words),
        'estimated_cost_usd': round(estimated_cost, 2),
        'target_language': target_language
    }

def create_translation_readme(output_dir: str, source_language: str, target_language: str, cost_info: dict):
    """Create README.md file documenting the translation process"""
    readme_path = os.path.join(output_dir, "README.md")
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(f"# Translation: {source_language} → {target_language}\n\n")
        f.write(f"This directory contains transcripts translated from {source_language} to {target_language} using OpenAI GPT-4.\n\n")
        
        f.write(f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Processing:** translation\n")
        f.write(f"**Source Language:** {source_language}\n")
        f.write(f"**Target Language:** {target_language}\n")
        f.write(f"**Files Processed:** {cost_info['files']}\n")
        f.write(f"**Estimated Segments:** {cost_info['estimated_segments']}\n")
        f.write(f"**Estimated Cost:** ${cost_info['estimated_cost_usd']:.2f}\n\n")
        
        f.write("## Translation Details\n\n")
        f.write("- **Model:** OpenAI GPT-4\n")
        f.write("- **Approach:** Batch translation with semantic preservation\n")
        f.write("- **Timing:** Original timing data preserved\n")
        f.write("- **Quality:** Professional-grade contextual translation\n\n")
        
        f.write("## File Format\n\n")
        f.write("Each translated JSON file maintains the original structure with:\n")
        f.write("- Original timing information (start/end times)\n")
        f.write("- Translated text content\n")
        f.write("- Language metadata updated to target language\n")
        f.write("- Translation metadata for reference\n\n")
        
        f.write("## Usage\n\n")
        f.write("These translated transcripts can be used with:\n")
        f.write("- FCPXML generator for Final Cut Pro subtitles\n")
        f.write("- ITT generator for standard subtitle files\n")
        f.write("- Markdown generator for readable transcripts\n")
        f.write("- Any application expecting transcript JSON format\n")

def main():
    parser = argparse.ArgumentParser(
        description="Translate transcript JSON files using OpenAI API"
    )
    parser.add_argument('-t', '--transcript-dir', required=True,
                        help='Directory containing JSON transcript files')
    parser.add_argument('-o', '--output-dir', required=True,
                        help='Directory for translated output files')
    parser.add_argument('-l', '--target-language', required=True,
                        help='Target language (e.g., "Spanish", "French", "zh")')
    parser.add_argument('--source-language', default='English',
                        help='Source language (default: English)')
    parser.add_argument('--api-key',
                        help='OpenAI API key (overrides OPENAI_API_KEY env var)')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Number of segments to translate per API call (default: 10)')
    parser.add_argument('--estimate-only', action='store_true',
                        help='Only estimate cost, do not translate')
    parser.add_argument('--skip-confirm', action='store_true',
                        help='Skip interactive confirmation (for automated use)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.transcript_dir):
        sys.exit(f"Error: transcript directory does not exist: {args.transcript_dir}")
    
    # Get API key
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key and not args.estimate_only:
        sys.exit("Error: OpenAI API key required. Set OPENAI_API_KEY env var or use --api-key")
    
    # Get full language name
    target_language = get_language_name(args.target_language)
    
    # Cost estimation
    print(f"🔍 Analyzing transcripts for translation to {target_language}...")
    cost_info = estimate_translation_cost(args.transcript_dir, target_language)
    
    print(f"\n📊 Translation Estimate:")
    print(f"  Files: {cost_info['files']}")
    print(f"  Segments: ~{cost_info['estimated_segments']}")
    print(f"  Words: ~{cost_info['estimated_words']}")
    print(f"  Estimated cost: ~${cost_info['estimated_cost_usd']:.2f}")
    print(f"  Target: {target_language}")
    
    if args.estimate_only:
        return
    
    # Confirm before proceeding (unless skipped)
    if not args.skip_confirm:
        print(f"\n💰 This will cost approximately ${cost_info['estimated_cost_usd']:.2f}")
        confirm = input("Continue with translation? [y/N]: ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Translation cancelled.")
            return
    else:
        print(f"\n💰 Estimated cost: ${cost_info['estimated_cost_usd']:.2f} (proceeding automatically)")
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create README for this translation stage
    create_translation_readme(args.output_dir, args.source_language, target_language, cost_info)
    
    # Find transcript JSON files
    json_files = glob(os.path.join(args.transcript_dir, '*.json'))
    
    if not json_files:
        print(f"No JSON files found in {args.transcript_dir}")
        return
    
    print(f"\n🌐 Starting translation of {len(json_files)} files...")
    print(f"Source: {args.source_language} → Target: {target_language}")
    print("")
    
    success_count = 0
    for json_path in json_files:
        filename = os.path.basename(json_path)
        stem = filename.replace('.json', '')
        
        # Add language suffix to filename
        lang_code = args.target_language.lower().replace(' ', '_')
        output_filename = f"{stem}_{lang_code}.json"
        output_path = os.path.join(args.output_dir, output_filename)
        
        try:
            if translate_transcript_file(json_path, output_path, target_language, 
                                       api_key, args.batch_size):
                success_count += 1
            else:
                print(f"  → Failed: {filename}")
        except Exception as e:
            print(f"  → Error: {e}")
        
        print()  # Add spacing between files
    
    print(f"✅ Translation complete: {success_count}/{len(json_files)} files")
    print(f"📁 Translated files saved to: {args.output_dir}")
    
    if success_count > 0:
        print(f"\n🎯 Next steps:")
        print(f"• Use translated JSON files with ITT/FCPXML generators")
        print(f"• Set language metadata to match your target language")
        print(f"• Generated subtitles will be in {target_language}")

if __name__ == '__main__':
    main()
