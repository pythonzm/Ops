# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      crypt_pwd
   Description:
   Author:          Administrator
   date：           2018/5/24
-------------------------------------------------
   Change Activity:
                    2018/5/24:
-------------------------------------------------
"""
import base64
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES, PKCS1_v1_5


class CryptPwd:
    """
    用于加密和解密密码,
    """

    def __init__(self):
        self.key = "juren"
        self.mode = AES.MODE_ECB

    @staticmethod
    def add_to_16(value):
        """
        要加密的数据和使用的key的字节数必须是16位，这里不足16位的用'\n'填充，方便后面解密使用rstrip
        :param value: 要加长的内容
        :return: bytes类型的数据
        :type value: str
        :rtype: bytes
        """
        while len(value) % 16 != 0:
            value += '\n'
        return value.encode('utf-8')

    def encrypt_pwd(self, pwd):
        """
        对密码进行加密
        :param pwd: 密码
        :return: 加密后的密码
        :type pwd: str
        :rtype: str
        """
        aes = AES.new(self.add_to_16(self.key), self.mode)
        encrypt_aes = aes.encrypt(self.add_to_16(pwd))
        encrypted_pwd = str(base64.b64encode(encrypt_aes), encoding='utf-8')
        return encrypted_pwd

    def decrypt_pwd(self, encrypted_pwd):
        """
        对密码进行解密
        :param encrypted_pwd: 加密后的密码，必须是使用同一种方式加密的密码
        :return: 解密后的密码，字符串类型
        :type encrypted_pwd: str
        :rtype: str
        """
        aes = AES.new(self.add_to_16(self.key), self.mode)
        decrypt_base64 = base64.b64decode(encrypted_pwd.encode('utf-8'))
        decrypt_pwd = str(aes.decrypt(decrypt_base64), encoding='utf-8')
        return decrypt_pwd.rstrip()

    @staticmethod
    def de_js_encrypt(en_pwd):
        """
        解密通过jsencrypt.js文件加密的密码
        :param en_pwd:
        :return:
        """

        key = """-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgGhvDNv1H/3EGeNcS+ju3Ytx7QlWtvUi3KqV5U73md9G4Gyw+izQ
uvYYnZ/rDZrHocLB2fVcSZKKj8vNxkkpNqv00OJCGbwzGcOtXOpsRpiY2qhd0kvR
wglnN84h9kWq8C6oMe/eWwZkpsCQJMmtiHeHdzSUxHkf4mpwxUfVDqF5AgMBAAEC
gYBKjjUs9qN/JDejJCohQh4xxgSGLTzyZpAIzHhnVsaoKs5faj1AL0e6Fzq4hzMw
M6LdCk2TJ+5ySq97vQz5AA5B5nf0y4zokCwYn5vdFVVtZeyiVeY0LYSpEvBS0xHY
G3SJWLjMEtql2k1xJ8/1jvFkMx5SJKzruFFTvkRKn4bRAQJBANAuL2HZDjgcqgeF
M7pQOKR+MxJzkN0hWBap1yJ5HQnUPqsEyBD3/BIcffCk2rQkfxnMT7gbnbiWVUd7
/Ioh+FkCQQCAbClrx7wQW26JMjRqSBVyHWm1RoYDi0/USs7B9mct2KNGkPVr8dAB
nm/glt5Rs9ay2QHbI103TjSPP938xs4hAkB6oup4utQcjA5B1d8uH3nutQVDFl89
VRo+Z5j7jttjYev09SEileOhi7VJIORRgLp7KRfBPkuAZNciAFE50l8pAkBYE9bE
yRQ+07aX+grg6ddrkKizX08Cl0WFAFmVxf02AGLbPwhTpGFY+uUYT+DigEk8GIGh
XjvMdqKtrMv/VgqBAkEAjqQqCyiK1R9INladDpt8PjAJZecr1PLVdulyzlHvMm2l
CHd72qhDwZUKVQck56xLGpPVPBGyyMl+cjRhZ+mnIQ==
-----END RSA PRIVATE KEY-----"""

        rsakey = RSA.importKey(key)  # 导入私钥
        cipher = PKCS1_v1_5.new(rsakey)  # 生成对象
        missing_padding = len(en_pwd) % 4
        if missing_padding:
            en_pwd += '=' * (4 - missing_padding)
        text = cipher.decrypt(base64.b64decode(en_pwd.encode('utf-8')), "ERROR")  # 将密文解密成明文，返回的是一个bytes类型数据，需要自己转换成str

        return text.decode('utf-8')
