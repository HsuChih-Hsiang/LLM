from enum import Enum
from typing import Dict, Type, List, Any
from dependency_injector import containers, providers
from psycopg2.extensions import connection
from psycopg2.pool import SimpleConnectionPool
from sentence_transformers import SentenceTransformer
import PyPDF2
import yaml



class DB_extension(Enum):
    extand = "SELECT * FROM pg_extension where extname = "
    
    def __str__(self):
        pass

class DB_table(Enum):
    documents = ""
    
    
class DB_create():
    def __init__(self, db_connection):
        self.db = db_connection
        _is_init: bool = None
        if not _is_init and self.extend_check() and self.table_check():
            self.add_extension()
            self.create_table()

    def db_conn_templete(self, func):
        def wrapper(*args, **kwargs):
            conn = self.db.getconn()
            try:
                return func(self, conn, *args, **kwargs)
            finally:
                self.db.putconn(conn)
        return wrapper

    @db_conn_templete
    def extend_check(self, conn: connection) -> Dict:
        with conn.cursor() as cur:
            cur.execute("", return_dict=True)
            extend_exist = self.conn.fetchall()
        return extend_exist

    @db_conn_templete
    def table_check(self, conn: connection) -> Dict:
        with conn.cursor() as cur:
            cur.execute("", return_dict=True)
            table_exist = self.conn.fetchall()
        return table_exist

    @db_conn_templete
    def create_table(self, conn: connection, table: Dict) -> None:
        with conn.cursor() as cur:
            cur.execute("", return_dict=True)
            self.conn.commit()

    @db_conn_templete
    def add_extension(self, conn: connection, extension: Dict) -> None:
        with conn.cursor() as cur:
            cur.execute("", return_dict=True)
            self.conn.commit()
            

class DB_CONN:
    _instance: Type["DB_CONN"] = None
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
    
    @classmethod
    def getconn(self) -> connection:
        return self.pool.getconn()
    
    @classmethod
    def putconn(self, conn: connection) -> None:
        self.pool.putconn(conn)
        
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    db_conn = providers.Singleton(
        DB_CONN
    )

    db_create = providers.Factory(
        DB_create,
        db=db_conn
    )
    
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