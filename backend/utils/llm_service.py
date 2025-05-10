import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, gemini_api_key):
        self.gemini_api_key = gemini_api_key
        self._initialize_llm()
    
    def _initialize_llm(self):
        try:
            genai.configure(api_key=self.gemini_api_key)
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=self.gemini_api_key,
                temperature=0,
                convert_system_message_to_human=True
            )
            logger.info("Gemini LLM initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gemini LLM: {e}")
            raise
    
    # def generate_response(self, query, context_docs):
    #     try:
    #         if not context_docs:
    #             logger.warning("No context documents provided for query")
    #             return {
    #                 "text": "I couldn't find any relevant information in your documents to answer this question.",
    #                 "sources": []
    #             }
            
    #         # Create context from retrieved documents
    #         context = "\n\n---\n\n".join([doc["content"] for doc in context_docs])
            
    #         # Create source references
    #         sources = []
    #         chunk_counts = {}  # Track count of each document

    #         for i, doc in enumerate(context_docs):
    #             meta = doc.get("metadata", {})
    #             file_id = meta.get("file_id", "")
    #             file_name = meta.get("file_name", meta.get("filename", "Unknown Document"))
    #             page = meta.get("page", None)

    #             # Track chunks from each file to number them
    #             if file_name not in chunk_counts:
    #                 chunk_counts[file_name] = 0
    #             chunk_counts[file_name] += 1
                
    #             # Add the chunk number to the filename
    #             numbered_title = f"{file_name} ({chunk_counts[file_name]})"
                
    #             source_entry = {
    #                 "fileId": file_id,
    #                 "title": numbered_title,
    #                 "originalName": file_name
    #             }
                
    #             if page is not None:
    #                 source_entry["page"] = page
                    
    #             sources.append(source_entry)

            
    #         # Create prompt with context and the query, the context consists of the documents retrieved from the vector store, the query is the question asked by the user
    #         system_prompt = """You are an AI assistant that answers questions based on provided documents.
    #         Use ONLY the information in the context provided to answer the question.
    #         If the context doesn't contain the information needed, say you don't know or cannot find it in the documents.
    #         Provide a clear, concise answer that directly addresses the question.
    #         Do not make up information or draw from knowledge outside the provided context."""
            
    #         user_prompt = f"""Context:
    #         {context}
            
    #         Question: {query}
            
    #         Please provide an answer based only on the context above."""
            
    #         # In langchain we can provide separate messages for the system and user prompts
    #         messages = [
    #             SystemMessage(content=system_prompt),
    #             HumanMessage(content=user_prompt)
    #         ]

    #         # Generate response using the LLM using the invoke method of the ChatGoogleGenerativeAI library
    #         response = self.llm.invoke(messages)
            
    #         return {
    #             "text": response.content,
    #             "sources": sources
    #         }
        
    #     except Exception as e:
    #         logger.error(f"Error generating response from Gemini LLM: {e}")
    #         return {
    #             "text": "Sorry, I encountered an error while processing your question.",
    #             "sources": []
    #         }

    def generate_response(self, query, context_docs):
        try:
            if not context_docs:
                logger.warning("No context documents provided for query")
                return {
                    "text": "I couldn't find any relevant information in your documents to answer this question.",
                    "sources": []
                }
            
            # Create context from retrieved documents
            context = "\n\n---\n\n".join([doc["content"] for doc in context_docs])
            
            # First, get the relevance information for each document
            # We need to capture this before modifying the documents
            docs_with_info = []
            for i, doc in enumerate(context_docs):
                meta = doc.get("metadata", {})
                # Use the index position as a proxy for relevance score (lower index = higher relevance)
                # Vector search already returns most relevant first
                relevance_score = 1.0 - (i / max(len(context_docs), 1))  # Normalize to 0-1, higher is better
                
                docs_with_info.append({
                    "doc": doc,
                    "relevance": relevance_score,
                    "index": i  # Original position in results
                })
            
            # Sort by relevance score in descending order
            docs_with_info.sort(key=lambda x: x["relevance"], reverse=True)
            
            # Create source references with numbered chunks based on relevance
            sources = []
            chunk_counts = {}  # Track count of each document
            
            for info in docs_with_info:
                doc = info["doc"]
                meta = doc.get("metadata", {})
                file_id = meta.get("file_id", "")
                file_name = meta.get("file_name", meta.get("filename", "Unknown Document"))
                page = meta.get("page", None)
                
                # Track chunks from each file to number them
                if file_name not in chunk_counts:
                    chunk_counts[file_name] = 0
                chunk_counts[file_name] += 1
                
                # Format relevance score as percentage for display
                relevance_pct = int(info["relevance"] * 100)
                
                # Add the relevance percentage to the title
                numbered_title = f"{file_name} ({chunk_counts[file_name]})"
                
                source_entry = {
                    "fileId": file_id,
                    "title": numbered_title,
                    "originalName": file_name,
                    "relevance": info["relevance"]
                }
                
                if page is not None:
                    source_entry["page"] = page
                    
                sources.append(source_entry)
            
            # Rest of your function remains the same...
            system_prompt = """You are an AI assistant that answers questions based on provided documents.
            Use ONLY the information in the context provided to answer the question.
            If the context doesn't contain the information needed, say you don't know or cannot find it in the documents.
            Provide a clear, concise answer that directly addresses the question.
            Do not make up information or draw from knowledge outside the provided context."""
            
            user_prompt = f"""Context:
            {context}
            
            Question: {query}
            
            Please provide an answer based only on the context above."""
            
            # In langchain we can provide separate messages for the system and user prompts
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # Generate response using the LLM using the invoke method of the ChatGoogleGenerativeAI library
            response = self.llm.invoke(messages)
            
            return {
                "text": response.content,
                "sources": sources
            }
        
        except Exception as e:
            logger.error(f"Error generating response from Gemini LLM: {e}")
            return {
                "text": "Sorry, I encountered an error while processing your question.",
                "sources": []
            }