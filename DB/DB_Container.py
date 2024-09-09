from dependency_injector import containers, providers
from text_rag import DB_CONN, DB_CREATE, RAG

class Container(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=["init_config.yml"])

    db_conn = providers.Singleton(
        DB_CONN,
        db_arg=config.database,
        minconn=1,
        maxconn=10
    )

    db_create = providers.Factory(
        DB_CREATE,
        db_connection=db_conn
    )
    
    rag = providers.Factory(
        RAG,
        db_connection=db_conn
    )