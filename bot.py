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

PROMOTION_REQUIREMENT = 32 * 60  # 32 hours in minutes

def get_now():
    return datetime.now(EASTERN)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"weekly": 0, "monthly": 0, "promotion": 0, "last_weekly_reset": "", "last_monthly_reset": ""}
    data = json.load(open(DATA_FILE))
    if "promotion" not in data:
        data["promotion"] = 0
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def maybe_reset(data):
    now = get_now()
    week_key = now.strftime("%Y-W%U")
    if now.weekday() == 6:
        week_key = now.strftime("%Y-W%U-SUN")
    if data["last_weekly_reset"] != week_key and now.weekday() == 6 and now.hour == 0:
        data["weekly"] = 0
        data["last_weekly_reset"] = week_key
    month_key = now.strftime("%Y-%m")
    if data["last_monthly_reset"] != month_key:
        data["monthly"] = 0
        data["last_monthly_reset"] = month_key
    return data

def format_time(minutes):
    h = minutes // 60
    m = minutes % 60
    return f"{h} hours {m} minutes"

def promotion_status(minutes):
    remaining = max(0, PROMOTION_REQUIREMENT - minutes)
    percent = min(100, int((minutes / PROMOTION_REQUIREMENT) * 100))
    if minutes >= PROMOTION_REQUIREMENT:
        return f"{format_time(minutes)} / 32 hours ✅ **REQUIREMENT MET**"
    else:
        return f"{format_time(minutes)} / 32 hours — {format_time(remaining)} remaining ({percent}%)"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

@tree.command(name="addaccess", description="Add time to your Roblox access totals")
@app_commands.describe(hours="How many hours to add", minutes="How many minutes to add")
async def addaccess(interaction: discord.Interaction, hours: int = 0, minutes: int = 0):
    data = load_data()
    data = maybe_reset(data)
    total = (hours * 60) + minutes
    data["weekly"] += total
    data["monthly"] += total
    data["promotion"] += total
    save_data(data)
    embed = discord.Embed(color=0x5865F2)
    embed.description = (
        f"Added {hours}h {minutes}m to both access totals.\n"
        f"Total Weekly Access = {format_time(data['weekly'])} ✅\n"
        f"Total Monthly Access = {format_time(data['monthly'])} ✅\n\n"
        f"**Promotion Requirement:** {promotion_status(data['promotion'])}"
    )
    await interaction.response.send_message(embed=embed)

@tree.command(name="access", description="Check your Roblox playtime totals")
async def access(interaction: discord.Interaction):
    data = load_data()
    data = maybe_reset(data)
    save_data(data)
    embed = discord.Embed(color=0x5865F2)
    embed.description = (
        f"Total Weekly Access = {format_time(data['weekly'])} ✅\n"
        f"Total Monthly Access = {format_time(data['monthly'])} ✅\n\n"
        f"**Promotion Requirement:** {promotion_status(data['promotion'])}"
    )
    await interaction.response.send_message(embed=embed)

@tree.command(name="clearaccess", description="Reset your Roblox access totals")
async def clearaccess(interaction: discord.Interaction):
    data = load_data()
    data["weekly"] = 0
    data["monthly"] = 0
    save_data(data)
    embed = discord.Embed(color=0x5865F2)
    embed.description = (
        f"Access totals have been reset. ✅\n"
        f"Total Weekly Access = 0 hours 0 minutes ✅\n"
        f"Total Monthly Access = 0 hours 0 minutes ✅"
    )
    await interaction.response.send_message(embed=embed)

@tree.command(name="resetpromotionrequirement", description="Reset the promotion requirement progress")
async def resetpromotionrequirement(interaction: discord.Interaction):
    data = load_data()
    data["promotion"] = 0
    save_data(data)
    embed = discord.Embed(color=0x5865F2)
    embed.description = "Promotion requirement has been reset. ✅\n**Promotion Requirement:** 0 hours 0 minutes / 32 hours — 32 hours remaining (0%)"
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
