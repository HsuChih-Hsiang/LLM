from enum import Enum

class DocumentsCommand(Enum):
    ADD_DOCUMENTS = "INSERT INTO documents (file_name, file_type) VALUES (%(file_name)s, %(file_type)s) RETURNING id"
    DOCUMENTS_TYPE_LIST = "SELECT * FROM documents_type"
    DOCUMENTS_LIST = "SELECT * FROM documents_type as dt, documents as d where d.file_type = dt.id"
    
class RagCommand(Enum):
    INSERT_DOCUMENT_CHUNK = "INSERT INTO document_chunks (document_id, chunk_text) VALUES (%(document_id)s, %(chunk_text)s) RETURNING id"
    INSERT_DOCUMENT_EMBEDDING = "INSERT INTO documents_embedding (chunk_id, embedding, keywords) VALUES (%(chunk_id)s, %(embedding)s, %(keywords)s)"
    SEARCH_VECTOR = """SELECT dc.chunk_text, (de.embedding <-> %(embedding)s) / min(de.embedding <-> %(embedding)s) OVER () AS distance_ratio FROM documents_embedding de
    JOIN document_chunks dc ON de.chunk_id = dc.id WHERE de.keywords @> (unnest(%(keywords)s)) AND distance_ratio < %(ratio)s ORDER BY distance LIMIT %(limit)s
    """
    
