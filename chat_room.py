class Room:
    def __init__(self, room_id):
        self.room = room_id
        self.connections = []

    async def broadcast(self, *args):
        response, llm, rag = args
        cnt = 0
        
        for connection in self.connections:
            if rag:
                response = rag.rag_pipeline(response)
            conversion, streamer = llm.generater_response(response)

        for new_text in streamer:
            output = new_text.replace(conversion, '')
            if '[INST]' or ' [/INST]' in output:
                cnt += 1
            if output and cnt>=2:
                await connection.send_text(output)