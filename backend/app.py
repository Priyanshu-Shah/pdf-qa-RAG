from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
from dotenv import load_dotenv
import config
from utils.pdf_processor import PDFProcessor
from utils.vector_store import VectorStoreService
from utils.llm_service import LLMService
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)
CORS(app)

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

"""
The flask backend has the following routes:
1. /api/upload: Upload a PDF file and process it. (use the pdf_processor to extract text and chunk it)
2. /api/chat: Send a message to the LLM and get a response based on the uploaded files.
3. /api/files: Get a list of all uploaded files. (to display on the side collumn)
4. /api/files/<file_id>: Delete a file from storage and vector database.
"""

# @app.route('/api/upload', methods=['POST'])
# def upload_pdf():
#     # We will first save the pdf, update metadata, extarct chunks, and chunk mapping, and add those to the vector store
#     try:
#         # Save pdf
#         pdf_file = request.files['pdf']
#         file_info = pdf_processor.save_pdf(pdf_file)
#         # Update metadata with the current date
#         file_info['dateUploaded'] = datetime.now().isoformat()
        
#         # Process the PDF (extract text, chunk, etc.)
#         chunks, chunk_page_map, updated_file_info = pdf_processor.process_pdf(file_info)
#         # Add to vector store
#         if chunks and updated_file_info["status"] == "processed":
#             vector_store.add_file(updated_file_info, chunks, chunk_page_map)
        
#         # Return file info to frontend to show the file size, path and such
#         return jsonify({
#             "fileId": updated_file_info["id"],
#             "filename": updated_file_info["name"],
#             "size": updated_file_info["size"],
#             "data": {
#                 "pages": updated_file_info.get("pages", 0),
#                 "processed": updated_file_info["status"] == "processed",
#                 "error": updated_file_info.get("error", None)
#             }
#         })
    
#     except Exception as e:
#         logger.error(f"Error uploading file: {e}")
#         return jsonify({"error": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    try:
        # Check if file was provided
        if 'pdf' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        pdf_file = request.files['pdf']
        
        # Check if file has name
        if pdf_file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Check file extension
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Only PDF files are allowed"}), 400
        
        # Get processing method from request
        processing_method = request.form.get('method', 'standard')
        logger.info(f"Using processing method: {processing_method}")
        
        # Save the file and get basic info
        file_info = pdf_processor.save_pdf(pdf_file)
        file_info['dateUploaded'] = datetime.now().isoformat()
        
        # Process the PDF with the specified method
        chunks, chunk_page_map, updated_file_info = pdf_processor.process_pdf(file_info, processing_method)
        
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
                "error": updated_file_info.get("error", None),
                "method": updated_file_info.get("processing_method", "standard")
            }
        })
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    # The chat route just takes a message and a list of file IDs, and returns the response from the LLM
    try:
        # Get request data (which has our message and the file_ids)
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        message = data.get('message', '')
        file_ids = data.get('fileIds', [])
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Check if file IDs even exist in the vector store
        valid_file_ids = []
        for file_id in file_ids:
            if vector_store.get_file_metadata(file_id):
                valid_file_ids.append(file_id)
        
        if not valid_file_ids:
            return jsonify({
                "text": "No valid documents selected. Please upload and select at least one document.",
                "sources": []
            })
        
        # Query vector store to find relevant chunks from the vector store based on the message and file IDs
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
    #This returns a list of all files in the vector store, along with their metadata
    # This is useful for the frontend to show the files in the side column and for the querying process
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
    try:
        # Ensure that the file exists
        file_info = vector_store.get_file_metadata(file_id)
        if not file_info:
            logger.warning(f"File not found: {file_id}")
            return jsonify({"error": "File not found", "fileId": file_id}), 404
        
        # Remove from vector store
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