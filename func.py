import config
import asyncio
import json
import pywikibot
import time
import logging
import random
import string
from filelock import FileLock
from telegram import Bot, Update
from telegram.ext import ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

site = pywikibot.Site('zh', 'wikipedia')
Bot = Bot(config.token, base_url='https://api.telegram.org/bot', base_file_url='https://api.telegram.org/file/bot')

def is_verified(userid:int) -> bool:
    lock = FileLock("record.json.lock", timeout=10)
    try:
        with lock:
            with open("record.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            if userid in data["verifiedUsername"]:
                return True
            else:
                return False
    except:
        logging.error("Error: is verified?")
        return False

def is_blocked(userid:int) -> bool:
    return False

def accessVerifyCode(command:str, userid=None) -> dict:
    lock = FileLock("record.json.lock", timeout=10)
    try:
        with lock:
            with open("record.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            match command:
                case "remove":
                    verifycode = data["verifyCode"]
                    verifycode.pop(str(userid))
                    with open("record.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                case "get":
                    return data["verifyCode"]
    except:
        logging.error("在访问验证码列表的过程中发生了错误")

def accessVerifiedUsername(command:str, userid=None, username=None) -> str:
    lock = FileLock("record.json.lock", timeout=10)
    try:
        with lock:
            with open("record.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            match command:
                case "whois":
                    vdict = data["verifiedUsername"]
                    if str(userid) in vdict:
                        return str(vdict[str(userid)])
                    else:
                        return ""
                case "add":
                    vdict = data["verifiedUsername"]
                    if str(userid) in vdict:
                        vdict.pop(str(userid))
                        vdict[str(userid)] = str(username)
                        with open("record.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                    else:
                        vdict[str(userid)] = str(username)
                        with open("record.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                case "remove":
                    vdict = data["verifiedUsername"]
                    if str(userid) in vdict:
                        vdict.pop(str(userid))
                        with open("record.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                    else:
                        logging.error("收到了要求从已验证用户列表中移除 Telegram ID 为 {userid} 的用户的请求，但没有找到该用户。".format(userid=userid))
    except:
        logging.error("在访问已验证用户的时候发生了错误")

def accessAdmin(command:str, userid:int) -> bool:
    lock = FileLock("record.json.lock", timeout=10)
    try:
        with lock:
            with open("record.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            match command:
                case "is":
                    adict = data["admin"]
                    if userid in adict:
                        return True
                    else:
                        return False
                case "add":
                    adict = data["admin"]
                    if userid in adict:
                        adict.remove(userid)
                        adict.append(userid)
                        with open("record.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                    else:
                        adict.append(userid)
                        with open("record.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                case "remove":
                    adict = data["admin"]
                    if userid in adict:
                        adict.remove(userid)
                        with open("record.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                    else:
                        logging.error("收到了要求从已验证用户列表中移除 Telegram ID 为 {userid} 的用户的请求，但没有找到该用户。".format(userid=userid))
    except:
        logging.error("在访问已验证用户的时候发生了错误")

def startAuth(userid:int) -> str:
    lock = FileLock("record.json.lock", timeout=10)
    try:
        with lock:
            with open("record.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            tokenlist = data["verifyCode"]
            token = ''.join(random.sample(string.ascii_letters + string.digits, 15))
            if str(userid) in tokenlist:
                tokenlist.pop(str(userid))
                tokenlist[str(userid)] = token
                with open("record.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                return token
            else:
                tokenlist[str(userid)] = token
                with open("record.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                return token
    except:
        logging.error(f'{userid}在开始验证阶段发生问题')
        return "Error: 发生错误，请不要继续验证。请到 @YimingMB 反馈问题。"

def isEligible(username:str) -> bool:
    user = pywikibot.User(site, username)
    if "abusefilter" in user.groups() or "abusefilter-helper" in user.groups() or "sysop" in user.groups():
        return True
    else:
        return False

async def getInviteLink(username:str) -> str:
    link = await Bot.create_chat_invite_link(
        chat_id = config.limitedGroupID,
        member_limit = 1,
        name = username
    )
    return link.invite_link

async def start(update: Update, context=ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == "private":
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = "{username}你好，发送 /auth 来开始验证。".format(username=update.effective_user.first_name),
            disable_notification = True,
            reply_parameters = {
                "chat_id" : update.effective_chat.id,
                "message_id" : update.effective_message.message_id
            }
        )
    else:
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = "{username}你好，在私聊中发送 /auth 来开始验证。".format(username=update.effective_user.first_name),
            reply_parameters = {
                "chat_id" : update.effective_chat.id,
                "message_id" : update.effective_message.message_id
            }
        )

async def auth(update:Update, context:ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == "private":
        if is_blocked(update.effective_chat.id):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="您的操作被自动识别为有害，请加入 @YimingMB 解决问题。"
            )
            logging.error("{userid} 尝试使用本机器人，但机器人发现该用户已被列于一些黑名单上".format(userid=update.effective_chat.id))
        else:
            token = startAuth(update.effective_chat.id)
            await context.bot.send_message(
                chat_id= update.effective_chat.id,
                text = "请在 Wikipedia:沙盒 页面随意添加一些文字，然后在编辑摘要部分添加：{token} \n 完成后请稍作等待，机器人最长可能需要 10 分钟才能处理您的验证。".format(token=token),
                reply_parameters={
                    "chat_id": update.effective_chat.id,
                    "message_id": update.effective_message.message_id
                }
            )
            logging.info("{userid} 开启了一次验证".format(userid=update.effective_chat.id))

async def whois(update:Update, context:ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message:
        userid = update.message.reply_to_message.from_user.id
        if accessVerifiedUsername("whois", userid):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="您所查询的用户（Telegram ID 为 {userid}）的站内用户名是 {username}。".format(userid=userid, username=accessVerifiedUsername("whois", userid)),
                reply_parameters={
                    "chat_id": update.effective_chat.id,
                    "message_id": update.effective_message.message_id
                }
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="未查询到 Telegram ID 为 {userid} 的用户的站内用户名，该用户可能是由群组管理员邀请但管理员忘记使用 /link 为其绑定身份。".format(userid=userid, username=accessVerifiedUsername("whois", userid)),
                reply_parameters={
                    "chat_id": update.effective_chat.id,
                    "message_id": update.effective_message.message_id
                }
            )
    else:
        if context.args[0]:
            userid = context.args[0]
            if accessVerifiedUsername("whois", userid):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="您所查询的用户（Telegram ID 为 {userid}）的站内用户名是 {username}。".format(userid=userid, username=accessVerifiedUsername("whois", userid)),
                    reply_parameters={
                        "chat_id": update.effective_chat.id,
                        "message_id": update.effective_message.message_id
                    }
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="未查询到 Telegram ID 为 {userid} 的用户的站内用户名，可能是您输入的参数错误或该用户可能是由群组管理员邀请但管理员忘记使用 /link 为其绑定身份。".format(userid=userid, username=accessVerifiedUsername("whois", userid)),
                    reply_parameters={
                        "chat_id": update.effective_chat.id,
                        "message_id": update.effective_message.message_id
                    }
                )
        else:
            if accessVerifiedUsername("whois", update.message.from_user.id):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="您已验证的站内用户名是 {username}。".format(userid=userid, username=accessVerifiedUsername("whois", userid)),
                    reply_parameters={
                        "chat_id": update.effective_chat.id,
                        "message_id": update.effective_message.message_id
                    }
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="未查询到您的身份，可能是因为邀请您加入的管理员忘记使用 /link 为您绑定身份。\n @eveningtaco".format(userid=userid, username=accessVerifiedUsername("whois", userid)),
                    reply_parameters={
                        "chat_id": update.effective_chat.id,
                        "message_id": update.effective_message.message_id
                    }
                )

async def link(update:Update, context:ContextTypes.DEFAULT_TYPE) -> None:
    if accessAdmin("is", update.message.from_user.id):
        if update.message.reply_to_message:
            if context.args:
                if accessVerifiedUsername("whois", update.message.reply_to_message.from_user.id):
                    accessVerifiedUsername("remove", update.message.reply_to_message.from_user.id)
                    accessVerifiedUsername("add", update.message.reply_to_message.from_user.id, context.args[0])
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="已覆写此用户身份信息",
                        reply_parameters={
                            "chat_id": update.effective_chat.id,
                            "message_id": update.effective_message.message_id
                        }
                    )
                else:
                    accessVerifiedUsername("add", update.message.reply_to_message.from_user.id, context.args[0])
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="已链接此用户身份",
                        reply_parameters={
                            "chat_id": update.effective_chat.id,
                            "message_id": update.effective_message.message_id
                        }
                    )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="请提供用户站内用户名",
                    reply_parameters={
                        "chat_id": update.effective_chat.id,
                        "message_id": update.effective_message.message_id
                    }
                )  
        else:
            if context.args:
                if context.args[1]:
                    if context.args[0]:
                        accessVerifiedUsername("add", context.args[1], context.args[0])
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="已将 {userid} 识别为 {username}".format(userid=context.args[1], username=context.args[0]),
                            reply_parameters={
                                "chat_id": update.effective_chat.id,
                                "message_id": update.effective_message.message_id
                            }
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="请提供用户站内用户名",
                            reply_parameters={
                                "chat_id": update.effective_chat.id,
                                "message_id": update.effective_message.message_id
                            }
                        )
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="请提供 Telegram ID",
                        reply_parameters={
                            "chat_id": update.effective_chat.id,
                            "message_id": update.effective_message.message_id
                        }
                    )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="请提供参数",
                    reply_parameters={
                        "chat_id": update.effective_chat.id,
                        "message_id": update.effective_message.message_id
                    }
                )  

async def checkPolling() -> None:
    while True:
        if accessVerifyCode("get"):
            for userid, verifyCode in accessVerifyCode("get").items():
                page = pywikibot.Page(site, "Wikipedia:沙盒")
                for history in page.revisions(total=50, content=False):
                    username = history["user"]
                    comment = history["comment"]
                    if str(verifyCode) == str(comment):
                        accessVerifyCode("remove", userid)
                        if isEligible(str(username)):
                            accessVerifiedUsername("add", userid, username)
                            await Bot.send_message(
                                chat_id = userid,
                                text = "您的身份已验证。请使用后面的链接加入群组。 {invitelink}".format(invitelink=await getInviteLink(str(username)))
                            )
                            await Bot.send_message(
                                chat_id = config.limitedGroupID,
                                text = "我已验证 Telegram ID 为{userid}的用户的身份为{username}，并已发送邀请链接。\n #{userid}".format(userid=userid, username=str(username))
                            )
                        else:
                            await Bot.send_message(
                                chat_id = userid,
                                text = "对不起，您可能不符合入群资格。如有疑问，请加入 @YimingMB 反馈问题。"
                            )
                            await Bot.send_message(
                                chat_id = config.limitedGroupID,
                                text = "我已验证 Telegram ID 为{userid}的用户的身份为{username}，但该用户似乎不符入群资格。请群组管理员复检。\n #{userid}".format(userid=userid, username=str(username))
                            )
        else:
            time.sleep(10)

if __name__ == '__main__':
    asyncio.run(checkPolling())