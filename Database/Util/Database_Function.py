from enum import Enum
import psycopg2.extras
from psycopg2.extensions import connection, cursor
from psycopg2.pool import SimpleConnectionPool
from typing import Dict, Type, List, Callable, Any, Union
from Database.Util.Database_Enum import DatabaseTable, CreateTableCommand, DatabaseTableCommand, DatabaseExtension


class ReturnType(Enum):
    Dict = 1
    List = 2
    OneDimList = 3
    Raw = 4

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
                    
                    elif return_type in (ReturnType.Dict, ReturnType.List, ReturnType.OneDimList):
                        fetched = cursor.fetchall()
                        if not fetched:
                            return []
                    
                        elif return_type == ReturnType.Dict:
                            column_names = [desc[0] for desc in cursor.description]
                            return [dict(zip(column_names, row)) for row in fetched]
                        
                        elif return_type == ReturnType.List:
                            return [list(row) for row in fetched]
                        
                        elif return_type == ReturnType.OneDimList:
                            return [row[0] for row in fetched]
                    
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
        self.add_extension()
        existing_tables = self.table_list()
        self.create_init_table(existing_tables)
            
    @DataBaseUtility.db_get_data(return_type=ReturnType.List)
    def table_list(self, cur: cursor) -> None:
        """_summary_
            用於取得目前資料庫所有的 table list
        """
        cur.execute(DatabaseTableCommand.CHECK.value)
        
    @DataBaseUtility.db_commit
    def create_table(self, cur: cursor, table_command: str) -> None:
        """_summary_
            依指令建立 table
        """
        cur.execute(table_command)
    
    @DataBaseUtility.db_commit
    def add_extension(self, cur: cursor) -> None:
        cur.execute(DatabaseExtension.PGVECTOR.value)
        
    def create_init_table(self, table_list: List):
        for table in DatabaseTable:
            if table.value not in table_list:
                create_command = getattr(CreateTableCommand, table.name, None)
                if create_command:
                    self.create_table(create_command.value)
    