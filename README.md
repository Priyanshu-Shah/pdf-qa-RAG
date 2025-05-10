# PDF Question-Answering System with RAG

## Overview
This project implements a document-based question answering system using the Retrieval Augmented Generation (RAG) approach. Users can upload PDF documents, which are processed and stored in a vector database. The system then answers questions based on the content of these documents, providing source references for verification.

## Key Features

### 1. PDF Upload and Management
- Upload single or multiple PDF files
- Display PDF thumbnails and metadata
- Document deletion functionality
- Document status tracking (uploading, processing, error states)

### 2. PDF Processing Methods
- **Standard Processing**: Basic text extraction using PyPDF
- **Layout Processing**: OCR-based extraction with layout awareness using pytesseract
- Processing method selection before upload
- Automatic fallback to simpler methods if advanced processing fails

### 3. Vector Database Storage
- Text chunking using various strategies (recursive, markdown-aware)
- Embedding generation using Hugging Face models
- Storage in ChromaDB for semantic search capabilities
- Document-page mapping for source attribution

### 4. Semantic Search
- Query embedding and similarity search
- Filtering by selected documents
- Relevance ranking of retrieved chunks
- Smart chunk retrieval based on semantic similarity rather than keyword matching

### 5. AI Response Generation
- Context-based answer generation using Google's Gemini model
- Source attribution linking to specific documents and pages
- Controls to prevent hallucinations by limiting the model to only use provided context

### 6. Interactive Chat Interface
- Real-time chat with the document collection
- Message history preservation
- Source citation for each response
- Visual indicators for processing states

## Technical Implementation

### Frontend (React)
- **File Context**: Manages document upload, processing status, and method selection
- **Chat Context**: Handles message history, document selection, and query processing
- **Components**:
  - `DocumentSidebar`: For file uploading and management
  - `ChatInterface`: For question input and response display
  - `ProcessingMethodSelector`: For choosing PDF processing method
  - `PDFThumbnail`: For document previews using PDF.js
  - `MessageBubble`: For displaying chat messages with source attribution

### Backend (Flask)
- **PDF Processor**: 
  - Extracts text using different methods (PyPDF, unstructured, pytesseract)
  - Chunks text using appropriate strategies
  - Maps chunks to source pages for attribution
  
- **Vector Store Service**:
  - Creates and manages the ChromaDB vector database
  - Handles document embedding and storage
  - Provides semantic search functionality
  - Manages document metadata and access logs

- **LLM Service**:
  - Interfaces with Google's Gemini model
  - Constructs prompts with context from retrieved chunks
  - Formats responses with source attribution

### API Endpoints
- `/api/upload`: For PDF file uploads with processing method selection
- `/api/chat`: For sending queries and receiving AI responses
- `/api/files`: For listing and managing uploaded documents

### Data Flow
1. User uploads PDF document with selected processing method
2. Backend processes the document and extracts text
3. Text is chunked, embedded, and stored in vector database
4. User asks a question through chat interface
5. System retrieves relevant chunks from vector database
6. LLM generates a response based on retrieved context
7. Response is displayed to user with source attribution

## Technology Stack
- **Frontend**: React, JavaScript, CSS
- **Backend**: Flask, Python
- **PDF Processing**: PyPDF, Unstructured, pytesseract, pdf2image
- **Vector Database**: ChromaDB
- **Embeddings**: Hugging Face sentence-transformers
- **LLM**: Google Gemini through langchain-google-genai
- **Development**: Vite, dotenv

## System Requirements
- Python 3.8+ with required packages from `backend/requirements.txt`
- Node.js and npm for frontend
- Tesseract OCR installation for layout processing
- Poppler for PDF to image conversion
- Google Gemini API key for LLM responses

## Summary
This PDF-QA-RAG system demonstrates an effective implementation of retrieval-augmented generation for document question answering, combining modern NLP techniques with practical document processing to provide accurate, source-attributed responses to user queries.