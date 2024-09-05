from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from threading import Thread, Lock
import uvicorn
import torch
import uuid
from threading import Thread, Lock


class LLM_MODEL():
    _instance = None 
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None: 
            with cls._lock:
                cls._instance = super().__new__(cls) 
                cls.model = AutoModelForCausalLM.from_pretrained(
                    "MediaTek-Research/Breeze-7B-Instruct-v1_0",
                    device_map="auto",
                    torch_dtype=torch.bfloat16,
                    attn_implementation="flash_attention_2" # optional
                    )
                cls.device = torch.device("cuda")
                cls.tokenizer = AutoTokenizer.from_pretrained("MediaTek-Research/Breeze-7B-Instruct-v1_0")
            return cls._instance
        
    def __init__(self):
        pass
        
    @classmethod
    def generater_response(self, message):
        chat = [
        {"role": "user", "content": message},
        ]
        conversion = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=False)
        encoding = self.tokenizer(conversion, return_tensors="pt").to(self.device)
        streamer = TextIteratorStreamer(self.tokenizer)
        generation_kwargs = dict(encoding, streamer=streamer, max_new_tokens=1000)
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        return conversion, streamer
    

llm = LLM_MODEL()     

app = FastAPI()

users = {}


class Room:
    def __init__(self, room_id):
        self.room = room_id
        self.connections = []

    async def broadcast(self, message):
        for connection in self.connections:
            conversion, streamer = llm.generater_response(message)

        for new_text in streamer:
            output = new_text.replace(conversion, '')
            if output:
                await connection.send_text(output)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    id = uuid.uuid4()
    return templates.TemplateResponse(
        request=request, name="LLM.html", context={"id": id}
    )

room_dict = {}

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
            await room.broadcast(data)

    except WebSocketDisconnect:
        if room_id in room_dict:
            room = room_dict[room_id]
            room.connections.remove(websocket)
            if len(room.connections) == 0:
                del room_dict[room_id]


if __name__ == "__main__":
    uvicorn.run("server:app", reload=True)