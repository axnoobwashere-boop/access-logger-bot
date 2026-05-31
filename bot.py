import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
import pytz

TOKEN = os.environ.get("TOKEN")
DATA_FILE = "data.json"
EASTERN = pytz.timezone("America/New_York")

def get_now():
    return datetime.now(EASTERN)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"weekly": 0, "monthly": 0, "last_weekly_reset": "", "last_monthly_reset": ""}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def maybe_reset(data):
    now = get_now()
    # Weekly reset — Sunday 12am
    week_key = now.strftime("%Y-W%U")
    if now.weekday() == 6:
        week_key = now.strftime("%Y-W%U-SUN")
    if data["last_weekly_reset"] != week_key and now.weekday() == 6 and now.hour == 0:
        data["weekly"] = 0
        data["last_weekly_reset"] = week_key
    # Monthly reset — 1st of month 12am
    month_key = now.strftime("%Y-%m")
    if data["last_monthly_reset"] != month_key:
        data["monthly"] = 0
        data["last_monthly_reset"] = month_key
    return data

def format_time(minutes):
    h = minutes // 60
    m = minutes % 60
    return f"{h} hours {m} minutes"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

@tree.command(name="addaccess", description="Add minutes to your Roblox access totals")
@app_commands.describe(minutes="How many minutes to add")
async def addaccess(interaction: discord.Interaction, minutes: int):
    data = load_data()
    data = maybe_reset(data)
    data["weekly"] += minutes
    data["monthly"] += minutes
    save_data(data)
    embed = discord.Embed(color=0x5865F2)
    embed.description = (
        f"Added {minutes} minute{'s' if minutes != 1 else ''} to both access totals.\n"
        f"Total Weekly Access = {format_time(data['weekly'])} ✅\n"
        f"Total Monthly Access = {format_time(data['monthly'])} ✅"
    )
    await interaction.response.send_message(embed=embed)

@tree.command(name="clearaccess", description="Reset your Roblox access totals")
async def clearaccess(interaction: discord.Interaction):
    data = load_data()
    data["weekly"] = 0
    data["monthly"] = 0
    save_data(data)
    embed = discord.Embed(color=0x5865F2)
    embed.description = "Access totals have been reset. ✅\nTotal Weekly Access = 0 hours 0 minutes ✅\nTotal Monthly Access = 0 hours 0 minutes ✅"
    await interaction.response.send_message(embed=embed)

@tree.command(name="access", description="Check your Roblox playtime totals")
async def access(interaction: discord.Interaction):
    data = load_data()
    data = maybe_reset(data)
    save_data(data)
    embed = discord.Embed(color=0x5865F2)
    embed.description = (
        f"Total Weekly Access = {format_time(data['weekly'])} ✅\n"
        f"Total Monthly Access = {format_time(data['monthly'])} ✅"
    )
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
