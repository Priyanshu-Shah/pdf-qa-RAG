import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self, vector_db_path, model_name="all-MiniLM-L6-v2"):
        self.vector_db_path = vector_db_path
        self._initialize_embeddings(model_name)
        self.db = None
        self.file_metadata = {}
        self.metadata_file = os.path.join(vector_db_path, "metadata.json")
        self._load_metadata()
        self._initialize_db()
    
    def _initialize_embeddings(self, model_name):
        """Initialize HuggingFace embeddings model"""
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info(f"HuggingFace embeddings initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Error initializing HuggingFace embeddings: {e}")
            raise
    
    def _initialize_db(self):
        """Initialize the vector database"""
        try:
            # Create or load the vector database
            self.db = Chroma(
                persist_directory=self.vector_db_path,
                embedding_function=self.embeddings
            )
            logger.info(f"Vector DB initialized with {self.db._collection.count()} documents")
        except Exception as e:
            logger.error(f"Error initializing vector DB: {e}")
            raise
    
    def _load_metadata(self):
        """Load file metadata from disk"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    self.file_metadata = json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                self.file_metadata = {}
    
    def _save_metadata(self):
        """Save file metadata to disk"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.file_metadata, f)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def add_file(self, file_info, chunks, chunk_page_map):
        """Add file chunks to the vector database"""
        try:
            # Create document metadatas for each chunk
            metadatas = []
            for chunk_info in chunk_page_map:
                chunk_pages = chunk_info["pages"]
                page = min(chunk_pages) if chunk_pages else None
                
                metadata = {
                    "file_id": file_info["id"],
                    "filename": file_info["name"],
                    "page": page
                }
                metadatas.append(metadata)
            
            # Add chunks to vector database
            chunks_text = [item["chunk"] for item in chunk_page_map]
            self.db.add_texts(
                texts=chunks_text,
                metadatas=metadatas
            )
            
            # Store file metadata
            self.file_metadata[file_info["id"]] = {
                "id": file_info["id"],
                "name": file_info["name"],
                "size": file_info["size"],
                "pages": file_info["pages"],
                "path": file_info["path"],
                "dateUploaded": file_info.get("dateUploaded", "")
            }
            
            # Save metadata to disk
            self._save_metadata()
            
            return True
        except Exception as e:
            logger.error(f"Error adding file to vector DB: {e}")
            return False
    
    def remove_file(self, file_id):
        """Remove a file from the vector database"""
        try:
            # Delete all chunks with this file_id from vector store
            self.db._collection.delete(
                where={"file_id": file_id}
            )
            
            # Remove from metadata
            if file_id in self.file_metadata:
                # Get file path before removing from metadata
                file_path = self.file_metadata[file_id].get("path")
                
                # Delete from metadata
                del self.file_metadata[file_id]
                self._save_metadata()
                
                # Delete the actual PDF file if it exists
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            
            return True
        except Exception as e:
            logger.error(f"Error removing file from vector DB: {e}")
            return False
    
    def get_file_metadata(self, file_id=None):
        """Get file metadata for one or all files"""
        if file_id:
            return self.file_metadata.get(file_id)
        return list(self.file_metadata.values())
    
    def query(self, query_text, file_ids=None, top_k=5):
        """Query the vector database for relevant chunks"""
        try:
            # Filter by file_ids if provided
            filter_dict = {}
            if file_ids and len(file_ids) > 0:
                filter_dict = {"file_id": {"$in": file_ids}}
            
            # Perform similarity search - note that with HF embeddings we use similarity_search
            # instead of similarity_search_with_relevance_scores
            results = self.db.similarity_search(
                query_text,
                k=top_k,
                filter=filter_dict if filter_dict else None
            )
            
            # Format results - since we don't have relevance scores directly, we'll
            # simply include all results with a default score
            formatted_results = []
            for i, doc in enumerate(results):
                # Assign decreasing relevance scores (dummy scores for compatibility)
                relevance = 1.0 - (i * 0.1)
                
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "relevance": relevance
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error querying vector DB: {e}")
            return []