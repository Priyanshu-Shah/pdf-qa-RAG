import os
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
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
        
        # Initialize processor methods dictionary
        self.processors = {
            "standard": self.process_standard,
            "semantic": self.process_semantic,
            "layout": self.process_layout,
        }
    
    def save_pdf(self, pdf_file):
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
        file_size = os.path.getsize(file_path)
        
        return {
            "id": file_id,
            "name": filename,
            "size": file_size,
            "path": file_path,
            "status": "uploaded"
        }

    def extract_text(self, file_path):
        """Standard text extraction using PyPDF"""
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
    
    def extract_text_with_structure(self, file_path):
        """Extract text while preserving document structure using Unstructured"""
        try:
            from unstructured.partition.auto import partition_auto
            # try:
            #     import importlib.util
            #     if importlib.util.find_spec("unstructured") is None:
            #         logger.warning("Unstructured library not available. Falling back to standard extraction.")
            #         raise ImportError("Unstructured library not available")
                
            #     from unstructured.partition.pdf import partition_pdf
            # except ImportError:
            #     logger.warning("Unstructured library not available. Falling back to standard extraction.")
            #     # Fall back to standard text extraction but return 4 values
            #     text, page_map, num_pages = self.extract_text(file_path)
            #     # Return empty headers list to maintain the expected 4 return values
            #     return text, page_map, num_pages, []
        
            # elements = partition_pdf(
            #     file_path,
            #     extract_images_in_pdf=False,
            #     infer_table_structure=True
            # )

            elements_auto = partition_auto(
                file_path,
                extract_images_in_pdf=False,
                infer_table_structure=True
            )
            
            # Group elements by type and page
            structured_text = ""
            page_map = {}
            current_pos = 0
            text_elements = []
            
            # Get headers to create markdown structure
            headers = []
            current_page = 1
            page_texts = {}
            
            for element in elements_auto:
                element_text = str(element)
                # Check if this element is from a different page
                page_num = element.metadata.page_number if hasattr(element, "metadata") and hasattr(element.metadata, "page_number") else current_page
                
                # Initialize page text if needed
                if page_num not in page_texts:
                    page_texts[page_num] = ""
                
                # Add element text to the corresponding page
                if hasattr(element, "category") and element.category == "Title":
                    level = min(3, 1 + element_text.count('.'))  # Estimate heading level
                    page_texts[page_num] += f"{'#' * level} {element_text}\n\n"
                    headers.append((element_text, f"Header {level}"))
                else:
                    page_texts[page_num] += element_text + "\n\n"
                
                current_page = max(current_page, page_num)
            
            # Combine all page texts with page markers
            for page_num in sorted(page_texts.keys()):
                page_start = current_pos
                page_text = page_texts[page_num]
                structured_text += page_text
                
                # Map this page's position in the full text
                current_pos += len(page_text)
                page_map[page_num] = (page_start, current_pos)
            
            return structured_text, page_map, current_page, headers
            
        except Exception as e:
            logger.error(f"Error extracting structured text from PDF: {e}")
            # Fall back to standard extraction
            logger.info("Falling back to standard text extraction")
            text, page_map, num_pages = self.extract_text(file_path)
            # Return empty headers list
            return text, page_map, num_pages, []
    
    def extract_with_layout(self, file_path):
        """Extract text while preserving layout information"""
        try:
            import layoutparser as lp
            import pdf2image
            import pytesseract
            
            # Convert PDF to images
            images = pdf2image.convert_from_path(file_path)
            
            # Try to load OCR model
            try:
                ocr_agent = lp.TesseractAgent(languages='eng')
            except Exception as ocr_error:
                logger.error(f"Error loading OCR: {ocr_error}")
                # Fall back if OCR fails
                return self.extract_text_with_structure(file_path)
            
            # Try to load layout model
            try:
                model = lp.Detectron2LayoutModel(
                    'lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config', 
                    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
                    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
                )
            except Exception as model_error:
                logger.error(f"Error loading layout model: {model_error}")
                # Fall back if model loading fails
                return self.extract_text_with_structure(file_path)
                
            all_elements = []
            structured_text = ""
            page_map = {}
            current_pos = 0
            
            # Process each page
            for i, image in enumerate(images):
                page_num = i + 1
                page_start = current_pos
                page_text = ""
                
                try:
                    # Detect layout
                    layout = model.detect(image)
                    
                    # Sort elements by their vertical position to maintain reading order
                    sorted_blocks = sorted(layout, key=lambda block: block.coordinates[1])
                    
                    # Process each element based on its type
                    for block in sorted_blocks:
                        element_type = block.type
                        
                        # Extract text with OCR
                        segment_image = (image.crop(block.coordinates))
                        text = ocr_agent.detect(segment_image)
                        
                        # Format based on element type
                        if element_type == "Title":
                            page_text += f"# {text.strip()}\n\n"
                        elif element_type == "List":
                            # Convert lines to list items
                            list_items = text.strip().split("\n")
                            for item in list_items:
                                page_text += f"- {item.strip()}\n"
                            page_text += "\n"
                        elif element_type == "Table":
                            page_text += f"[TABLE]\n{text.strip()}\n[/TABLE]\n\n"
                        else:
                            page_text += f"{text.strip()}\n\n"
                            
                except Exception as page_error:
                    logger.error(f"Error processing page {page_num}: {page_error}")
                    # If layout processing fails, try to extract just the text
                    try:
                        page_text = pytesseract.image_to_string(image)
                    except:
                        page_text = f"[Failed to extract text from page {page_num}]"
                
                # Add the page text to the full document text
                structured_text += page_text
                current_pos += len(page_text)
                
                # Map this page's position in the full text
                page_map[page_num] = (page_start, current_pos)
            
            return structured_text, page_map, len(images), []
                
        except Exception as e:
            logger.error(f"Error in layout-aware processing: {e}")
            # Fall back to structured extraction
            return self.extract_text_with_structure(file_path)
    
    def chunk_text(self, text, method="recursive"):
        """Chunk text using the specified method"""
        try:
            if method == "recursive":
                return self.text_splitter.split_text(text)
            elif method == "markdown":
                markdown_splitter = MarkdownHeaderTextSplitter(
                    headers_to_split_on=[
                        ("#", "Header 1"),
                        ("##", "Header 2"),
                        ("###", "Header 3"),
                    ]
                )
                md_header_splits = markdown_splitter.split_text(text)
                
                # Now split these potentially large chunks into smaller ones
                chunks = []
                for split in md_header_splits:
                    # Extract the metadata
                    metadata = {k: v for k, v in split.metadata.items()}
                    
                    # Split the content into smaller chunks if needed
                    if len(split.page_content) > self.chunk_size:
                        smaller_chunks = self.text_splitter.split_text(split.page_content)
                        for chunk in smaller_chunks:
                            chunks.append(chunk)
                    else:
                        chunks.append(split.page_content)
                
                return chunks
            else:
                # Default to recursive
                return self.text_splitter.split_text(text)
                
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            # Fall back to standard chunking
            return self.text_splitter.split_text(text)
    
    def map_chunks_to_pages(self, chunks, text, page_map):
        """Map chunks to their source pages"""
        chunk_page_map = []
        
        # For each chunk, find which page it comes from
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
    
    def process_standard(self, file_info):
        """Standard PDF processing with basic text extraction and chunking"""
        try:
            logger.info(f"🔍 Starting standard processing for '{file_info['name']}'")
            file_path = file_info["path"]
            
            # Extract text from PDF using standard method
            text, page_map, num_pages = self.extract_text(file_path)
            
            # Chunk the text using recursive character splitting
            chunks = self.chunk_text(text, "recursive")
            
            # Map chunks to pages
            chunk_page_map = self.map_chunks_to_pages(chunks, text, page_map)
            
            # Update file info
            file_info["pages"] = num_pages
            file_info["status"] = "processed"
            file_info["processing_method"] = "standard"
            
            return chunks, chunk_page_map, file_info
            
        except Exception as e:
            logger.error(f"Error in standard PDF processing: {e}")
            file_info["status"] = "error"
            file_info["error"] = str(e)
            return [], [], file_info
    
    def process_semantic(self, file_info):
        """Semantic PDF processing using structure-aware extraction"""
        try:
            logger.info(f"📚 Starting semantic processing for '{file_info['name']}'")
            file_path = file_info["path"]
            
            # Extract text from PDF using structure-aware method
            text, page_map, num_pages, headers = self.extract_text_with_structure(file_path)
            
            # Chunk the text using markdown-aware splitting if we found headers
            if headers:
                chunks = self.chunk_text(text, "markdown")
            else:
                chunks = self.chunk_text(text, "recursive")
            
            # Map chunks to pages
            chunk_page_map = self.map_chunks_to_pages(chunks, text, page_map)
            
            # Update file info
            file_info["pages"] = num_pages
            file_info["status"] = "processed"
            file_info["processing_method"] = "semantic"
            
            return chunks, chunk_page_map, file_info
            
        except Exception as e:
            logger.error(f"Error in semantic PDF processing: {e}")
            # Fall back to standard processing
            logger.info("Falling back to standard processing")
            return self.process_standard(file_info)
    
    def process_layout(self, file_info):
        """Layout-aware PDF processing using OCR and layout detection"""
        try:
            logger.info(f"🖼️ Starting layout processing for '{file_info['name']}'")
            file_path = file_info["path"]
            
            # Extract text from PDF using layout-aware method
            text, page_map, num_pages, _ = self.extract_with_layout(file_path)
            
            # Chunk the text (we'll use markdown chunking since the layout extraction adds markdown)
            chunks = self.chunk_text(text, "markdown") 
            
            # Map chunks to pages
            chunk_page_map = self.map_chunks_to_pages(chunks, text, page_map)
            
            # Update file info
            file_info["pages"] = num_pages
            file_info["status"] = "processed"
            file_info["processing_method"] = "layout"
            
            return chunks, chunk_page_map, file_info
            
        except Exception as e:
            logger.error(f"Error in layout-aware PDF processing: {e}")
            # Fall back to semantic processing
            logger.info("Falling back to semantic processing")
            return self.process_semantic(file_info)
    
    def process_pdf(self, file_info, method="standard"):
        """Process a PDF file using the specified method"""
        try:
            # Log the processing request
            logger.info(f"📄 Processing PDF '{file_info['name']}' using method: {method}")
            
            # Select processing method based on parameter
            if method in self.processors:
                processor = self.processors[method]
            else:
                logger.warning(f"⚠️ Unknown processing method: {method}, falling back to standard")
                processor = self.processors["standard"]
            
            # Process using selected method and time it
            import time
            start_time = time.time()
            result = processor(file_info)
            elapsed_time = time.time() - start_time
            
            # Log the processing result
            logger.info(f"✅ Processed PDF '{file_info['name']}' with {method} method in {elapsed_time:.2f}s")
            
            return result
        except Exception as e:
            logger.error(f"❌ Error processing PDF with {method} method: {e}")
            raise