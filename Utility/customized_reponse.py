from fastapi.responses import HTMLResponse, JSONResponse, Response

class CustomResponse:
    def __init__(self, data):
        self.data = data