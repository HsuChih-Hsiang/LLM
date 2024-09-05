import psycopg2
from psycopg2.extensions import connection
from sentence_transformers import SentenceTransformer
import PyPDF2
from typing import Dict

class DB_CONN():
    _instance = None
    conn = None

    db_arg: Dict[str, str] = {
        "database": "NTU_LLM",
        "user": "",
        "password": "",
        "host": "140.112.3.52",
        "port": "5432"
    }

    def __new__(cls):
        if cls._instance is None and cls.conn is None:
            cls._intance = super().__new__(cls) 
            cls.conn = cls.connect(cls.db_arg)

        return cls.conn
    
    def __init__(self):
        pass
    
    @property
    def connect(self, max_retries=3, retry_delay=5, **kwargs):
        for time in range(max_retries):
            try:
                conn = psycopg2.connect(**kwargs)
            except psycopg2.OperationalError as e:
                time.sleep(retry_delay)
        return conn
    
class RAG():
    
    def __init__(self) -> None:
        self.conn = DB_CONN().conn
    
    @staticmethod
    def encoding_text(text: str):
        # 向量化
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding = model.encode(text).tolist()
        return embedding

    @classmethod
    def store_pdf(cls, pdf: bytes):
        # 提取 PDF 文本
        with open(pdf, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()

        embedding = cls.encoding_text(text)

        cur = cls.conn.cursor()
        cur.execute("INSERT INTO documents (text, embedding, pdf_path) VALUES (%s, %s, %s)", (text, embedding, pdf))
        cls.conn.commit()
        cur.close()

    # 搜尋相關 PDF
    @classmethod
    def retrieve_pdfs(cls, query: str):
        query_embedding = cls.encoding_text(query)
        cur = cls.conn.cursor()
        cur.execute("SELECT pdf_path FROM documents ORDER BY embedding <-> %s LIMIT 5", (query_embedding,))
        results = cur.fetchall()
        cur.close()
        return [result[0] for result in results]