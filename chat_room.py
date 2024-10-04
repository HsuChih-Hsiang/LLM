class Room:
    def __init__(self, room_id):
        self.room = room_id
        self.connections = []

    async def broadcast(self, response, llm, rag):
        # response = await rag.rag_pipeline(response)
        
        for connection in self.connections:
            conversion, streamer = llm.generater_response(response)

        for new_text in streamer:
            output = new_text.replace(conversion, '')
            if output:
                await connection.send_text(output)