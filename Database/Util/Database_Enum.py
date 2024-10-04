from enum import Enum

class DatabaseTable(Enum):
    DOCUMENTS_TYPE = "documents_type"
    DOCUMENTS = "documents"
    DOCUMENTS_CHUNKS = "document_chunks"
    DOCUMENTS_EMBEDDING = "documents_embedding"
    
    
class CreateTableCommand(Enum):
    DOCUMENTS_TYPE = """
    CREATE TABLE documents_type (
        id SERIAL PRIMARY KEY,
        file_type_name TEXT NOT NULL
    );
    
    INSERT INTO documents_type (file_type_name) VALUES ('undefined');
    INSERT INTO documents_type (file_type_name) VALUES ('pdf');
    INSERT INTO documents_type (file_type_name) VALUES ('text');
    """
    
    DOCUMENTS = """
    CREATE TABLE documents (
        id SERIAL PRIMARY KEY,
        file_name TEXT NOT NULL,
        file_type INTEGER NOT NULL references documents_type(id) default 0
        );
    """
    
    DOCUMENTS_CHUNKS = """
    CREATE TABLE document_chunks (
        id SERIAL PRIMARY KEY,
        document_id INTEGER NOT NULL references documents(id),
        chunk_text TEXT
        );
    """
    
    DOCUMENTS_EMBEDDING = """
    CREATE TABLE documents_embedding (
        id SERIAL PRIMARY KEY,
        chunk_id INTEGER NOT NULL references document_chunks(id),
        embedding vector(768),
        keywords TEXT[]
    );
    """

class DatabaseTableCommand(Enum):
    CHECK = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    
class DatabaseExtension(Enum):
    PGVECTOR = "CREATE EXTENSION IF NOT EXISTS vector"
    