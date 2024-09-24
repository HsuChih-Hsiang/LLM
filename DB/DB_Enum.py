from enum import Enum

class DB_TABLE(Enum):
    DOCUMENTS = "documents"
    
class CREATE_TABLE_COMMAND(Enum):
    DOCUMENTS_TYPE = """
    CREATE TABLE IF NOT EXISTS documents_type (
        id SERIAL PRIMARY KEY,
        file_type_name TEXT NOT NULL,
    );
    
    INSERT INTO documents_type (file_type_name) VALUES ('undefined') ON CONFLICT (file_type_name) DO NOTHING;
    """
    
    DOCUMENTS = """
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        file_name TEXT NOT NULL,
        file_type INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (file_type_id) REFERENCES documents_type(id)
    )
    """
    DOCUMENTS_EMBEDDING = """
    CREATE TABLE IF NOT EXISTS documents_embedding (
        id SERIAL PRIMARY KEY,
        file_name TEXT NOT NULL,
        embedding vector(768),
        keywords TEXT[],
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )
    """
    
    SEARCH_VECTOR = """
    SELECT chunk_id FROM documents WHERE keywords && %s ORDER BY embedding <-> %s LIMIT %s
    """

class DB_TABLE_COMMAND(Enum):
    CHECK = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    
class RAG_COMMAND(Enum):
    ADD_DOCUMENTS = "INSERT INTO documents (file_name, embedding) VALUES (%s, %s)"
    # ADD_DOCUMENTS = """INSERT INTO documents (chunk_id, embedding, keywords) VALUES (%s, %s, %s)"""
    SEARCH_VECTOR = """SELECT embedding FROM documents WHERE keywords && %s ORDER BY embedding <-> %s LIMIT %s"""
    
class DB_EXTENSION(Enum):
    PGVECTOR = "CREATE EXTENSION IF NOT EXISTS vector"