import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

from telethon_db import TelethonDB

from telethon import events, TelegramClient
from telethon.tl.patched import Message
import asyncio
import re
from Config import Config

FROM = Config.FROM

TO = Config.TO


TelethonDB.creat_tables()

client = TelegramClient(
    session="telethon_session",
    api_hash=Config.API_HASH,
    api_id=Config.API_ID,
).start(phone=Config.PHONE)


@client.on(events.NewMessage(chats=FROM))
@client.on(events.Album(chats=FROM))
async def get_post(event: events.NewMessage.Event):
    gallery = getattr(event, "messages", None)
    if event.grouped_id and not gallery:
        return

    await copy_messages(event, gallery, TO)

    raise events.StopPropagation


async def copy_messages(
    event: events.NewMessage.Event, gallery: list[Message], to: list[int]
):
    stored_msg = None
    if not event.grouped_id:
        message: Message = event.message
        # Single Photo
        if (message.photo and not message.web_preview) or message.video:
            for channel in to:
                if event.is_reply:
                    stored_msg = TelethonDB.get_messages(
                        from_message_id=message.reply_to_msg_id,
                        from_channel_id=event.chat_id,
                        to_channel_id=channel,
                    )
                msg = await client.send_file(
                    channel,
                    caption=replace_content(message.text),
                    file=message.photo if message.photo else message.video,
                    reply_to=stored_msg[0] if stored_msg else None,
                )
                await TelethonDB.add_message(
                    from_message_id=message.id,
                    to_message_id=msg.id,
                    from_channel_id=event.chat_id,
                    to_channel_id=channel,
                )
        # Just Text
        else:
            for channel in to:
                if event.is_reply:
                    stored_msg = TelethonDB.get_messages(
                        from_message_id=message.reply_to_msg_id,
                        from_channel_id=event.chat_id,
                        to_channel_id=channel,
                    )
                msg = await client.send_message(
                    channel,
                    replace_content(message.text),
                    reply_to=stored_msg[0] if stored_msg else None,
                )
                await TelethonDB.add_message(
                    from_message_id=message.id,
                    to_message_id=msg.id,
                    from_channel_id=event.chat_id,
                    to_channel_id=channel,
                )
    # Albums
    else:
        for channel in to:
            if event.is_reply:
                stored_msg = TelethonDB.get_messages(
                    from_message_id=gallery[0].reply_to_msg_id,
                    from_channel_id=event.chat_id,
                    to_channel_id=channel,
                )
            msg = await client.send_file(
                channel,
                gallery,
                caption=[replace_content(m.text) for m in gallery],
                reply_to=stored_msg[0] if stored_msg else None,
            )
            await TelethonDB.add_message(
                from_message_id=gallery[0].id,
                to_message_id=msg[0].id,
                from_channel_id=event.chat_id,
                to_channel_id=channel,
            )


def replace_content(text):
    # Replace Telegram usernames
    text = re.sub(r"@[a-zA-Z0-9_]{5,32}\b", Config.USERNAME, text)

    # Replace URLs (handling various formats)
    text = re.sub(
        r"(?:(?:https?|ftp):\/\/)?(?:www\.)?[\w-]+(?:\.[\w-]+)+\S*", Config.LINK, text
    )

    return text


async def request_updates(client):
    while True:
        await client.catch_up()
        await asyncio.sleep(5)


print("Running....")
client.loop.create_task(request_updates(client))
client.run_until_disconnected()
print("Stopping....")
