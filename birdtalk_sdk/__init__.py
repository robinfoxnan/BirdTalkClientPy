import logging
from .birdtalk_client import BirdTalkClient
from .birdtalk_client import ClientState
import birdtalk_sdk.msg_pb2 as msg_pb2

VERSION = '1.0.0'
logging.basicConfig(level=logging.INFO)
