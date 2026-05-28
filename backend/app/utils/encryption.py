"""
Encryption Utilities for API Credentials
使用 AES-256 加密存储密码
"""
import os
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


# 从环境变量获取加密密钥，或使用默认值（生产环境应使用环境变量）
ENCRYPTION_KEY = os.environ.get('INSPECTION_KEY', 'host-inspection-secret-key-32b!')


def get_key():
    """获取32字节密钥"""
    key = ENCRYPTION_KEY.encode('utf-8')
    # 确保密钥长度为32字节（AES-256）
    if len(key) < 32:
        key = key + b'0' * (32 - len(key))
    elif len(key) > 32:
        key = key[:32]
    return key


def encrypt_password(password: str) -> str:
    """
    加密密码
    返回 base64 编码的加密数据
    """
    if not password:
        return ""

    key = get_key()
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # 加密
    padded_data = pad(password.encode('utf-8'), AES.block_size)
    encrypted = cipher.encrypt(padded_data)

    # 组合 IV 和加密数据，然后 base64 编码
    result = base64.b64encode(iv + encrypted).decode('utf-8')
    return result


def decrypt_password(encrypted_password: str) -> str:
    """
    解密密码
    """
    if not encrypted_password:
        return ""

    try:
        key = get_key()
        # base64 解码
        data = base64.b64decode(encrypted_password.encode('utf-8'))

        # 分离 IV 和加密数据
        iv = data[:16]
        encrypted = data[16:]

        # 解密
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)

        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"解密失败: {e}")
        return ""


# 测试
if __name__ == "__main__":
    test_pwd = "my-secret-password"
    encrypted = encrypt_password(test_pwd)
    decrypted = decrypt_password(encrypted)
    print(f"原始: {test_pwd}")
    print(f"加密: {encrypted}")
    print(f"解密: {decrypted}")
    assert test_pwd == decrypted, "加密/解密测试失败"
    print("测试成功!")