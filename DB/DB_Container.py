from dependency_injector import containers, providers
from text_rag import DataBaseConnection, DataBaseCreate, RAG

class Container(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=["init_config.yml"])

    db_conn = providers.Singleton(
        DataBaseConnection,
        db_arg=config.database,
        minconn=1,
        maxconn=10
    )

    db_create = providers.Factory(
        DataBaseCreate,
        db_connection=db_conn
    )
    
    rag = providers.Factory(
        RAG,
        db_connection=db_conn
    )