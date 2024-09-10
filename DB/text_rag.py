from typing import Dict, Type, List, Callable, Any, Union
import psycopg2.extras
from psycopg2.extensions import connection, cursor
from psycopg2.pool import SimpleConnectionPool
from sentence_transformers import SentenceTransformer
import PyPDF2
from DB_Enum import RAG_COMMAND, DB_EXTENSION
from enum import Enum
from DB.DB_Enum import DB_TABLE, CREATE_TABLE_COMMAND, DB_TABLE_COMMAND

class ReturnType(Enum):
    Dict = 1
    List = 2
    Raw = 3


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
    
    def db_get_data(self, return_type: ReturnType = ReturnType.Dict) -> Callable:
        def decorator(func: Callable) -> Callable:
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
        if check := self.table_check(): 
            self.create_table(check)
            
    @DataBaseUtility.db_get_data(return_type=ReturnType.List)
    @DataBaseUtility.db_conn_template
    def table_list(self, cur: cursor) -> None:
        cur.execute(DB_TABLE_COMMAND)
        
    @DataBaseUtility.db_commit
    @DataBaseUtility.db_conn_template
    def create_table(self, cur: cursor, table_command: str) -> None:
        cur.execute(table_command)
        
    def create_init_table(self, table_list: List):
        for table in DB_TABLE:
            if table.value not in table_list:
                create_command = getattr(CREATE_TABLE_COMMAND, table.name, None)
                if create_command:
                    self.create_table(create_command)
        
    @DataBaseUtility.db_commit
    @DataBaseUtility.db_conn_template
    def add_extension(self, cur: cursor) -> None:
        cur.execute(DB_EXTENSION.PGVECTOR)

    
class RAG(DataBaseUtility):
    def __init__(self, db_connection: DataBaseConnection) -> None:
        super().__init__(db_connection)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def encoding_text(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    @DataBaseUtility.db_commit
    @DataBaseUtility.db_conn_template
    def store_pdf(self, cur: cursor, pdf: bytes) -> None:       
        with open(pdf, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = "".join(page.extract_text() for page in reader.pages)

        embedding = self.encoding_text(text)
        cur.execute(RAG_COMMAND.ADD_DOCIMENTS, (text, embedding))

    @DataBaseUtility.db_get_data(return_type=ReturnType.Raw)
    @DataBaseUtility.db_conn_template
    def retrieve_pdfs(self, cur: cursor, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.encoding_text(query)
        cur.execute(RAG_COMMAND.SEARCH_VECTOR, (query_embedding, limit))
        results = cur.fetchall()
        return [result[0] for result in results]
    