import time
import json
import logging
import asyncio
import requests
from multiprocessing import Pool
from web3 import Web3
from web3.middleware import geth_poa_middleware
from telegram import Bot
from telegram.error import TelegramError
import os
from dotenv import load_dotenv
import websockets

load_dotenv()  # take environment variables from .env.

# Configuration
INFURA_URL = os.getenv('BASE_RPC')  # Replace with your Infura URL or another Ethereum node provider URL
TELEGRAM_TOKEN = os.getenv('TG_TOKEN')  # Replace with your Telegram bot token
CHAT_IDS = os.getenv('TG_CHAT_IDS').split(',')  # Comma-separated list of Telegram chat IDs
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')  # Your Etherscan API key
POLL_INTERVAL = 1  # Polling interval in seconds
IMAGE_PATH = 'image.jpg'  # Path to the image to be sent with each message
token_address_env = os.getenv('token_address')
# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory cache for token details
token_details_cache = {}

async def send_telegram_message(message, photo):
    for chat_id in CHAT_IDS:
        try:
            logger.info(f"Sending message to chat {chat_id}: {message}")
            await bot.send_photo(chat_id=chat_id, photo=open(photo, 'rb'), caption=message, parse_mode='Markdown')
            logger.info(f"Sent message to chat {chat_id}: {message}")
        except TelegramError as e:
            logger.error(f"Failed to send message to chat {chat_id}: {e}")
        await asyncio.sleep(1)  # Add a delay after sending the message to each chat

async def handle_websocket_message(data):
    try:
        logger.info(f"Handling WebSocket message: {data}")
        tx_type = data.get('type')
        token_info = data.get('tokenInfo', {})

        token_name = token_info.get('name', 'Unknown Token')
        token_symbol = token_info.get('symbol', '')
        token_address = data.get('token', 'Unknown Address')
        native_amount = data.get('nativeAmount', 0)
        token_amount = data.get('tokenAmount', 0)
        recipient = data.get('recipient', 'Unknown Recipient')
        market_cap = data.get('marketCap', 'N/A')
        token_link = f"[{token_name}](https://basescan.org/address/{token_address})"

        if tx_type == "buy" and token_address == token_address_env:
            message = (f"Buy 💰💰💰💰💰💰💰💰:\n"
                       f"Token: {token_link}\n"
                       f"[Buyer](https://basescan.org/address/{recipient})\n"
                       f"Buy Amount: {token_amount} {token_symbol}\n"
                       f"ETH Sent: {native_amount} ETH\n"
                       f"Market Cap: {market_cap} USD\n"
                       f"[Buy Here](https://omnipump.omniswap.ai/token/{token_address}?ref=0x7117b8699329347714994033f32A540215e7Be90) \n"
                       f"Buy on the [Gemach Telegram Bot](https://t.me/GemachEVM_Bot?start=435363513) \n"
                       f"Brought to you by [Arcadia](https://twitter.com/thearcadiagroup)"
                       )
            logger.info(f"Generated message: {message}")

            # Send message via Telegram
            await send_telegram_message(message, IMAGE_PATH)
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")

async def connect_to_ws():
    uri = "wss://pump-ws.omniswap.ai"
    connection_message = {"topics": "trade"}

    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(connection_message))
        logger.info(f"Sent: {connection_message}")

        while True:
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            if response == "ACK":
                logger.info("Received ACK from WebSocket server")
                continue

            try:
                data = json.loads(response)
                if data.get('type') in ['buy', 'sell']:
                    await handle_websocket_message(data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON: {e}")

async def main():
    await connect_to_ws()

if __name__ == "__main__":
    asyncio.run(main())
