from enum import Enum

class DocumentsCommand(Enum):
    ADD_DOCUMENTS = "INSERT INTO documents (file_name, file_type) VALUES (%s, %s) RETURNING id"
    DOCUMENTS_TYPE_LIST = "SELECT * FROM documents_type"
    DOCUMENTS_LIST = "SELECT * FROM documents_type as dt, documents as d where d.file_type = dt.id"
    
class RagCommand(Enum):
    INSERT_DOCUMENT_CHUNK = "INSERT INTO document_chunks (document_id, chunk_text) VALUES (%s, %s) RETURNING id"
    INSERT_DOCUMENT_EMBEDDING = "INSERT INTO documents_embedding (document_id, embedding, keywords) VALUES (%s, %s, %s)"
    SEARCH_VECTOR = """SELECT dc.chunk_text, de.embedding <-> %s AS distance FROM documents_embedding de
    JOIN document_chunks dc ON de.chunk_id = dc.id WHERE de.keywords @> (unnest(%s)) ORDER BY distance LIMIT %s
    """
    
