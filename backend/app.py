from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Import config and utility modules
import config
from utils.pdf_processor import PDFProcessor
from utils.vector_store import VectorStoreService
from utils.llm_service import LLMService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize services
pdf_processor = PDFProcessor(
    pdf_storage_path=config.PDF_STORAGE_PATH,
    chunk_size=config.CHUNK_SIZE,
    chunk_overlap=config.CHUNK_OVERLAP
)

vector_store = VectorStoreService(
    vector_db_path=config.VECTOR_DB_PATH,
    model_name=config.HF_EMBEDDING_MODEL
)

llm_service = LLMService(
    gemini_api_key=config.GEMINI_API_KEY
)

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    try:
        pdf_file = request.files['pdf']
        file_info = pdf_processor.save_pdf(pdf_file)
        file_info['dateUploaded'] = datetime.now().isoformat()
        
        # Process the PDF (extract text, chunk, etc.)
        chunks, chunk_page_map, updated_file_info = pdf_processor.process_pdf(file_info)
        
        # Add to vector store
        if chunks and updated_file_info["status"] == "processed":
            vector_store.add_file(updated_file_info, chunks, chunk_page_map)
        
        # Return file info to client
        return jsonify({
            "fileId": updated_file_info["id"],
            "filename": updated_file_info["name"],
            "size": updated_file_info["size"],
            "data": {
                "pages": updated_file_info.get("pages", 0),
                "processed": updated_file_info["status"] == "processed",
                "error": updated_file_info.get("error", None)
            }
        })
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handle Q&A queries against uploaded documents
    """
    try:
        # Get request data
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        message = data.get('message', '')
        file_ids = data.get('fileIds', [])
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Validate file IDs
        valid_file_ids = []
        for file_id in file_ids:
            if vector_store.get_file_metadata(file_id):
                valid_file_ids.append(file_id)
        
        if not valid_file_ids:
            return jsonify({
                "text": "No valid documents selected. Please upload and select at least one document.",
                "sources": []
            })
        
        # Query vector store for relevant chunks
        context_docs = vector_store.query(message, valid_file_ids)
        
        # Generate response from LLM
        response = llm_service.generate_response(message, context_docs)
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return jsonify({
            "text": f"Error processing your request: {str(e)}",
            "sources": []
        }), 500

@app.route('/api/files', methods=['GET'])
def get_files():
    """
    Get list of all uploaded files
    """
    try:
        files = vector_store.get_file_metadata()
        
        # Format for frontend
        formatted_files = []
        for file in files:
            formatted_files.append({
                "id": file["id"],
                "name": file["name"],
                "size": file["size"],
                "dateUploaded": file.get("dateUploaded", "")
            })
        
        return jsonify(formatted_files)
    
    except Exception as e:
        logger.error(f"Error getting files: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """
    Delete a file from storage and vector database
    """
    try:
        # Log the request
        logger.info(f"Delete request received for file ID: {file_id}")
        
        # Check if file exists
        file_info = vector_store.get_file_metadata(file_id)
        if not file_info:
            logger.warning(f"File not found: {file_id}")
            # Return a 404 with a descriptive message
            return jsonify({"error": "File not found", "fileId": file_id}), 404
        
        # Remove from vector store (which also removes the PDF file)
        success = vector_store.remove_file(file_id)
        
        if success:
            return jsonify({
                "success": True,
                "fileId": file_id,
                "message": "File successfully deleted"
            })
        else:
            return jsonify({"error": "Failed to delete file"}), 500
    
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/')
def index():
    return jsonify({"message": "PDF Q&A API is running", "status": "ok"})

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)