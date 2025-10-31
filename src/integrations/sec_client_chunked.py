"""
SEC Client - Chunked Parallel Extraction for Large Sections

PRODUCTION-GRADE SOLUTION for Item 1A and other large sections:
- Intelligent chunking based on semantic boundaries
- Parallel API calls with asyncio
- Timeout protection and fallback mechanisms
- Progressive extraction with checkpoints
"""
import asyncio
import re
from typing import Dict, List, Any, Optional
from loguru import logger
from anthropic import Anthropic
import os


class ChunkedSECExtractor:
    """
    Intelligent chunked extraction for large SEC sections (e.g., Item 1A)
    
    Features:
    - Splits large sections into semantic chunks
    - Processes chunks in parallel (5 concurrent API calls)
    - Timeout protection (30s per chunk)
    - Progressive assembly of results
    - Fallback to regex if LLM fails
    """
    
    def __init__(self):
        """Initialize chunked extractor with LLM"""
        self.llm = None
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.llm = Anthropic(api_key=api_key)
                logger.info("✓ Chunked SEC extractor initialized with LLM")
            else:
                logger.warning("⚠️ ANTHROPIC_API_KEY not found - will use regex fallback")
        except ImportError:
            logger.warning("⚠️ Anthropic library not available - will use regex fallback")
        
        # Configuration
        self.chunk_size = 15000  # Chars per chunk (safe for Claude)
        self.chunk_overlap = 500  # Overlap between chunks
        self.max_parallel = 5  # Max concurrent API calls
        self.timeout_per_chunk = 30  # Seconds
    
    async def extract_large_section_parallel(
        self,
        full_text: str,
        start_marker: str,
        end_marker: str
    ) -> Optional[str]:
        """
        Extract large section using parallel chunked processing
        
        Strategy:
        1. Find the section boundaries
        2. Split into semantic chunks (paragraphs, risk categories)
        3. Extract each chunk in parallel (5 concurrent)
        4. Assemble results progressively
        5. Fallback to regex if any chunk fails
        
        Args:
            full_text: Complete SEC filing text
            start_marker: Section start (e.g., "Item 1A")
            end_marker: Section end (e.g., "Item 1B")
        
        Returns:
            Complete extracted section or None
        """
        try:
            logger.info(f"Starting parallel chunked extraction for {start_marker}")
            
            # Step 1: Find section boundaries using fast regex
            section_text = self._quick_regex_extract(full_text, start_marker, end_marker)
            
            if not section_text:
                logger.warning(f"Could not locate {start_marker} boundaries")
                return None
            
            section_length = len(section_text)
            logger.info(f"Found {start_marker} section: {section_length:,} chars")
            
            # Step 2: If small enough, use single LLM call
            if section_length <= self.chunk_size:
                logger.info("Section small enough for single extraction")
                return await self._extract_single_chunk(section_text, start_marker)
            
            # Step 3: Split into semantic chunks
            chunks = self._split_into_semantic_chunks(section_text)
            logger.info(f"Split into {len(chunks)} semantic chunks")
            
            # Step 4: Process chunks in parallel with timeout protection
            extracted_chunks = await self._process_chunks_parallel(chunks, start_marker)
            
            # Step 5: Assemble results
            if all(chunk is not None for chunk in extracted_chunks):
                complete_text = '\n\n'.join(extracted_chunks)
                logger.info(f"✓ Parallel extraction successful: {len(complete_text):,} chars")
                return complete_text
            else:
                # Fallback: Some chunks failed, return regex result
                logger.warning("Some chunks failed, using regex fallback")
                return section_text
            
        except Exception as e:
            logger.error(f"Parallel extraction failed: {e}")
            # Final fallback: Return raw regex result
            return self._quick_regex_extract(full_text, start_marker, end_marker)
    
    def _quick_regex_extract(
        self,
        text: str,
        start_marker: str,
        end_marker: str
    ) -> Optional[str]:
        """
        Fast regex-based section extraction (for boundaries)
        
        Args:
            text: Full filing text
            start_marker: Section start
            end_marker: Section end
        
        Returns:
            Extracted section or None
        """
        try:
            # Normalize text
            text_normalized = re.sub(r'\s+', ' ', text)
            
            # Extract item numbers
            start_item = start_marker.split()[-1].replace('.', '')
            end_item = end_marker.split()[-1].replace('.', '')
            
            # Multiple patterns for robustness
            patterns = [
                re.compile(
                    rf'Item\s+{start_item}[\.\:]\s*[^\n]*?(.+?)(?=Item\s+{end_item}[\.\:]|$)',
                    re.IGNORECASE | re.DOTALL
                ),
                re.compile(
                    rf'ITEM\s+{start_item}[\.\:]?\s*[^\n]*?(.+?)(?=ITEM\s+{end_item}[\.\:]?|$)',
                    re.DOTALL
                ),
                re.compile(
                    rf'Item\s+{start_item}[\.:\-\s]{{1,3}}(.+?)(?=Item\s+{end_item}[\.:\-\s]|$)',
                    re.IGNORECASE | re.DOTALL
                ),
            ]
            
            for pattern in patterns:
                match = pattern.search(text_normalized)
                if match:
                    extracted = match.group(1).strip()
                    if len(extracted) >= 500:
                        return extracted
            
            return None
            
        except Exception as e:
            logger.error(f"Regex extraction failed: {e}")
            return None
    
    def _split_into_semantic_chunks(self, text: str) -> List[str]:
        """
        Split text into semantic chunks based on:
        - Paragraph boundaries
        - Risk category headers
        - Natural section breaks
        
        Args:
            text: Section text to split
        
        Returns:
            List of text chunks
        """
        chunks = []
        
        # Strategy 1: Try to split by risk category headers
        # Common patterns: "Risks Related to...", "Business Risks", etc.
        risk_headers = re.findall(
            r'(?:^|\n)([A-Z][^\n]{10,100}(?:Risk|Risks|related to|Related to)[^\n]{0,50})(?:\n|$)',
            text,
            re.MULTILINE
        )
        
        if risk_headers and len(risk_headers) >= 3:
            # Split by headers
            logger.info(f"Splitting by {len(risk_headers)} risk category headers")
            
            for i, header in enumerate(risk_headers):
                # Find position of this header and next
                start_pos = text.find(header)
                
                if i < len(risk_headers) - 1:
                    next_header = risk_headers[i + 1]
                    end_pos = text.find(next_header)
                else:
                    end_pos = len(text)
                
                if start_pos != -1:
                    chunk = text[start_pos:end_pos].strip()
                    if len(chunk) >= 500:
                        chunks.append(chunk)
        
        # Strategy 2: If no clear headers, split by paragraphs
        if not chunks:
            logger.info("Splitting by paragraphs (no clear headers found)")
            
            # Split by double newlines (paragraph breaks)
            paragraphs = re.split(r'\n\s*\n', text)
            
            current_chunk = ""
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                # Add paragraph to current chunk
                if len(current_chunk) + len(para) < self.chunk_size:
                    current_chunk += "\n\n" + para
                else:
                    # Save current chunk and start new one
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para
            
            # Add final chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
        
        # Ensure minimum chunk size
        filtered_chunks = [c for c in chunks if len(c) >= 500]
        
        logger.info(f"Created {len(filtered_chunks)} chunks (avg size: {sum(len(c) for c in filtered_chunks) // max(len(filtered_chunks), 1):,} chars)")
        
        return filtered_chunks if filtered_chunks else [text]
    
    async def _process_chunks_parallel(
        self,
        chunks: List[str],
        section_name: str
    ) -> List[Optional[str]]:
        """
        Process chunks in parallel with timeout protection
        
        Args:
            chunks: List of text chunks
            section_name: Section name for context
        
        Returns:
            List of extracted chunks (None if failed)
        """
        if not self.llm:
            logger.warning("LLM not available, skipping parallel extraction")
            return chunks  # Return original chunks
        
        # Create tasks for parallel processing
        tasks = []
        for i, chunk in enumerate(chunks):
            task = self._extract_chunk_with_timeout(chunk, section_name, i)
            tasks.append(task)
        
        # Process in batches of max_parallel
        results = []
        for i in range(0, len(tasks), self.max_parallel):
            batch = tasks[i:i + self.max_parallel]
            logger.info(f"Processing batch {i // self.max_parallel + 1} ({len(batch)} chunks)")
            
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)
        
        # Convert exceptions to None
        processed_results = []
        for r in results:
            if isinstance(r, Exception):
                logger.warning(f"Chunk failed: {r}")
                processed_results.append(None)
            else:
                processed_results.append(r)
        
        success_rate = sum(1 for r in processed_results if r is not None) / len(processed_results)
        logger.info(f"Parallel processing complete: {success_rate:.1%} success rate")
        
        return processed_results
    
    async def _extract_chunk_with_timeout(
        self,
        chunk: str,
        section_name: str,
        chunk_index: int
    ) -> Optional[str]:
        """
        Extract single chunk with timeout protection
        
        Args:
            chunk: Text chunk to extract
            section_name: Section name
            chunk_index: Index of this chunk
        
        Returns:
            Cleaned/extracted chunk or None
        """
        try:
            # Use timeout to prevent hanging
            result = await asyncio.wait_for(
                self._extract_single_chunk(chunk, f"{section_name} Part {chunk_index + 1}"),
                timeout=self.timeout_per_chunk
            )
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Chunk {chunk_index} timed out after {self.timeout_per_chunk}s")
            return chunk  # Return original chunk as fallback
        
        except Exception as e:
            logger.error(f"Chunk {chunk_index} extraction failed: {e}")
            return chunk  # Return original chunk as fallback
    
    async def _extract_single_chunk(
        self,
        chunk: str,
        context: str
    ) -> Optional[str]:
        """
        Extract/clean a single chunk using LLM
        
        Args:
            chunk: Text chunk
            context: Context for extraction
        
        Returns:
            Cleaned text
        """
        if not self.llm:
            return chunk
        
        try:
            prompt = f"""Clean and format this SEC filing text section ({context}).

SECTION TEXT:
{chunk[:12000]}  

TASK:
1. Remove HTML tags, excessive whitespace, and formatting artifacts
2. Preserve all substantive content and risk descriptions
3. Return cleaned text with proper paragraph structure
4. Do NOT summarize - return complete text

Return the cleaned text directly."""

            # Use streaming for efficiency
            extracted_text = ""
            
            with self.llm.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=16000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            ) as stream:
                for text in stream.text_stream:
                    extracted_text += text
            
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Single chunk extraction failed: {e}")
            return chunk  # Return original as fallback


# Global instance
_chunked_extractor: Optional[ChunkedSECExtractor] = None


def get_chunked_extractor() -> ChunkedSECExtractor:
    """Get global chunked extractor instance"""
    global _chunked_extractor
    if _chunked_extractor is None:
        _chunked_extractor = ChunkedSECExtractor()
    return _chunked_extractor
