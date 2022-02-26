import hashlib
import json
import random
from pathlib import Path
from typing import Union

import httpx
from botoy import GroupMsg, FriendMsg, logger, S
from botoy import async_decorators as deco

__doc__ = """翻译插件"""

curFileDir = Path(__file__).parent  # 当前文件路径

try:
    with open(curFileDir / "config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except:
    logger.error("载入百度翻译配置文件出错")
    exit(0)

appid = config["appid"]  # appid
secretKey = config['secretKey']  # 密钥
defaultToLang = config['defaultToLang']  # 密钥
if appid == "" or secretKey == "":
    logger.error("请检查百度翻译appid和secretKey")
    exit(0)


async def translate(text: str, fromLang: str = "auto", toLang: str = defaultToLang) -> dict:
    """
    翻译
    :rtype: dict
    :param text:要翻译的文本
    :param fromLang: 翻译源语言 (可auto)
    :param toLang: 翻译目标语言 (不可auto)
    :return:
    """
    url = "https://api.fanyi.baidu.com/api/trans/vip/translate"
    salt = str(random.randint(32768, 65536))
    params = {
        "appid": appid,
        "q": text,
        "from": fromLang,
        "to": toLang,
        "salt": salt,
        "sign": hashlib.md5(str(appid + text + salt + secretKey).encode()).hexdigest()
    }
    async with httpx.AsyncClient() as client:
        res = await client.get(url, params=params)
        print(res.request.url)
        return res.json()


def return_msg(res: dict) -> str:
    return f"原文[{res['from']}]: {res['trans_result'][0]['src']}\r\n译文[{res['to']}]: {res['trans_result'][0]['dst']}"


# 翻译.en 你好

keyword = "翻译"


@deco.ignore_botself
@deco.startswith(keyword)
async def main(ctx: Union[GroupMsg, FriendMsg]):
    msg = ctx.Content[len(keyword) - 1:]
    cmd, rawtext = msg.split(" ", 1)
    if '.' in cmd:
        toLang = cmd.split(".", 1)[1]
        api_res = await translate(rawtext, toLang=toLang)
    else:
        api_res = await translate(rawtext)
    if "error_code" in api_res.keys():
        logger.error(f"翻译错误:{api_res}")
        S.text(text="error")
        return
    S.text(text=return_msg(api_res))


async def receive_group_msg(ctx):
    await main(ctx)


async def receive_friend_msg(ctx):
    await main(ctx)
