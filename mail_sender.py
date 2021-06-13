import asyncio
from asyncio import queues
from email.message import EmailMessage
import aiosmtplib
import json


async def send_mail(email):
    message = EmailMessage()
    message["From"] = "login@host"  # ex: admin@example.com
    message["To"] = email
    message["Subject"] = "Sent via aiosmtplib"
    message.set_content("Сообщение является рассылкой!")

    await aiosmtplib.send(message, hostname="hostname", port=25, username="username", password="password")


async def email_sender(Q):
    while True:
        email = await Q.get()
        if email is None:
            await Q.put(None)
            break
        await send_mail(email)


async def main(*args):
    Q = queues.Queue(maxsize=5)
    senders = []
    for _ in range(10):
        sender = asyncio.create_task(email_sender(Q))
        senders.append(sender)
    for mail in args[0]:
        await Q.put(mail)
    await Q.put(None)
    for sender in senders:
        await sender


def start(*args):
    asyncio.run(main(args))
    return json.dumps({'status': True})
