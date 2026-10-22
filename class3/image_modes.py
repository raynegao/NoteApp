import os
from PIL import Image
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# 读取图片的像素
image = Image.open("assets/apple.jpg").convert("RGB")
data = image.tobytes()
key = AESGCM.generate_key(bit_length=256)

# ECB 加密，再把密文当成像素保存
encryptor = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
ecb_data = encryptor.update(data) + encryptor.finalize()
Image.frombytes("RGB", image.size, ecb_data).save("results/images/ecb_pixels.png")

# GCM 使用课件第 25 页的写法
nonce = os.urandom(12)
gcm_data = AESGCM(key).encrypt(nonce, data, None)
# 最后 16 字节是认证标签，显示图片时不放进去
Image.frombytes("RGB", image.size, gcm_data[:-16]).save("results/images/gcm_pixels.png")
