import asyncio
import websockets
import ssl

class WebSocketClient:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.stop_event = asyncio.Event()
        self.on_connect_callback = None
        self.on_disconnect_callback = None
        self.on_raw_message_callback = None
    
    def set_on_raw_message_callback(self, callback):
        self.on_raw_message_callback = callback

    def set_on_connect_callback(self, callback):
        self.on_connect_callback = callback

    def set_on_disconnect_callback(self, callback):
        self.on_disconnect_callback = callback

    #文本消息，测试使用
    async def handle_text_message(self, message):
        print(f"Received text message: {message}")

    #二进制编码消息
    async def handle_binary_message(self, message):
        #print(f"Received binary message: {message}")
        if self.on_raw_message_callback:
            await self.on_raw_message_callback(message)

    async def handle_message(self, message):
        if isinstance(message, str):
            await self.handle_text_message(message)
        elif isinstance(message, bytes):
            await self.handle_binary_message(message)

    async def receive_loop(self):
        async for message in self.websocket:
            await self.handle_message(message)

    async def send_message(self, message):
        if self.websocket:
            #print(f"Sending message: {message}")
            await self.websocket.send(message)
        else:
            print("WebSocket is not connected")


    async def start(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            print("Attempting to connect to WebSocket...")
            async with websockets.connect(self.uri, ssl=ssl_context) as websocket:
                self.websocket = websocket
                print("WebSocket connection established")
                # Call on_connect_callback if set
                if self.on_connect_callback:
                    await self.on_connect_callback(True)

                receive_task = asyncio.create_task(self.receive_loop())
                stop_task = asyncio.create_task(self.stop_event.wait())
                done, pending = await asyncio.wait(
                    [receive_task, stop_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for task in pending:
                    task.cancel()
        except websockets.exceptions.InvalidURI:
            print("Error: Invalid WebSocket URI")
        except websockets.exceptions.InvalidHandshake:
            print("Error: WebSocket handshake failed")
        except ssl.SSLError as e:
            print(f"SSL error: {e}")
        except Exception as e:
            print(f"Error connecting to WebSocket: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()
                # Call on_disconnect_callback if set
                if self.on_disconnect_callback:
                    self.on_disconnect_callback()
                print("WebSocket connection closed")
            self.websocket = None
             
               

    def stop(self):
        print("Stopping WebSocket client")
        self.stop_event.set()


