import os
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, pdf_storage_path, chunk_size=1000, chunk_overlap=200):
        self.pdf_storage_path = pdf_storage_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, 
            chunk_overlap=self.chunk_overlap
        )
    
    def save_pdf(self, pdf_file):
        """Save uploaded PDF to storage with a unique ID"""
        filename = pdf_file.filename
        file_id = str(uuid.uuid4())
        
        # Get extension from original filename or default to .pdf
        _, ext = os.path.splitext(filename)
        if not ext:
            ext = '.pdf'
        
        # Create a filename with the unique ID
        unique_filename = f"{file_id}{ext}"
        file_path = os.path.join(self.pdf_storage_path, unique_filename)
        
        # Save the file
        pdf_file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        return {
            "id": file_id,
            "name": filename,
            "size": file_size,
            "path": file_path,
            "status": "uploaded"
        }

    def extract_text(self, file_path):
        """Extract text from PDF"""
        try:
            pdf = PdfReader(file_path)
            text = ""
            page_map = {}
            current_pos = 0
            
            # Extract text from each page
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                text += page_text + "\n\n"
                
                # Map character positions to page numbers for source attribution
                end_pos = current_pos + len(page_text)
                page_map[i+1] = (current_pos, end_pos)
                current_pos = end_pos + 2  # +2 for the newlines
                
            return text, page_map, len(pdf.pages)
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def chunk_text(self, text):
        """Split text into chunks for embedding"""
        try:
            chunks = self.text_splitter.split_text(text)
            return chunks
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            raise

    def map_chunks_to_pages(self, chunks, text, page_map):
        """Map each chunk to its source page numbers"""
        chunk_page_map = []
        
        # For each chunk, find which page(s) it comes from
        for chunk in chunks:
            chunk_start = text.find(chunk)
            if chunk_start == -1:
                # If exact match not found, this is a fallback
                chunk_page_map.append({"chunk": chunk, "pages": []})
                continue
                
            chunk_end = chunk_start + len(chunk)
            chunk_pages = []
            
            # Check which pages contain this chunk
            for page_num, (page_start, page_end) in page_map.items():
                # If there's overlap between chunk and page
                if not (chunk_end < page_start or chunk_start > page_end):
                    chunk_pages.append(page_num)
            
            chunk_page_map.append({
                "chunk": chunk, 
                "pages": chunk_pages
            })
        
        return chunk_page_map

    def process_pdf(self, file_info):
        """Process a PDF file: extract text, chunk it, and map chunks to pages"""
        try:
            file_path = file_info["path"]
            
            # Extract text from PDF
            text, page_map, num_pages = self.extract_text(file_path)
            
            # Chunk the text
            chunks = self.chunk_text(text)
            
            # Map chunks to pages
            chunk_page_map = self.map_chunks_to_pages(chunks, text, page_map)
            
            # Update file info
            file_info["pages"] = num_pages
            file_info["status"] = "processed"
            
            return chunks, chunk_page_map, file_info
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            file_info["status"] = "error"
            file_info["error"] = str(e)
            return [], [], file_info