import torch
import PyPDF2
from psycopg2.extensions import cursor
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from Database.Util.Database_Function import DataBaseUtility, DataBaseConnection, ReturnType
from Database.Rag.Rag_Database_Enum import DocumentsCommand, RagCommand
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
    
class RAG(DataBaseUtility):
    def __init__(self, db_connection: DataBaseConnection) -> None:
        super().__init__(db_connection)
        self.model = SentenceTransformer('allenai/longformer-base-4096')
        self.max_seq_length = 4096
        self.embedding_dim = 768
        self.overlap = 50
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')

    def encoding_text(self, text: str) -> List[float]:
        if len(text.split()) <= self.max_seq_length:
            return self.model.encode(text).tolist()
        else:
            chunks = self.split_text(text)
            embeddings = [self.model.encode(chunk) for chunk in chunks]
            return torch.mean(torch.stack(embeddings), dim=0).tolist()
        
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        tfidf_matrix = self.tfidf_vectorizer.transform([text])
        feature_names = np.array(self.tfidf_vectorizer.get_feature_names_out())
        tfidf_scores = tfidf_matrix.toarray()[0]
        sorted_indices = np.argsort(tfidf_scores)[::-1]
        return list(feature_names[sorted_indices[:top_n]])

    def split_text(self, text: str) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.max_seq_length - self.overlap):
            chunk = ' '.join(words[i:i + self.max_seq_length])
            chunks.append(chunk)
        return chunks
    
    def pdf_dealer(self, doc: bytes|str):
        with open(doc, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = "".join(page.extract_text() for page in reader.pages)
        return pdf_file.name, text
        
    def deal_text(self, text: str) -> None:    
        chunks = self.split_text(text)
        chunk_data = []
        for chunk in chunks:
            embedding = self.encoding_text(chunk)
            keywords = self.extract_keywords(chunk)
            data = {
                "text": chunk,
                "embedding": embedding,
                "keywords": keywords
            }
            chunk_data.append(data)
        return chunk_data
        
    @DataBaseUtility.db_commit
    def store_text(self, cur: cursor, file_name:str, text: List[Dict], file_type: int = 0) -> None:
        cur.execute(DocumentsCommand.ADD_DOCUMENTS.value, {"file_name": file_name, "file_type": file_type})
        document_id = cur.fetchone()[0]
        for data in text:
            text, embedding, keywords = data["text"], data["embedding"], data["keywords"]
            cur.execute(RagCommand.INSERT_DOCUMENT_CHUNK.value, {"document_id": document_id, "chunk_text": text})
            chunk_id = cur.fetchone()[0]
            cur.execute(RagCommand.INSERT_DOCUMENT_EMBEDDING.value, {"chunk_id": chunk_id, "embedding": embedding, "keywords": keywords})

    @DataBaseUtility.db_get_data(return_type=ReturnType.OneDimList)
    def retrieve_text(self, cur: cursor, query: str, limit: int = 5, ratio: float = 0.5) -> List:
        """
            搜尋最相關的 pdf
        """
        query_embedding = self.encoding_text(query)
        query_keywords = self.extract_keywords(query)
        cur.execute(RagCommand.SEARCH_VECTOR.value, {"embedding": query_embedding, "keywords": query_keywords, "ratio": ratio, "limit": limit})

    async def generate_response(self, query: str, context: List[str]) -> str:
        """
            base on context generate response
        """
        combined_context = " ".join(context)
        prompt = f"""基於以下上下文回答問題：\n\n上下文：{combined_context}\n\n問題：{query}\n\n回答："""
    
        return prompt

    async def rag_pipeline(self, query: str) -> str:
        """
            完整的 RAG 流程
        """
        relevant_chunks = self.retrieve_text(query)
        response = self.generate_response(query, relevant_chunks)
        return response