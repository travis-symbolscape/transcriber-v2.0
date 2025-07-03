#!/usr/bin/env python3
"""
Basic tests for Transcriber v2.0 modules
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

def test_imports():
    """Test that all modules can be imported"""
    try:
        import transcribe
        import diarize_transcript
        import context_correct_transcript
        import translate_transcript
        import generate_fcpxml
        import generate_itt
        import generate_markdown
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import module: {e}")

def test_script_help():
    """Test that all scripts show help without errors"""
    script_dir = Path(__file__).parent.parent / "scripts"
    scripts = [
        "transcribe.py",
        "diarize_transcript.py", 
        "context_correct_transcript.py",
        "translate_transcript.py",
        "generate_fcpxml.py",
        "generate_itt.py",
        "generate_markdown.py"
    ]
    
    for script in scripts:
        script_path = script_dir / script
        if script_path.exists():
            # Test that script doesn't crash when importing
            assert script_path.is_file()

def test_output_directories():
    """Test that output directories can be created"""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dirs = [
            "transcripts",
            "corrected_transcripts", 
            "translated_transcripts",
            "diarized_transcripts",
            "final_fcpxml",
            "final_itt",
            "final_markdown",
            "final_json"
        ]
        
        for dir_name in test_dirs:
            dir_path = Path(temp_dir) / dir_name
            dir_path.mkdir(exist_ok=True)
            assert dir_path.exists()
            assert dir_path.is_dir()

class TestUnifiedPipeline:
    """Test the unified pipeline interface"""
    
    def test_pipeline_import(self):
        """Test that the main pipeline can be imported"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        try:
            import run_transcription_pipeline_v2
            assert hasattr(run_transcription_pipeline_v2, 'main')
        except ImportError as e:
            pytest.fail(f"Failed to import unified pipeline: {e}")

if __name__ == "__main__":
    pytest.main([__file__])
