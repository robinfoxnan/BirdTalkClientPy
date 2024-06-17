from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import os
import struct
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ECDHKeyExchange:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.shared_key = None
        self.key_print = 0

    def generate_key_pair(self):
        """Generate an ECDH key pair."""
        self.private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        self.public_key = self.private_key.public_key()
        print("Key pair generated.")

    def export_public_key(self, filename):
        """Export the generated public key to a file."""
        if self.public_key is None:
            raise ValueError("Public key not generated yet.")
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        if filename != "":
            with open(filename, 'wb') as f:
                f.write(pem)
            print(f"Public key saved to {filename}.")
        return pem.decode('utf-8')
    
    def get_public_key(self):
        if self.public_key is None:
            raise ValueError("Public key not generated yet.")
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem


    def exchange_keys_from_file(self, peer_public_key_filename):
        """Exchange keys and generate the shared key using the peer's public key."""
        if self.private_key is None:
            raise ValueError("Private key not generated yet.")
        with open(peer_public_key_filename, 'rb') as f:
            peer_public_key_pem = f.read()
        peer_public_key = serialization.load_pem_public_key(peer_public_key_pem, backend=default_backend())
        self.shared_key = self.private_key.exchange(ec.ECDH(), peer_public_key)
        print("Shared key generated.")
    
    # 这里传入的是pem格式的字节流
    def exchange_keys(self, peer_public_key_pem):
        """Exchange keys and generate the shared key using the peer's public key PEM string."""
        if self.private_key is None:
            raise ValueError("Private key not generated yet.")
        # peer_public_key_pem.encode('utf-8')
        peer_public_key = serialization.load_pem_public_key(peer_public_key_pem, backend=default_backend())
        self.shared_key = self.private_key.exchange(ec.ECDH(), peer_public_key)
        print("Shared key generated.")

    def get_shared_key(self):
        if self.shared_key is None:
            return None
        
        return self.shared_key

    def save_shared_key(self, filename):
        """Save the shared key to a file."""
        if self.shared_key is None:
            raise ValueError("Shared key not generated yet.")
        with open(filename, 'wb') as f:
            f.write(self.shared_key)
        print(f"Shared key saved to {filename}.")
    
    def export_shared_key_base64(self):
        """Export the shared key as a base64 encoded string."""
        if self.shared_key is None:
            raise ValueError("Shared key not generated yet.")
        return base64.b64encode(self.shared_key).decode('utf-8')

    def load_shared_key(self, filename):
        """Load the shared key from a file."""
        try:
            with open(filename, 'rb') as f:
                self.shared_key = f.read()
            print(f"Shared key loaded from {filename}.")
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            return 
        except IOError as e:
            print(f"Error: IOError occurred while trying to read '{filename}'.")
            return

    def save_key_print(self, filename):
        """Save the shared key to a file."""
        if self.key_print is None:
            raise ValueError("Shared key not generated yet.")
        with open(filename, 'wb') as f:
            data = str(self.key_print).encode('utf-8')
            f.write(data)
        print(f"key print saved to {filename}.")

    def load_key_print(self, filename):
        """Load the shared key from a file."""
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                try:
                    # Assuming the key is a string representation of an integer
                    self.key_print = int(data.decode('utf-8').strip())
                    print(f"Key print loaded from {filename}.")
                    return self.key_print
                except ValueError as e:
                    #print(f"Error: Cannot convert data in {filename} to an integer.")
                    return 0
                except UnicodeDecodeError as e:
                    #print(f"Error: Cannot decode data in {filename} as UTF-8.")
                    return 0
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            return 0
        except IOError as e:
            print(f"Error: IOError occurred while trying to read '{filename}'.")
            return 0


    def delete_key_file(self, filename):
        """Delete a key file."""
        if os.path.exists(filename):
            os.remove(filename)
            print(f"File {filename} deleted.")
        else:
            print(f"File {filename} does not exist.")
    
    def get_key_print(self):
        if self.key_print is None:
            return 0
        
        return self.key_print

    def get_int64_print(self):
        if self.shared_key is None:
            raise ValueError("Shared key not generated yet.")
         
        """Convert a byte array to a 64-bit integer."""
        # 检查字节数组长度是否足够
        if len(self.shared_key) < 8:
            raise ValueError("Insufficient bytes to convert to int64")

        # 将字节数组转换为 int64
        self.key_print = struct.unpack('<q',  self.shared_key[:8])[0]  # 使用 little-endian 格式

        return self.key_print
    
    def encrypt_aes_ctr_str_to_base64(self, plaintext):
        # 传入的是字符串
        cipher = self.encrypt_aes_ctr(plaintext.encode('utf-8'))
        return base64.b64encode(cipher)
        # .decode('utf-8')
    
    def encrypt_aes_ctr_bytes_to_bytes(self, plaintext):
        # 传入的是字符串
        cipher =self.encrypt_aes_ctr(plaintext.encode('utf-8'))
        return cipher
    
    def decrypt_aes_ctr_bytes_to_str(self, ciphertext):
        data = self.decrypt_aes_ctr(ciphertext)
        return data.decode('utf-8')


    def encrypt_aes_ctr(self, plaintext):
        if self.shared_key is None:
            raise ValueError("Shared key not generated yet.")
        
        # 生成随机的初始化向量（IV）
        iv = os.urandom(16)  # 初始化向量长度为 16 字节

        # 创建 AES-CTR 算法对象
        algorithm = algorithms.AES(self.shared_key)
        mode = modes.CTR(iv)
        cipher = Cipher(algorithm, mode, backend=default_backend())

        # 使用加密器加密数据
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(plaintext) + encryptor.finalize()

        # 将随机初始化向量和加密后的数据拼接在一起
        ciphertext = iv + encrypted_data

        return ciphertext
    
    def decrypt_aes_ctr(self, ciphertext):
        """Decrypt ciphertext using AES-CTR with the shared key."""
        if self.shared_key is None:
            raise ValueError("Shared key not generated yet.")
        
        # 从密文中提取初始化向量（IV）
        iv = ciphertext[:16]  # 初始化向量长度为 16 字节
        encrypted_data = ciphertext[16:]

        # 创建 AES-CTR 算法对象
        algorithm = algorithms.AES(self.shared_key)
        mode = modes.CTR(iv)
        cipher = Cipher(algorithm, mode, backend=default_backend())

        # 使用解密器解密数据
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(encrypted_data) + decryptor.finalize()

        return plaintext
###############################################################
def test_create_key_pair():
    # 实例化两个 ECDHKeyExchange 对象，模拟两个参与方
    alice = ECDHKeyExchange()
    bob = ECDHKeyExchange()

    # Alice 生成密钥对并导出公钥
    alice.generate_key_pair()
    alice_pub_key = alice.export_public_key("alice_public_key.pem")
    print(alice_pub_key)

    # Bob 生成密钥对并导出公钥
    bob.generate_key_pair()
    bob_pub_key = bob.export_public_key("bob_public_key.pem")
    print(bob_pub_key)

    # Alice 和 Bob 交换公钥并生成共享密钥
    alice.exchange_keys(bob_pub_key)
    bob.exchange_keys(alice_pub_key)

    # 保存共享密钥
    alice.save_shared_key("alice_shared_key.bin")
    bob.save_shared_key("bob_shared_key.bin")

    # 加载共享密钥
    alice.load_shared_key("alice_shared_key.bin")
    bob.load_shared_key("bob_shared_key.bin")
    print(alice.get_int64_print())
    print(bob.get_int64_print())

    alice.save_key_print("alice_key_print.txt")
    keyprint = alice.load_key_print("alice_key_print.txt")
    print(keyprint)

    # 删除密钥文件
    # alice.delete_key_file("alice_public_key.pem")
    # alice.delete_key_file("alice_shared_key.bin")
    # bob.delete_key_file("bob_public_key.pem")
    # bob.delete_key_file("bob_shared_key.bin")

def test_load_key():
    alice = ECDHKeyExchange()
    alice.load_shared_key("alice_shared_key.bin")
    #print(alice.get_shared_key())
    key_print = alice.load_key_print("alice_key_print.txt")
    print(key_print)

    tm = '123456789412'
    ciper = alice.encrypt_aes_ctr(tm.encode('utf-8'))
    plain = alice.decrypt_aes_ctr(ciper)
    print(plain)

# 示例使用
if __name__ == "__main__":
    test_load_key()
