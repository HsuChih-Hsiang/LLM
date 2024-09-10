from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response
from llm_model import LLM_MODEL
from chat_room import Room
import uvicorn
import uuid


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm
    llm = LLM_MODEL()
    yield
   
app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")
room_dict = {}

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
            await room.broadcast(data, llm)

    except WebSocketDisconnect:
        if room_id in room_dict:
            room = room_dict[room_id]
            room.connections.remove(websocket)
            if len(room.connections) == 0:
                del room_dict[room_id]
 
@app.post("/documents")               
async def add_documents():
    pass

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