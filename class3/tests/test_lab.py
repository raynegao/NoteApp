"""验证实际学习目标、错误边界与导出文件。"""

import tempfile
import unittest
import os
import runpy
import shutil
from pathlib import Path

from PIL import Image
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from caesar import crack, decrypt, encrypt


class CaesarTests(unittest.TestCase):
    def test_known_vector_and_wraparound(self):
        self.assertEqual(encrypt("HELLO", 3), "KHOOR")
        self.assertEqual(encrypt("XYZ, 123! 中文", 3), "ABC, 123! 中文")
        self.assertEqual(decrypt("KHOOR", 3), "HELLO")

    def test_all_shifts_preserve_the_message(self):
        message = "ZEBRA CROSSINGS: ABC XYZ, 123. 中文\n"
        for key in range(-27, 53):
            with self.subTest(key=key):
                self.assertEqual(decrypt(encrypt(message, key), key), message)

    def test_frequency_attack_on_independent_text_all_keys(self):
        # 这是另一段文字；攻击入口没有接收真实密钥或原文。
        message = (
            "The people in the village read the newspaper every morning. "
            "They hear the weather report and prepare for the journey to the nearest town. "
            "There are several different routes, and the driver chooses the safest one. "
            "Before the journey begins, everyone checks the equipment and shares the plan. "
            "The children remember the stories their parents told them about the river. "
            "When the travelers return in the evening, they describe the places they have seen. "
            "Their friends listen carefully and ask questions about the experience."
        ).upper()
        for key in range(26):
            with self.subTest(key=key):
                guessed_key = crack(encrypt(message, key))
                self.assertEqual(guessed_key, key)
                self.assertEqual(decrypt(encrypt(message, key), guessed_key), message)

    def test_attack_rejects_missing_english_letters(self):
        for message in ("", "123! 中文 ß"):
            with self.subTest(message=message), self.assertRaises(ValueError):
                crack(message)


class ImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temporary.name)
        cls.addClassCleanup(cls.temporary.cleanup)
        project = Path(__file__).resolve().parents[1]
        (cls.base / "assets").mkdir()
        (cls.base / "results/images").mkdir(parents=True)
        shutil.copy2(project / "assets/apple.jpg", cls.base / "assets/apple.jpg")
        previous = Path.cwd()
        try:
            os.chdir(cls.base)
            cls.script_values = runpy.run_path(str(project / "image_modes.py"))
        finally:
            os.chdir(previous)

    def test_saved_images_match_ciphertext(self):
        output = self.base / "results/images"
        for filename, expected in (
            ("ecb_pixels.png", self.script_values["ecb_data"]),
            ("gcm_pixels.png", self.script_values["gcm_data"][:-16]),
        ):
            with Image.open(output / filename) as image:
                self.assertEqual(image.size, (1200, 630))
                self.assertEqual(image.tobytes(), expected)

    def test_ecb_decrypts_and_preserves_repeated_blocks(self):
        decryptor = Cipher(algorithms.AES(self.script_values["key"]), modes.ECB()).decryptor()
        restored = decryptor.update(self.script_values["ecb_data"]) + decryptor.finalize()
        self.assertEqual(restored, self.script_values["data"])
        # 首行背景有重复块，ECB 中对应块仍相等。
        self.assertEqual(self.script_values["data"][:16], self.script_values["data"][48:64])
        self.assertEqual(self.script_values["ecb_data"][:16], self.script_values["ecb_data"][48:64])

    def test_gcm_decrypts_and_rejects_tampering(self):
        aesgcm = AESGCM(self.script_values["key"])
        nonce = self.script_values["nonce"]
        ciphertext = self.script_values["gcm_data"]
        self.assertEqual(len(nonce), 12)
        self.assertEqual(aesgcm.decrypt(nonce, ciphertext, None), self.script_values["data"])
        for index in (0, -1):
            changed = bytearray(ciphertext)
            changed[index] ^= 1
            with self.subTest(index=index), self.assertRaises(InvalidTag):
                aesgcm.decrypt(nonce, bytes(changed), None)


if __name__ == "__main__":
    unittest.main()
