from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File
from contextlib import asynccontextmanager
from DB.DB_Container import DataBaseContainer
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from llm_model import LLM_MODEL
from chat_room import Room
import uvicorn
import uuid
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, room_dict, rag
    llm = LLM_MODEL()
    # database = DataBaseContainer()
    # database.db_conn()
    # database.db_create()
    # rag = database.rag()
    room_dict = {}
    yield
   
app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

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
            # response = await rag.rag_pipeline(data)
            await room.broadcast(data, llm)

    except WebSocketDisconnect:
        if room_id in room_dict:
            room = room_dict[room_id]
            room.connections.remove(websocket)
            if len(room.connections) == 0:
                del room_dict[room_id]
 
@app.post("/documents")               
async def add_documents(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(contents)
        
        rag.store_pdf(file_path)
        os.remove(file_path)
        return JSONResponse(content={"message": "文档已成功添加到 RAG 系统"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": f"添加文档时出错: {str(e)}"}, status_code=500)

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