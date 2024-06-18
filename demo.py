import asyncio
import signal
from birdtalk_sdk import BirdTalkClient
from birdtalk_sdk import ClientState


client = BirdTalkClient("wss://127.0.0.1/ws?code=plain", "robin")

async def onClientError(state, err):
    print(state, err)


async def onClientStateChange(state, sub_state):
    if state == ClientState.WAIT_LOGIN:
        await client.login("id", 10003, "123456")
    elif state == ClientState.READY:
        print("login ok, can't send msg now...")

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
        client.set_error_callback(onClientError)
        client.set_state_callback(onClientStateChange)
        asyncio.run(client.start())
    except KeyboardInterrupt:
        print("Keyboard interrupt detected, exiting...")