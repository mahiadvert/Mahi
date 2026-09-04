import asyncio
import logging
import random
import os
from telethon import TelegramClient, events, errors, functions
from telethon.sessions import StringSession, MemorySession
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

API_ID = int(os.getenv("API_ID", "35299699"))
API_HASH = os.getenv("API_HASH", "5d2740679fc529a1ca52f479a74bcfeb")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8681729506:AAFAY-_roLbuXUMmwO7uYraJzckqoVTB8bY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8828879573"))
USER_SESSION_STRING = os.getenv("USER_SESSION_STRING", "")

SOURCE_CHAT = "RoboroHq"

TARGET_GROUPS = [
    ("@aizenmarket", 21),
    ("@RareHandle", 79),
    ("@Nitroraid", 1007631),
    ("@buffestmarket", 20),
    ("@guremarketplace", 2),
    ("@stockless", 39),
    ("@totalsmp", 3757448),
    ("@iinvd", 120080),
    ("@Escrowplace", 21),
    ("@marketogs", 127871),
    ("@kimsocialMP", 2),
]

IS_RUNNING = True
INTERVAL_SECONDS = 3900

# MemorySession stops sqlite database lock errors
user_client = TelegramClient(StringSession(USER_SESSION_STRING) if USER_SESSION_STRING else MemorySession(), API_ID, API_HASH)
bot_client = TelegramClient(MemorySession(), API_ID, API_HASH)


async def broadcast_cycle():
    global IS_RUNNING
    while True:
        try:
            try:
                source_peer = await user_client.get_input_entity(SOURCE_CHAT)
                messages = await user_client.get_messages(SOURCE_CHAT, limit=1)
                source_msg = messages[0] if messages else None
            except Exception as e:
                source_msg = None
                logging.error(f"Error fetching source entity/message: {e}")

            if not source_msg:
                await bot_client.send_message(ADMIN_ID, "❌ **Error:** Source post nahi mila!")
                await asyncio.sleep(300)
                continue

            success, failed = 0, 0

            for group, topic_id in TARGET_GROUPS:
                if not IS_RUNNING:
                    break

                try:
                    target_peer = await user_client.get_input_entity(group)
                    
                    # Native Telegram Raw Forward Request
                    await user_client(functions.messages.ForwardMessagesRequest(
                        from_peer=source_peer,
                        id=[source_msg.id],
                        to_peer=target_peer,
                        top_msg_id=topic_id if topic_id else None,
                        random_id=[random.randint(-2**63, 2**63 - 1)]
                    ))
                    
                    success += 1
                    logging.info(f"[+] NATIVELY FORWARDED to {group} (Topic: {topic_id})")
                except errors.FloodWaitError as e:
                    logging.warning(f"Rate limited! Pausing for {e.seconds + 5}s")
                    await asyncio.sleep(e.seconds + 5)
                    continue
                except Exception as e:
                    failed += 1
                    logging.error(f"Failed delivery to {group}: {e}")

                await asyncio.sleep(random.randint(15, 25))

            await bot_client.send_message(
                ADMIN_ID,
                f"📢 **Broadcast Round Finished!**\n\n✅ Success: `{success}`\n❌ Failed: `{failed}`\n\n⏰ Next round in `{INTERVAL_SECONDS // 60}` minutes.",
            )

        except Exception as e:
            logging.error(f"Broadcast cycle error: {e}")

        await asyncio.sleep(INTERVAL_SECONDS)


async def main():
    await user_client.start()
    
    if not USER_SESSION_STRING:
        print("\n" + "="*50)
        print("YOUR USER_SESSION_STRING:")
        print(user_client.session.save())
        print("="*50 + "\n")

    await bot_client.start(bot_token=BOT_TOKEN)
    await user_client.get_dialogs()
    logging.info("Both User Client and Bot Client are Online!")
    asyncio.create_task(broadcast_cycle())
    await bot_client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())