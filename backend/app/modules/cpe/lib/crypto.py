"""
CPE AES 加密模块
"""

import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def intAesIV() -> bytes:
    """生成固定的 IV"""
    return b'0000000000000000'


class AESEncryptor:
    """AES 加密器"""
    
    @staticmethod
    def encrypt(data: str, key: str) -> str:
        """
        AES CBC 加密
        
        Args:
            data: 要加密的数据
            key: 加密密钥(前16位)
        
        Returns:
            加密后的十六进制字符串
        """
        key_bytes = key[:16].encode('utf-8')
        iv = intAesIV()
        
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        padded_data = pad(data.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        
        return encrypted.hex()
    
    @staticmethod
    def decrypt(data: str, key: str) -> str:
        """
        AES CBC 解密
        
        Args:
            data: 加密后的十六进制字符串
            key: 解密密钥(前16位)
        
        Returns:
            解密后的字符串
        """
        key_bytes = key[:16].encode('utf-8')
        iv = intAesIV()
        
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        encrypted_bytes = bytes.fromhex(data)
        decrypted = cipher.decrypt(encrypted_bytes)
        unpadded = unpad(decrypted, AES.block_size)
        
        return unpadded.decode('utf-8')
