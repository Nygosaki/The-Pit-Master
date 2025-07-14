import discord
from collections import defaultdict
from apis import getPrice
import json
from copy import deepcopy
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

global customers
customers = defaultdict(lambda: {"portfolio": defaultdict(int), "balance": 1000.0, "transactions": []})

try:
    with open("customers.json", "r") as f:
        customers.update(json.load(f))
        for customer in customers.values():
            portfolio_data = customer.get("portfolio", {})
            if isinstance(portfolio_data, (dict, defaultdict)):
                customer["portfolio"] = defaultdict(
                    int,
                    {str(k): int(v) for k, v in dict(portfolio_data).items()}
                )
            else:
                customer["portfolio"] = defaultdict(int)
except (FileNotFoundError, json.JSONDecodeError):
    pass

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    
    msgParts = message.content.lower().split(' ')
    global customers

    if msgParts[0] == 'buy':
        customer = customers[message.author.name]
        portfolio = customer["portfolio"]
        balance = customer["balance"] if isinstance(customer["balance"], (int, float)) else 0.0
        symbol = msgParts[2]
        qty = int(msgParts[1])

        price = getPrice(symbol)

        portfolio[symbol] += qty
        balance -= (qty * price)
        customer["balance"] = balance
        if not isinstance(customer["transactions"], list): customer["transactions"] = []
        customer["transactions"].append({
            "type": "buy",
            "symbol": symbol.upper(),
            "quantity": qty,
            "price": price,
            "total": qty * price
        })

        await message.channel.send(f"Bought {qty} of {symbol.upper()} at ${price}! \nYou now have: {portfolio[symbol]} w/ ${balance}")
    elif msgParts[0] == 'sell':
        customer = customers[message.author.name]
        portfolio = customer["portfolio"]
        balance = customer["balance"] if isinstance(customer["balance"], (int, float)) else 0.0
        symbol = msgParts[2]
        qty = int(msgParts[1])

        price = getPrice(symbol)

        portfolio[symbol] -= qty
        balance += (qty * price)
        customer["balance"] = balance
        if not isinstance(customer["transactions"], list): customer["transactions"] = []
        customer["transactions"].append({
            "type": "sell",
            "symbol": symbol.upper(),
            "quantity": qty,
            "price": price,
            "total": qty * price
        })

        await message.channel.send(f"Sold {qty} of {symbol.upper()} at ${price}! \nYou now have: {portfolio[symbol]} w/ ${balance}")
    elif msgParts[0] == 'price':
        symbol = msgParts[1]
        price = getPrice(symbol)
        await message.channel.send(f"The current price of {symbol.upper()} is ${price}")
    elif msgParts[0] == 'portfolio':
        await message.channel.send(f"Your portfolio: {customers[message.author.name]['portfolio']} \nYour balance: ${customers[message.author.name]['balance']}")
    elif msgParts[0] == 'leaderboard':
        customersTemp = deepcopy(customers)
        leaderboard_entries = []
        for customer in customersTemp:
            additives = 0.0
            portfolio = customersTemp[customer].get("portfolio", {})
            for symbol, qty in portfolio.items():
                if qty != 0:
                    additives += (getPrice(symbol) * qty)
            total_balance = customersTemp[customer]["balance"] + additives
            leaderboard_entries.append((customer, total_balance))
        
        leaderboard_entries.sort(key=lambda x: x[1], reverse=True)
        
        leaderboard_str = "**Leaderboard:**\n"
        for idx, (customer, total_balance) in enumerate(leaderboard_entries, 1):
            leaderboard_str += f"{idx}. {customer}: ${total_balance:,.2f}\n"
        
        await message.channel.send(leaderboard_str)
    
    with open("customers.json", "w") as f:
        json.dump(customers, f, default=lambda x: dict(x) if isinstance(x, defaultdict) else x, indent=4)

client.run(os.getenv("DISCORD_TOKEN"))
