"""
Data Ingestion Agent - Processes and indexes documents for analysis
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
import mimetypes
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .base_agent import BaseAgent
from ..core.state import DiligenceState, Document
from ..core.llm_factory import get_llm
from ..integrations.gcs_client import get_gcs_client

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not available, PDF processing disabled")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available, DOCX processing disabled")

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available, vector search disabled")


class DataIngestionAgent(BaseAgent):
    """
    Data Ingestion Agent - The Librarian
    
    Responsibilities:
    - Process uploaded documents (PDF, DOCX, TXT, etc.)
    - Extract text and metadata
    - Perform OCR on scanned documents
    - Create vector embeddings
    - Index documents for semantic search
    - Catalog all data sources
    """
    
    def __init__(self):
        """Initialize Data Ingestion Agent"""
        super().__init__("data_ingestion")
        self.gcs_client = get_gcs_client()
        
        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize vector database if available
        self.vector_db = None
        if CHROMA_AVAILABLE:
            try:
                self.vector_db = chromadb.PersistentClient(path="data/chromadb")
                logger.info("ChromaDB initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize ChromaDB: {e}")
    
    async def run(self, state: DiligenceState) -> DiligenceState:
        """
        Run method required by BaseAgent
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state
        """
        return await self.execute(state)
    
    async def execute(self, state: DiligenceState) -> DiligenceState:
        """
        Execute data ingestion tasks
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with processed documents
        """
        try:
            logger.info(f"📚 Data Ingestion: Processing documents for deal {state['deal_id']}")
            
            if not state['documents']:
                logger.info("No documents to process")
                return state
            
            # Step 1: Process each document
            processed_docs = []
            for doc in state['documents']:
                processed_doc = await self._process_document(doc, state)
                if processed_doc:
                    processed_docs.append(processed_doc)
            
            # Step 2: Create document catalog
            catalog = self._create_catalog(processed_docs)
            state['metadata']["document_catalog"] = catalog
            
            # Step 3: Create vector index
            if self.vector_db and processed_docs:
                collection_name = f"deal_{state['deal_id']}"
                await self._create_vector_index(processed_docs, collection_name)
                state['metadata']["vector_collection"] = collection_name
            
            # Step 4: Upload to GCS
            for doc in processed_docs:
                await self._upload_to_gcs(doc, state['deal_id'])
            
            # Step 5: Generate document summary
            summary = await self._generate_document_summary(processed_docs, state)
            state['metadata']["document_summary"] = summary
            
            logger.info(f"✅ Processed {len(processed_docs)} documents successfully")
            
            # Update state documents
            state['documents'] = processed_docs
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Data Ingestion failed: {e}")
            state['errors'].append({
                "agent": "data_ingestion",
                "error": str(e),
                "phase": "document_processing"
            })
            return state
    
    async def _process_document(
        self,
        doc: Document,
        state: DiligenceState
    ) -> Optional[Document]:
        """
        Process a single document
        
        Args:
            doc: Document to process
            state: Current state
        
        Returns:
            Processed document or None if failed
        """
        try:
            logger.info(f"Processing document: {doc.filename}")
            
            # Determine file type
            file_type = self._get_file_type(doc.filename)
            
            # Extract text based on type
            if file_type == "pdf":
                text = self._extract_from_pdf(doc.filepath)
            elif file_type == "docx":
                text = self._extract_from_docx(doc.filepath)
            elif file_type == "txt":
                text = self._extract_from_txt(doc.filepath)
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return None
            
            if not text or len(text.strip()) < 50:
                logger.warning(f"No meaningful content extracted from {doc.filename}")
                return None
            
            # Update document with extracted content
            doc.content = text
            doc.metadata["word_count"] = len(text.split())
            doc.metadata["char_count"] = len(text)
            doc.metadata["processed"] = True
            
            # Classify document using AI
            classification = await self._classify_document(doc)
            doc.metadata["classification"] = classification
            
            # Extract key information
            key_info = await self._extract_key_information(doc)
            doc.metadata["key_information"] = key_info
            
            logger.info(f"✅ Processed: {doc.filename} ({doc.metadata['word_count']} words)")
            
            return doc
            
        except Exception as e:
            logger.error(f"Failed to process {doc.filename}: {e}")
            return None
    
    def _get_file_type(self, filename: str) -> str:
        """Get file type from filename"""
        suffix = Path(filename).suffix.lower()
        type_map = {
            ".pdf": "pdf",
            ".docx": "docx",
            ".doc": "docx",
            ".txt": "txt",
            ".md": "txt"
        }
        return type_map.get(suffix, "unknown")
    
    def _extract_from_pdf(self, filepath: str) -> str:
        """Extract text from PDF"""
        if not PDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            logger.warning("No PDF library available")
            return ""
        
        try:
            # Try pdfplumber first (better for tables)
            if PDFPLUMBER_AVAILABLE:
                import pdfplumber
                text = []
                with pdfplumber.open(filepath) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text.append(page_text)
                return "\n\n".join(text)
            
            # Fallback to PyPDF2
            elif PDF_AVAILABLE:
                text = []
                with open(filepath, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text.append(page.extract_text())
                return "\n\n".join(text)
        
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ""
    
    def _extract_from_docx(self, filepath: str) -> str:
        """Extract text from DOCX"""
        if not DOCX_AVAILABLE:
            logger.warning("python-docx not available")
            return ""
        
        try:
            doc = DocxDocument(filepath)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return ""
    
    def _extract_from_txt(self, filepath: str) -> str:
        """Extract text from TXT"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try different encoding
            with open(filepath, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            logger.error(f"TXT extraction failed: {e}")
            return ""
    
    async def _classify_document(self, doc: Document) -> Dict[str, Any]:
        """
        Classify document using AI
        
        Args:
            doc: Document to classify
        
        Returns:
            Classification information
        """
        try:
            # Get first 1000 characters for classification
            sample = doc.content[:1000] if doc.content else ""
            
            prompt = f"""Classify this document from an M&A due diligence package.

Document Filename: {doc.filename}
Content Sample:
{sample}

Provide:
1. Document Type (e.g., Financial Statement, Legal Contract, Market Report, etc.)
2. Category (financial, legal, operational, market, technical)
3. Key Topics (list of 3-5 main topics)
4. Importance (High/Medium/Low)
5. Summary (1-2 sentences)

Format as JSON."""
            
            messages = [
                SystemMessage(content="You are a document classification expert."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Parse response (simplified - in production, use structured output)
            return {
                "type": "Unknown",
                "category": doc.document_type,
                "importance": "Medium",
                "ai_summary": response.content[:200]
            }
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return {"type": "Unknown", "category": doc.document_type}
    
    async def _extract_key_information(self, doc: Document) -> Dict[str, Any]:
        """
        Extract key information from document
        
        Args:
            doc: Document to analyze
        
        Returns:
            Key information dictionary
        """
        try:
            # For now, return basic info
            # In production, use AI to extract entities, numbers, dates, etc.
            return {
                "extracted_at": "2025-01-20",
                "entities": [],
                "key_numbers": [],
                "dates": []
            }
        except Exception as e:
            logger.error(f"Information extraction failed: {e}")
            return {}
    
    def _create_catalog(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Create document catalog
        
        Args:
            documents: List of processed documents
        
        Returns:
            Catalog information
        """
        catalog = {
            "total_documents": len(documents),
            "by_type": {},
            "total_words": 0,
            "documents": []
        }
        
        for doc in documents:
            # Count by type
            doc_type = doc.document_type
            catalog["by_type"][doc_type] = catalog["by_type"].get(doc_type, 0) + 1
            
            # Add to total word count
            catalog["total_words"] += doc.metadata.get("word_count", 0)
            
            # Add document info
            catalog["documents"].append({
                "id": doc.document_id,
                "filename": doc.filename,
                "type": doc.document_type,
                "word_count": doc.metadata.get("word_count", 0),
                "processed": doc.metadata.get("processed", False)
            })
        
        return catalog
    
    async def _create_vector_index(
        self,
        documents: List[Document],
        collection_name: str
    ):
        """
        Create vector index for semantic search
        
        Args:
            documents: Documents to index
            collection_name: Name of collection
        """
        if not self.vector_db:
            logger.warning("Vector database not available")
            return
        
        try:
            # Get or create collection
            collection = self.vector_db.get_or_create_collection(
                name=collection_name,
                metadata={"description": "M&A due diligence documents"}
            )
            
            # Process each document
            for doc in documents:
                if not doc.content:
                    continue
                
                # Split into chunks
                chunks = self.text_splitter.split_text(doc.content)
                
                # Add chunks to collection
                for i, chunk in enumerate(chunks):
                    collection.add(
                        ids=[f"{doc.document_id}_chunk_{i}"],
                        documents=[chunk],
                        metadatas=[{
                            "document_id": doc.document_id,
                            "filename": doc.filename,
                            "type": doc.document_type,
                            "chunk_index": i
                        }]
                    )
            
            logger.info(f"✅ Created vector index: {collection_name}")
            
        except Exception as e:
            logger.error(f"Vector indexing failed: {e}")
    
    async def _upload_to_gcs(self, doc: Document, deal_id: str):
        """
        Upload document to GCS
        
        Args:
            doc: Document to upload
            deal_id: Deal identifier
        """
        try:
            # Determine GCS path
            gcs_path = self.gcs_client.get_deal_path(
                deal_id,
                f"documents/{doc.document_type}"
            )
            destination = f"{gcs_path}/{doc.filename}"
            
            # Upload file
            uploaded_path = self.gcs_client.upload_file(
                doc.filepath,
                destination
            )
            
            # Update document metadata
            doc.metadata["gcs_path"] = uploaded_path
            
            logger.info(f"✅ Uploaded to storage: {doc.filename}")
            
        except Exception as e:
            logger.error(f"GCS upload failed: {e}")
    
    async def _generate_document_summary(
        self,
        documents: List[Document],
        state: DiligenceState
    ) -> str:
        """
        Generate overall summary of all documents
        
        Args:
            documents: List of processed documents
            state: Current state
        
        Returns:
            Summary text
        """
        try:
            doc_list = "\n".join([
                f"- {doc.filename} ({doc.document_type}): {doc.metadata.get('word_count', 0)} words"
                for doc in documents
            ])
            
            prompt = f"""Provide a brief summary of the document package for this M&A deal.

Deal: {state['target_company']}
Documents Processed:
{doc_list}

Create a 2-3 sentence summary of what documents were provided and their overall quality/completeness."""
            
            messages = [
                SystemMessage(content="You are a due diligence document analyst."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"Processed {len(documents)} documents for analysis."
