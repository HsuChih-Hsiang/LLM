from enum import Enum

class DB_EXTENSION(Enum):
    PGVECTOR = "CREATE EXTENSION IF NOT EXISTS vector"

class DB_TABLE(Enum):
    DOCUMENTS = "documents"
    
class CREATE_TABLE_COMMAND(Enum):
    DOCUMENTS = """"CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            file_name TEXT NOT NULL,
            embedding vector(768)
        )
    """

class DB_TABLE_COMMAND(Enum):
    CHECK = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    
class RAG_COMMAND(Enum):
    ADD_DOCIMENTS = "INSERT INTO documents (file_name, embedding) VALUES (%s, %s)"
    SEARCH_VECTOR = "SELECT pdf_path FROM documents ORDER BY embedding <-> %s LIMIT %s"