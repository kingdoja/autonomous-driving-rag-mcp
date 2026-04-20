"""Text Loader implementation for plain text files.

This module implements text file parsing for .txt files,
converting them to standardized Document format.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.types import Document
from src.libs.loader.base_loader import BaseLoader

logger = logging.getLogger(__name__)


class TextLoader(BaseLoader):
    """Text Loader for plain text files (.txt).
    
    This loader:
    1. Reads text content from .txt files
    2. Preserves the original text format
    3. Extracts metadata from YAML front matter if present
    """
    
    def __init__(self, **kwargs):
        """Initialize TextLoader.
        
        Args:
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
    
    def load(self, file_path: str | Path) -> Document:
        """Load a text file and convert to Document.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Document object with parsed content and metadata
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a .txt file
        """
        file_path = self._validate_file(file_path)
        
        if file_path.suffix.lower() not in ['.txt', '.md']:
            raise ValueError(f"Unsupported file type: {file_path.suffix}. Expected .txt or .md")
        
        logger.info(f"Loading text file: {file_path}")
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from YAML front matter if present
            yaml_metadata = self._extract_yaml_metadata(content)
            
            # Remove YAML front matter from content
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2].strip()
            
            # Calculate document hash (used as document ID)
            doc_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            # Create document with required structure
            document = Document(
                id=doc_hash,
                text=content,
                metadata={
                    'source_path': str(file_path),
                    'doc_type': 'text',
                    'file_name': file_path.name,
                    **yaml_metadata
                }
            )
            
            logger.info(f"Successfully loaded text file: {file_path.name} (id={doc_hash[:16]}...)")
            return document
            
        except Exception as e:
            logger.error(f"Failed to load text file {file_path}: {e}")
            raise
    
    def _extract_yaml_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from YAML front matter.
        
        Args:
            content: File content
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        if not content.startswith('---'):
            return metadata
        
        try:
            import yaml
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_content = parts[1].strip()
                metadata = yaml.safe_load(yaml_content) or {}
        except Exception as e:
            logger.warning(f"Failed to parse YAML front matter: {e}")
        
        return metadata
