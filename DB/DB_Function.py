import torch
import PyPDF2
from enum import Enum
import psycopg2.extras
from llm_model import LLM_MODEL
from psycopg2.extensions import connection, cursor
from psycopg2.pool import SimpleConnectionPool
from typing import Dict, Type, List, Callable, Any, Union
from sentence_transformers import SentenceTransformer
from DB.DB_Enum import RAG_COMMAND, DB_TABLE, CREATE_TABLE_COMMAND, DB_TABLE_COMMAND
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


class ReturnType(Enum):
    Dict = 1
    List = 2
    Raw = 3

class DataBaseUtility:
    def __init__(self, db_connection):
        self.db = db_connection
    
    @classmethod
    def db_conn_template(cls, func: Callable) -> Callable:
        """_summary_
            裝飾器: 取得 conn pool 的連線, 並在執行完後收回
        """
        def wrapper(self, *args, **kwargs):
            conn = self.db.getconn()
            try:
                return func(self, conn, *args, **kwargs)
            finally:
                self.db.putconn(conn)
        return wrapper
    
    @classmethod
    def db_get_data(cls, return_type: ReturnType = ReturnType.Dict) -> Callable:
        """_summary_
            裝飾器: 執行 SQL , 並更改從資料庫取得的資料型態
            Raw: 使用原本 function 的回傳
            List: 資料庫回傳的資料型態
            Dict: 方便 API 做後續操作
        """
        def decorator(func: Callable) -> Callable:
            @cls.db_conn_template
            def wrapper(self, conn: connection, *args, **kwargs) -> Union[List[Dict[str, Any]], List[Any], Any]:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    result = func(self, cursor, *args, **kwargs)
                    
                    if return_type == ReturnType.Raw:
                        return result
                    if return_type in (ReturnType.Dict, ReturnType.List):
                        fetched = cursor.fetchall()
                        if return_type == ReturnType.Dict:
                            return [dict(row) for row in fetched]
                        return [list(row) for row in fetched]
                    
            return wrapper
        return decorator
    
    @classmethod
    def db_commit(cls, func: Callable) -> Callable:
        """_summary_
            裝飾器: 執行 SQL , 並將資料儲存到資料庫
        """
        @cls.db_conn_template
        def wrapper(self, conn: connection, *args, **kwargs):
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                func(self, cursor, *args, **kwargs)
                conn.commit()
        return wrapper

class DataBaseConnection:
    _instance: Type["DataBaseConnection"] = None
    pool: SimpleConnectionPool = None

    def __new__(cls, db_arg: Dict[str, str], minconn: int = 1, maxconn: int = 10) -> Type["DataBaseConnection"]:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance = super().__new__(cls)
            if db_arg is None:
                raise ValueError("Database connection parameters are not provided")
            cls.pool = SimpleConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                **db_arg
            )
        return cls._instance

    @classmethod
    def getconn(cls) -> connection:
        """_summary_
            從 SimpleConnectionPool 取得於資料庫的連線
        """
        return cls.pool.getconn()

    @classmethod
    def putconn(cls, conn: connection) -> None:
        """_summary_
            將與資料庫的連線放回 SimpleConnectionPool
        """
        cls.pool.putconn(conn)
        
    @classmethod
    def closeall(cls) -> None:
        """
            關閉所有的資料庫連線
        """
        if cls.pool:
            cls.pool.closeall()
            cls.pool = None

class DataBaseCreate(DataBaseUtility):
    def __init__(self, db_connection: DataBaseConnection):
        super().__init__(db_connection)
        existing_tables = self.table_list()
        self.create_init_table(existing_tables)
            
    @DataBaseUtility.db_get_data(return_type=ReturnType.List)
    def table_list(self, cur: cursor) -> None:
        """_summary_
            用於取得目前資料庫所有的 table list
        """
        cur.execute(DB_TABLE_COMMAND.CHECK.value)
        
    @DataBaseUtility.db_commit
    def create_table(self, cur: cursor, table_command: str) -> None:
        """_summary_
            依指令建立 table
        """
        cur.execute(table_command)
        
    def create_init_table(self, table_list: List):
        for table in DB_TABLE:
            if table.value not in table_list:
                create_command = getattr(CREATE_TABLE_COMMAND, table.name, None)
                if create_command:
                    self.create_table(create_command.value)
    
class RAG(DataBaseUtility):
    def __init__(self, db_connection: DataBaseConnection) -> None:
        super().__init__(db_connection)
        self.model = SentenceTransformer('allenai/longformer-base-4096')
        self.max_seq_length = 4096
        self.embedding_dim = 768
        self.overlap = 50
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        self.llm = LLM_MODEL()

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

    def deal_pdf(self, pdf_path: str) -> None:       
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = "".join(page.extract_text() for page in reader.pages)
        embedding = self.encoding_text(text)
        return pdf_path, embedding
        
    @DataBaseUtility.db_commit
    def store_pdf(self, cur: cursor, pdf_path: str) -> None:
        pdf_path, embedding = self.deal_pdf(pdf_path)
        cur.execute(RAG_COMMAND.ADD_DOCUMENTS.value, (pdf_path, embedding))

    @DataBaseUtility.db_get_data(return_type=ReturnType.Raw)
    def retrieve_pdfs(self, cur: cursor, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.encoding_text(query)
        query_keywords = self.extract_keywords(query)
        cur.execute(RAG_COMMAND.SEARCH_VECTOR.value, (query_embedding, query_keywords, limit))
        results = cur.fetchall()
        return [result[0] for result in results]
    
    def search(self, query: str, limit: int = 5) -> List[str]:
        """
            搜尋最相關的 pdf
        """
        relevant_chunks = self.retrieve_pdfs(query, limit)
        return relevant_chunks

    async def generate_response(self, query: str, context: List[str]) -> str:
        """
            base on context generate response
        """
        combined_context = " ".join(context)
        prompt = f"""基於以下上下文回答問題：\n\n上下文：{combined_context}\n\n問題：{query}\n\n回答："""
        
        conversion, streamer = self.llm.generater_response(prompt)
        
        full_response = ""
        for new_text in streamer:
            output = new_text.replace(conversion, '')
            if output:
                full_response += output
        return full_response

    async def rag_pipeline(self, query: str) -> str:
        """
            完整的 RAG 流程
        """
        relevant_chunks = self.search(query)
        response = await self.generate_response(query, relevant_chunks)
        return response
    