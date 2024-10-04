from dependency_injector import containers, providers
from Database.Util.Database_Function import DataBaseConnection, DataBaseCreate
from Database.Rag.Retrieval_Augmented_Generation import RAG

class DataBaseContainer(containers.DeclarativeContainer):
    config_path =  "init_config.yml"
    config = providers.Configuration()
    config.from_yaml(config_path, required=True)

    db_conn = providers.Singleton(
        DataBaseConnection,
        db_arg=config.db_config,
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