from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form, Depends
from contextlib import asynccontextmanager
from API_Model.document_model import DocumentCreate
from API_Model.api_enum import FileType
from Utility.config import Configuration, ConfigKey
from Database.Util.Database_Container import DataBaseContainer
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from Model.llm_model import LLMFactory
from chat_room import Room
import traceback
import uvicorn
import uuid


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, room_dict, rag
    llm = LLMFactory.create_llm(Configuration().get_value(ConfigKey.LLM_MODEL.value))
    database = DataBaseContainer()
    db_conn = database.db_conn()
    database.db_create()
    rag = database.rag()
    room_dict = {}
    yield
    db_conn.closeall()
   
app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="Template")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(content=b"", media_type="image/x-icon")

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    id = uuid.uuid4()
    return templates.TemplateResponse(
        request=request, name="LLM.html", context={"id": id}
    )

@app.websocket('/ws/{room_id}')
async def websocket_endpoint(websocket:WebSocket, room_id: str):
    try:
        await websocket.accept()

        if room_id not in room_dict:
            room_dict[room_id] = Room(room_id)

        room  = room_dict[room_id]
        room.connections.append(websocket)

        while True:
            data = await websocket.receive_text()
            room_data = (data, llm, None) if True else (data, llm, rag)
            await room.broadcast(*room_data)

    except WebSocketDisconnect:
        if room_id in room_dict:
            room = room_dict[room_id]
            room.connections.remove(websocket)
            if len(room.connections) == 0:
                del room_dict[room_id]
 
@app.post("/documents")               
async def add_documents(request: Request):
    form_data = await request.form()
    document = DocumentCreate(**form_data)
    try:
        if document.file:
            name, text = rag.pdf_dealer(document.file)
            file_type = FileType.PDF.value
        elif document.name and document.text:
            name, text, file_type = document.name, document.text, FileType.TEXT.value
        else:
            return JSONResponse(content={"message": "Invalid request"}, status_code=400)
        
        text = rag.deal_text(text)   
        rag.store_text(name, text, file_type)
        return JSONResponse(content={"message": "資料已成功新增到 RAG"}, status_code=200)
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(content={"message": f"新增檔案時發生問題: {str(e)}"}, status_code=500)

@app.put("/documents")               
async def update_documents():
    pass

@app.get("/documents")               
async def search_documents():
    pass

@app.get("/documents_list")               
async def documents_list():
    pass

if __name__ == "__main__":
    uvicorn.run("server:app", host="140.112.3.52", port=8000, reload=True)