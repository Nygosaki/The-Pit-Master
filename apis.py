import finnhub
import os
from dotenv import load_dotenv

global client
load_dotenv()
FINNHUB_TOKEN = os.getenv("FINNHUB_TOKEN")
client = finnhub.Client(api_key=FINNHUB_TOKEN)

def getPrice(item: str) -> float:
    return client.quote(item.upper())["c"]