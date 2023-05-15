import asyncio
import os
import re

from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.raw import functions
from pyrogram.errors import PeerFlood, AuthKeyUnregistered, InputUserDeactivated, PeerIdInvalid, FloodWait, \
    SessionRevoked, ChatAdminRequired, ChatWriteForbidden, UserBannedInChannel, ChannelPrivate, AuthKeyDuplicated, \
    SlowmodeWait, UserDeactivated, UserDeactivatedBan

api_id = 24651572
api_hash = '6f5caff63de033cb0725399b5961ad7d'


async def for_dialogs(app, text, time_sleep, archivr_chats: bool):
    global n
    try:
        async for dialog in app.get_dialogs():
            if dialog.chat.type == ChatType.PRIVATE:
                try:
                    await app.send_message(dialog.chat.id, text, disable_web_page_preview=True)
                    if archivr_chats:
                        await app.archive_chats(dialog.chat.id)
                    n += 1
                    print(f'Message sent to {dialog.chat.first_name}')
                    await asyncio.sleep(time_sleep)
                except PeerFlood:
                    await asyncio.sleep(5)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except InputUserDeactivated:
                    continue
            elif dialog.chat.type == ChatType.CHANNEL:
                try:
                    await app.send_message(dialog.chat.id, text, disable_web_page_preview=True)
                    n += 1
                    await asyncio.sleep(time_sleep)
                except PeerFlood:
                    await asyncio.sleep(3)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except (ChatAdminRequired, UserBannedInChannel):
                    continue
            elif dialog.chat.type == ChatType.GROUP:
                try:
                    await app.send_message(dialog.chat.id, text, disable_web_page_preview=True)
                    await app.archive_chats(dialog.chat.id)
                    n += 1
                    await asyncio.sleep(time_sleep)
                except PeerFlood:
                    await asyncio.sleep(3)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except (UserBannedInChannel, PeerIdInvalid):
                    continue
            elif dialog.chat.type == ChatType.SUPERGROUP:
                try:
                    await app.send_message(dialog.chat.id, text, disable_web_page_preview=True)
                    await app.archive_chats(dialog.chat.id)
                    n += 1
                    await asyncio.sleep(3)
                except PeerFlood:
                    await asyncio.sleep(3)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except (ChatWriteForbidden, UserBannedInChannel, ChannelPrivate):
                    continue
    except ChannelPrivate:
        pass
async def for_contacts(app, text, time_sleep, archivr_chats: bool):
    global n
    for contact in await app.get_contacts():
        try:
            await app.send_message(contact.id, text, disable_web_page_preview=True)
            if archivr_chats:
                await app.archive_chats(contact.id)
            n += 1
            print(f'Message sent to the contact {contact.first_name}')
            await asyncio.sleep(time_sleep)
        except PeerFlood:
            await asyncio.sleep(3)
        except FloodWait as e:
            await asyncio.sleep(e.value)

async def delete_history(app):
    d = 0
    async for dialog in app.get_dialogs():
        try:
            await app.invoke(
                functions.messages.DeleteHistory(peer=await app.resolve_peer(dialog.chat.id), max_id=0, revoke=False,
                                                 just_clear=True))
            d += 1
        except PeerIdInvalid:
            continue
    print(f'Deleted messages: {d}')

async def get_chats(app):
    count_new_chats = 0
    async for dialog in app.get_dialogs():
        if dialog.chat.type == ChatType.SUPERGROUP or dialog.chat.type == ChatType.GROUP:
            try:
                open_chat = await app.get_chat(dialog.chat.id)
                if open_chat.username is not None:
                    chat_for = f"https://t.me/{open_chat.username}, @{open_chat.username}"
                    with open('chats.txt', 'a+') as file:
                        file.seek(0)
                        chats = [word for line in file for word in line.split('\n')]
                        if chat_for not in chats:
                            file.write(str(chat_for+'\n'))
                            count_new_chats += 1
                            await asyncio.sleep(1)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except ChannelPrivate:
                continue
    print(f"Added chats: {count_new_chats}")

async def spam_for_chats(app, text, sleep_time):
    global n
    with open('chats.txt', 'r') as f:
        for chat in re.findall(r"(?:http(?:s|)://|)t\.me/\w+", f.read()):
            try:
                await app.join_chat(chat.split(', @')[1])
                await asyncio.sleep(sleep_time)
                await app.send_message(chat.split(', @')[1], text)
                n += 1
                print(f"Sent message to {chat}")
            except PeerFlood:
                await asyncio.sleep(3)
            except (FloodWait, SlowmodeWait) as e:
                await asyncio.sleep(e.value)
            except (UserBannedInChannel, PeerIdInvalid, ChatWriteForbidden):
                continue
            except KeyError:
                continue

n = 0
async def spam():
    text = input('Enter text for message: ')
    delay = int(input('Enter a delay in sending messages'))
    get_chat = True if input("Download all groups from accounts?('y' or 'n'): ") == 'y' else False
    spam_contacts = True if input("Send messages to the contacts?('y' or 'n'): ") == 'y' else False
    archived = True if input("Archive messages after mailing?('y' or 'n'): ") == 'y' else False
    delete_messages = True if input("Delete messages after mailing?('y' or 'n'): ") == 'y' else False
    for session in os.listdir(path="./sessions"):
        try:
            async with Client(f"sessions/{session.split('.session')[0]}", api_id, api_hash) as app:
                if get_chat:
                    print(f"\nStarted download all groups from {session}\n")
                    await get_chats(app)
                    print(f"\nDownload all groups from {session}\n")
                print(f'Started sent message to {session}')
                await for_dialogs(app, text=text, archivr_chats=archived, time_sleep=delay)
                print('\nChat painting completed')
                print(f'Sent messages: {n}\n')
                if spam_contacts:
                    await for_contacts(app, text=text, archivr_chats=archived, time_sleep=delay)
                    print('\nPainting on contacts completed')
                    print(f'\nSent messages: {n}\n')
                if delete_messages:
                    await delete_history(app=app)
                    print("All chats deleted")
                print('End')

        except AuthKeyDuplicated as e:
            print(f"Error: {e}")
        except TimeoutError as e:
            print(e)
        except (UserDeactivated, UserDeactivatedBan, SessionRevoked, AuthKeyUnregistered):
            print(f'Session {session} died')


if __name__ == "__main__":
    asyncio.run(spam())
