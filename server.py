from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from llm_model import LLM_MODEL
from chat_room import Room
import uvicorn
import uuid


llm = LLM_MODEL()     
app = FastAPI()
templates = Jinja2Templates(directory="templates")
room_dict = {}

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


if __name__ == "__main__":
    uvicorn.run("server:app", reload=True)