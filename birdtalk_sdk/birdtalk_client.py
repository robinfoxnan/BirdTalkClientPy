import asyncio
import locale
import platform
from .ws_client import WebSocketClient
from .crypt_helper import ECDHKeyExchange
import birdtalk_sdk.msg_pb2 as msg_pb2
import socket

import time

class ClientState:
    INITIAL = 0
    DISCONNECTED = 1
    RECONNECTING = 2
    CONNECTING = 3
    CONNECTED = 4
    CONNECTION_LOST = 5
    CLOSING = 6
    CLOSED = 7
    EXITING = 8

    ERROR = 20
    SENDING_MESSAGE = 21
    WAITING_RESPONSE = 22
   
    HELLO = 30
    KEY_EXCHANGE = 31
    WAIT_LOGIN = 32
    REGISTERING = 33
    READY = 34



class BirdTalkClient:
    '''
    name: 当前使用的秘钥的一个名字
    '''
    def __init__(self, uri, name):
        self.uri = uri
        self.client = WebSocketClient(uri)
        self.client.set_on_connect_callback(self.on_connect)
        self.client.set_on_disconnect_callback(self.on_disconnect)
        self.client.set_on_raw_message_callback(self.on_message)
        self.running = False
        self.keyEx = ECDHKeyExchange()
        self.printName = f"key_print_{name}.txt"
        self.keyName = f"shared_key_{name}.bin"
        self.keyEx.load_key_print(self.printName)
        self.keyEx.load_shared_key(self.keyName)
        self.ws_state = ClientState.INITIAL
        self.client_state = ClientState.HELLO

    async def on_connect(self, success):
        if success:
            print("Connected to WebSocket successfully!")
            await self.process_with_state()
        else:
            print("Failed to connect to WebSocket.")

    def on_disconnect(self):
        print("Disconnected from WebSocket.")

    def deserialize_protobuf(self, binary_data):
        msg = msg_pb2.Msg()  # 创建一个空的 Msg 对象

        # 反序列化二进制数据
        msg.ParseFromString(binary_data)
        return msg


    #这里处理消息
    async def on_message(self, message):
        msg = self.deserialize_protobuf(message)
        await self.dispatch_msg(msg)

    async def start(self):
        self.running = True
        try:
            await self.client.start()
        except KeyboardInterrupt:
            print("Keyboard interrupt detected, exiting...")
        finally:
            self.stop()

    def stop(self):
        if self.running:
            self.client.stop()
            self.running = False
            print("BirdTalkClient stopped.")

    async def run_forever(self):
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            self.stop()

    async def send(self, message):
        if isinstance(message, msg_pb2.Msg):
            # Serialize the protobuf message to bytes
                serialized_message = message.SerializeToString()
                #print(f"Sent protobuf message of type {type(message)}")
                #print(f"formatted message of type type(serialized_message)")
                await self.client.send_message(serialized_message)
                print(f"send message {message}")
                
        else:
            # Assuming message is already in a sendable format (string, bytes, etc.)
            print(f"count not send message: {message}")
            #await self.websocket.send(message)

#################################################################
    # 状态机，根据当前的状态决定如何操作
    async def process_with_state(self):
        if self.client_state == ClientState.HELLO:
            hello = self.create_hello()
            await self.send(hello)
            return
        if self.client_state == ClientState.KEY_EXCHANGE:
            return
        

    async def dispatch_msg(self, msg : msg_pb2.Msg) -> None:
        # 在这里处理消息
        print(f'received message:\n --------------------\n{msg}')
       
        # print(f"msgType: {msg.msgType}")
        # print(f"version: {msg.version}")
        # print(f"timestamp: {msg.tm}")
        if msg.msgType == msg_pb2.ComMsgType.MsgTHello:
            await self.on_hello(msg)
            return
        if msg.msgType == msg_pb2.ComMsgType.MsgTError:
            await self.on_error(msg)
            return
        if msg.msgType == msg_pb2.ComMsgType.MsgTKeyExchange:
            await self.on_key_exchange(msg)
            return
        


    async def on_error(self, msg: msg_pb2.Msg):
        err = msg.plainMsg.errorMsg
        print(err)

    async def on_hello(self, msg: msg_pb2.Msg):
        hello = msg.plainMsg.hello
        if hello.stage == "waitlogin":   # 执行密钥交换
            self.client_state = ClientState.KEY_EXCHANGE
            msg = self.create_keyex1()
            await self.send(msg)

        elif hello.stage == "needlogin": # 注册或者登录
            self.client_state = ClientState.WAIT_LOGIN
            print("need login first")

        elif hello.stage == "waitdata":  # 
            self.client_state = ClientState.READY
            print("login with key print ok")

        

    # 这里会是阶段2，或者阶段4的应答
    async def on_key_exchange(self, msg: msg_pb2.Msg):
        keyex = msg.plainMsg.keyEx
        if keyex.stage == 2:
            key_print = keyex.keyPrint
            pub_key = keyex.pubKey
            print(f"remote public key {pub_key}")
            self.keyEx.exchange_keys(pub_key)
            local_print = self.keyEx.get_int64_print()

            print(f"local print: {local_print}")
            print(f"local share key: {self.keyEx.get_shared_key()}")
            if local_print != key_print:
                print(f"local keyprint:{local_print} is not same with remote key:{key_print}")
                return
            
            # 这里一致基本就问题不大了，可以保存了
            self.keyEx.save_key_print(self.printName)
            self.keyEx.save_shared_key(self.keyName)
            data = self.create_keyex3()
            await self.send(data)
        
        elif keyex.stage == 4:  # 交换秘钥之后也需要登录，或者注册
            if keyex.status == "waitdata":
                self.client_state = ClientState.READY
                print("user login ok")
            if keyex.status == "needlogin":
                self.client_state = ClientState.WAIT_LOGIN
                print("user should login or register")

        

##################################################################
    def create_hello(self) -> msg_pb2.Msg:
        tm = int(time.time())
        
        # 子消息
        hello = msg_pb2.MsgHello()
        hello.clientId =  socket.gethostname()
        hello.version = "1.0"
        hello.platform = platform.system()
        hello.stage = "clienthello"
        hello.keyPrint = 0
        language, encoding = locale.getdefaultlocale()
        hello.params["lang"] = language
        hello.params['encoding'] = encoding
        

        # 检查是否有共享密钥
        key_print = self.keyEx.get_key_print()
        shared_key = self.keyEx.get_shared_key()
        if key_print != 0 and shared_key != None:
            # 如果 sharedKeyPrint 存在，则执行相应的操作
            print("sharedKeyPrint 存在")
            print("key print is: ",key_print)
            print(f"时间戳={tm}")
            check_data = self.keyEx.encrypt_aes_ctr_str_to_base64(str(tm))
            print("check data",check_data)
            hello.keyPrint = key_print
            hello.params['checkTokenData'] = check_data
        else:
            # 如果 sharedKeyPrint 不存在，则执行其他操作
            print("sharedKeyPrint 不存在")

        # 将 MsgHello 消息设置为 Msg 消息的 plainMsg 字段
        plain_msg = msg_pb2.MsgPlain()
        plain_msg.hello.CopyFrom(hello)

        # 封装为通用消息
        msg = msg_pb2.Msg()
        msg.msgType = msg_pb2.ComMsgType.MsgTHello
        msg.version = 1
        msg.plainMsg.CopyFrom(plain_msg)
        msg.tm = tm
        #print("hello msg=", msg)
        return msg
    
    # 生成阶段1的消息
    def create_keyex1(self) -> msg_pb2.Msg:
        self.keyEx.generate_key_pair()
        pub_key = self.keyEx.get_public_key()  

        exMsg = msg_pb2.MsgKeyExchange()
        exMsg.keyPrint = 0
        exMsg.rsaPrint = 0
        exMsg.stage = 1
        exMsg.pubKey = pub_key    # PEM格式编码的字节流UTF-8
        exMsg.encType = "AES-CTR" # 加密算法

        # Create an instance of MsgPlain and set its keyex field
        plainMsg = msg_pb2.MsgPlain()
        plainMsg.keyEx.CopyFrom(exMsg)

        # Create an instance of Msg and set its fields
        msg = msg_pb2.Msg()
        msg.msgType = msg_pb2.ComMsgType.MsgTKeyExchange
        msg.version = 1
        msg.plainMsg.CopyFrom(plainMsg)
        msg.tm = int(time.time())  # returns a Unix timestamp in seconds
        return msg
    
    # 生成阶段3的消息, 已经秘钥交换完成；
    def create_keyex3(self) -> msg_pb2.Msg:

        tm = int(time.time())
        tmStr = str(tm)
        exMsg = msg_pb2.MsgKeyExchange()
        exMsg.keyPrint = self.keyEx.get_key_print()
        exMsg.tempKey = self.keyEx.encrypt_aes_ctr_bytes_to_bytes(tmStr)
        exMsg.rsaPrint = 0
        exMsg.stage = 3
        exMsg.encType = "AES-CTR" # 加密算法
        exMsg.status = "ready"

        # Create an instance of MsgPlain and set its keyex field
        plainMsg = msg_pb2.MsgPlain()
        plainMsg.keyEx.CopyFrom(exMsg)

        # Create an instance of Msg and set its fields
        msg = msg_pb2.Msg()
        msg.msgType = msg_pb2.ComMsgType.MsgTKeyExchange
        msg.version = 1
        msg.plainMsg.CopyFrom(plainMsg)
        msg.tm = tm  # returns a Unix timestamp in seconds
        return msg