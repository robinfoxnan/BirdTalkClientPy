import asyncio
import signal
from birdtalk_sdk import BirdTalkClient


client = BirdTalkClient("wss://127.0.0.1/ws?code=plain", "robin")

async def signal_handler():
    # Wait for the KeyboardInterrupt
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        # Stop the client when interrupted
        client.stop()

if __name__ == "__main__":
    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        print("Keyboard interrupt detected, exiting...")