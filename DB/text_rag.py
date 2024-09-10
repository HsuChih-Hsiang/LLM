from typing import Dict, Type, List, Callable, Any
import psycopg2.extras
from psycopg2.extensions import connection, cursor
from psycopg2.pool import SimpleConnectionPool
from sentence_transformers import SentenceTransformer
import PyPDF2

class DataBaseUtility:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def db_conn_template(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            conn = self.db.getconn()
            try:
                return func(self, conn, *args, **kwargs)
            finally:
                self.db.putconn(conn)
        return wrapper
    
    def db_trans_dict(self, func: Callable) -> Callable:
        def wrapper(self, conn: connection, *args, **kwargs):
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                func(self, cursor, *args, **kwargs)
                result = cursor.fetchall()
                return [dict(row) for row in result] if result else []
        return wrapper
    
    def db_commit(self, func: Callable) -> Callable:
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
            cls.pool = SimpleConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                **db_arg
            )
        return cls._instance

    @classmethod
    def getconn(cls) -> connection:
        return cls.pool.getconn()

    @classmethod
    def putconn(cls, conn: connection) -> None:
        cls.pool.putconn(conn)

class DataBaseCreate(DataBaseUtility):
    def __init__(self, db_connection: DataBaseConnection):
        super().__init__(db_connection)
        self.add_extension()
        if not self.table_check(): 
            self.create_table()
            
    @DataBaseUtility.db_trans_dict
    @DataBaseUtility.db_conn_template
    def table_list(self, cur: cursor) -> None:
        cur.execute("SELECT * FROM information_schema.tables")
        
    @DataBaseUtility.db_commit
    @DataBaseUtility.db_conn_template
    def create_table(self, cur: cursor, table_command: str) -> None:
        cur.execute(table_command)
        
    @DataBaseUtility.db_commit
    @DataBaseUtility.db_conn_template
    def add_extension(self, cur: cursor) -> None:
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgvector")

    
class RAG(DataBaseUtility):
    def __init__(self, db_connection: DataBaseConnection) -> None:
        super().__init__(db_connection)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    @staticmethod
    def encoding_text(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    @DataBaseUtility.db_commit
    @DataBaseUtility.db_conn_template
    def store_pdf(cls, cur: cursor, pdf: bytes) -> None:       
        with open(pdf, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = "".join(page.extract_text() for page in reader.pages)

        embedding = cls.encoding_text(text)
        cur.execute("INSERT INTO documents (file_name, embedding) VALUES (%s, %s)", (text, embedding))

    @DataBaseUtility.db_trans_dict
    @DataBaseUtility.db_conn_template
    def retrieve_pdfs(cls, cur: cursor, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_embedding = cls.encoding_text(query)
        cur.execute("SELECT pdf_path FROM documents ORDER BY embedding <-> %s LIMIT %s", (query_embedding, limit))
        results = cur.fetchall()
        return [result[0] for result in results]
    