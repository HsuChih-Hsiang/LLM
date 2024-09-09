from enum import Enum
from typing import Dict, Type, List, Any
from dependency_injector import containers, providers
from psycopg2.extensions import connection
from psycopg2.pool import SimpleConnectionPool
from sentence_transformers import SentenceTransformer
import PyPDF2



class DB_extension(Enum):
    PGVECTOR = "pgvector"

class DB_table(Enum):
    DOCUMENTS = "documents"
       
class DB_UTILITY:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def db_conn_template(self, func):
        def wrapper(*args, **kwargs):
            conn = self.db.getconn()
            try:
                return func(self, conn, *args, **kwargs)
            finally:
                self.db.putconn(conn)
        return wrapper
    
    
class DB_create(DB_UTILITY):
    def __init__(self, db_connection):
        super().__init__(db_connection)
        if self.extend_check() and self.table_check():
            self.add_extension()
            self.create_table()

    @DB_UTILITY.db_conn_template
    def extend_check(self, conn: connection) -> Dict:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM pg_extension")
            extend_exist = cur.fetchall()
        return extend_exist

    @DB_UTILITY.db_conn_template
    def table_check(self, conn: connection) -> Dict:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM information_schema.tables")
            table_exist = cur.fetchall()
        return table_exist

    @DB_UTILITY.db_conn_template
    def create_table(self, conn: connection) -> None:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS your_table_name (
                    id SERIAL PRIMARY KEY,
                    column1 TEXT,
                    column2 INTEGER
                )
            """)
            conn.commit()

    @DB_UTILITY.db_conn_template
    def add_extension(self, conn: connection) -> None:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgvector")
            conn.commit()

class DB_CONN:
    _instance: Type["DB_CONN"] = None
    pool: SimpleConnectionPool = None

    def __new__(cls, db_arg: Dict[str, str], minconn: int = 1, maxconn: int = 10) -> Type["DB_CONN"]:
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

class Container(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=["init_config.yml"])

    db_conn = providers.Singleton(
        DB_CONN,
        db_arg=config.database,
        minconn=1,
        maxconn=10
    )

    db_create = providers.Factory(
        DB_create,
        db_connection=db_conn
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
    @DB_UTILITY.db_conn_template
    def store_pdf(cls, conn: connection, pdf: bytes) -> None:
        with open(pdf, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()

        embedding = cls.encoding_text(text)
        
        with conn.cursor() as cur:
            cur.execute("INSERT INTO documents (file_name, embedding) VALUES (%s, %s)", (text, embedding))
            cls.conn.commit()
       

    @classmethod
    @DB_UTILITY.db_conn_template
    def retrieve_pdfs(cls, conn: connection, query: str) -> List:
        query_embedding = cls.encoding_text(query)
        
        with conn.cursor() as cur:
            cur.execute("SELECT pdf_path FROM documents ORDER BY embedding <-> %s LIMIT 5", (query_embedding))
            results = cur.fetchall()

        return [result[0] for result in results]