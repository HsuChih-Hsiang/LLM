from typing import Dict, Type, List, Any
from psycopg2.extensions import connection
from psycopg2.pool import SimpleConnectionPool
from sentence_transformers import SentenceTransformer
import PyPDF2
import yaml


class DB_CONN:
    _instance: Type["DB_CONN"] = None
    _is_init: bool = None
    pool: SimpleConnectionPool = None

    db_arg: Dict[str, str] = yaml.safe_load("init_config.yml")["database"]

    def __new__(cls) -> Type["DB_CONN"]:
        if cls._instance is None:
            cls._intance = super().__new__(cls) 
            cls.pool = SimpleConnectionPool(
                minconn = 1,
                maxconn = 10,
                **cls.db_arg
            )
        return cls._instance
    
    def __init__(self):
        if not self._is_init:
            self.init_db()
        
    @property
    def init_db(self):
        conn = self.getconn()
        try:
            conn = self.getconn()
            
        except:
            with conn.cursor() as cur:
                cur.execute("")
                table_exist = self.conn.fetchall()
                
            if not table_exist:
                with conn.cursor() as cur:
                    cur.execute("")
                    table_exist = self.conn.commit()
            
        finally:
            self.db.putconn(conn)
            self._is_init = True
    
    @classmethod
    def getconn(self) -> connection:
        return self.pool.getconn()
    
    @classmethod
    def putconn(self, conn: connection) -> None:
        self.pool.putconn(conn)
    
class RAG:
    
    def __init__(self) -> None:
        self.db: type["DB_CONN"] = DB_CONN()
    
    @staticmethod
    def encoding_text(text: str) -> List | Any:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding = model.encode(text).tolist()
        return embedding

    @classmethod
    def store_pdf(cls, pdf: bytes) -> None:
        with open(pdf, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()

        embedding = cls.encoding_text(text)
        conn = cls.db.get_conn()

        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO documents (file_name, embedding) VALUES (%s, %s)", (text, embedding))
                cls.conn.commit()
        finally:
            cls.db.putconn(conn)

    @classmethod
    def retrieve_pdfs(cls, query: str) -> List:
        query_embedding = cls.encoding_text(query)
        conn = cls.db.get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT pdf_path FROM documents ORDER BY embedding <-> %s LIMIT 5", (query_embedding))
                results = cur.fetchall()
        finally:
            cls.db.putconn(conn)

        return [result[0] for result in results]