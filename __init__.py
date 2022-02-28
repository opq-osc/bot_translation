import hashlib
import random
from typing import Union

import httpx
from botoy import FriendMsg, GroupMsg, S
from botoy import async_decorators as deco
from botoy import jconfig, logger
from botoy.contrib import plugin_receiver

__doc__ = """翻译插件"""


translation = jconfig.get_configuration('translation')
appid = translation.get('appid')
secretKey = translation.get('secretkey')
defaultToLang = translation.get("defaultToLang", "zh")

assert appid and secretKey, "请配置appid和secretKey"


async def translate(
    text: str, fromLang: str = "auto", toLang: str = defaultToLang
) -> dict:
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
        "sign": hashlib.md5(str(appid + text + salt + secretKey).encode()).hexdigest(),
    }
    async with httpx.AsyncClient() as client:
        res = await client.get(url, params=params)
        print(res.request.url)
        return res.json()


def return_msg(res: dict) -> str:
    return f"原文[{res['from']}]: {res['trans_result'][0]['src']}\r\n译文[{res['to']}]: {res['trans_result'][0]['dst']}"


# 翻译.en 你好

keyword = "翻译"


@plugin_receiver.friend
@plugin_receiver.group
@deco.ignore_botself
@deco.startswith(keyword)
async def main(ctx: Union[GroupMsg, FriendMsg]):
    msg = ctx.Content[len(keyword) - 1 :]
    cmd, rawtext = msg.split(" ", 1)
    if "." in cmd:
        toLang = cmd.split(".", 1)[1]
        api_res = await translate(rawtext, toLang=toLang)
    else:
        api_res = await translate(rawtext)
    if "error_code" in api_res.keys():
        logger.error(f"翻译错误:{api_res}")
        await S.atext(text="error")
        return
    await S.atext(text=return_msg(api_res))
