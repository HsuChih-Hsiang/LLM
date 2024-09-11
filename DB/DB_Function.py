import torch
import PyPDF2
from enum import Enum
import psycopg2.extras
from psycopg2.extensions import connection, cursor
from psycopg2.pool import SimpleConnectionPool
from typing import Dict, Type, List, Callable, Any, Union
from sentence_transformers import SentenceTransformer
from DB_Enum import RAG_COMMAND, DB_EXTENSION, DB_TABLE, CREATE_TABLE_COMMAND, DB_TABLE_COMMAND


class ReturnType(Enum):
    Dict = 1
    List = 2
    Raw = 3

class DataBaseUtility:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def db_conn_template(self, func: Callable) -> Callable:
        """_summary_
            裝飾器: 取得 conn pool 的連線, 並在執行完後收回
        """
        def wrapper(*args, **kwargs):
            conn = self.db.getconn()
            try:
                return func(self, conn, *args, **kwargs)
            finally:
                self.db.putconn(conn)
        return wrapper
    
    def db_get_data(self, return_type: ReturnType = ReturnType.Dict) -> Callable:
        """_summary_
            裝飾器: 執行 SQL , 並更改從資料庫取得的資料型態
            Raw: 使用原本 function 的回傳
            List: 資料庫回傳的資料型態
            Dict: 方便 API 做後續操作
        """
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
        """_summary_
            裝飾器: 執行 SQL , 並將資料儲存到資料庫
        """
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

class DataBaseCreate(DataBaseUtility):
    def __init__(self, db_connection: DataBaseConnection):
        super().__init__(db_connection)
        self.add_extension()
        if check := self.table_check(): 
            self.create_table(check)
            
    @DataBaseUtility.db_get_data(return_type=ReturnType.List)
    @DataBaseUtility.db_conn_template
    def table_list(self, cur: cursor) -> None:
        """_summary_
            用於取得目前資料庫所有的 table list
        """
        cur.execute(DB_TABLE_COMMAND)
        
    @DataBaseUtility.db_commit
    @DataBaseUtility.db_conn_template
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
                    self.create_table(create_command)
        
    @DataBaseUtility.db_commit
    @DataBaseUtility.db_conn_template
    def add_extension(self, cur: cursor) -> None:
        cur.execute(DB_EXTENSION.PGVECTOR)

    
class RAG(DataBaseUtility):
    def __init__(self, db_connection: DataBaseConnection) -> None:
        super().__init__(db_connection)
        self.model = SentenceTransformer('allenai/longformer-base-4096')
        self.max_seq_length = 4096
        self.embedding_dim = 768
    
    def encoding_text(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    def encoding_text(self, text: str) -> List[float]:
        if len(text.split()) <= self.max_seq_length:
            return self.model.encode(text).tolist()
        else:
            chunks = self.split_text(text)
            embeddings = [self.model.encode(chunk) for chunk in chunks]
            return torch.mean(torch.stack(embeddings), dim=0).tolist()

    def split_text(self, text: str, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.max_seq_length - overlap):
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
    @DataBaseUtility.db_conn_template
    def store_pdf(self, cur: cursor, pdf_path: str) -> None:
        pdf_path, embedding = self.deal_pdf(pdf_path)
        cur.execute(RAG_COMMAND.ADD_DOCUMENTS, (pdf_path, embedding))

    @DataBaseUtility.db_get_data(return_type=ReturnType.Raw)
    @DataBaseUtility.db_conn_template
    def retrieve_pdfs(self, cur: cursor, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.encoding_text(query)
        cur.execute(RAG_COMMAND.SEARCH_VECTOR, (query_embedding, limit))
        results = cur.fetchall()
        return [result[0] for result in results]
    