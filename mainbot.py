import discord
from discord.ext import commands
import pandas as pd
import io
import re

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # This is required for message commands

bot = commands.Bot(command_prefix='!', intents=intents)

# Load the spreadsheet data
# For now, I'll create a sample data structure - you'll need to adapt this to read your actual spreadsheet
runes_data = {
    "Bloom": {
        "rarity": "1/7.5B",
        "category": "Color Rune",
        "max": "No Limit",
        "stats": "1k Boost Spheres [No Limit] + Talent Upgrade (Prisms Talent Tree)"
    },
    "Mystery": {
        "rarity": "1/1T",
        "category": "Basic Rune",
        "max": "4k",
        "stats": "x1 Rune Bulk (MAX x5) + -0.1s RToken Cooldown (MAX -60s)"
    },
    "Hyper Finality": {
        "rarity": "1/750No",
        "category": "Basic Rune",
        "max": "110.54k",
        "stats": "x1 Rune Speed [EXPONENTIAL] (MAX x1T)+ Ticket Perks Upgrade",
        "formula": "1.00025^(number of HF)"
    },
    "Thorn": {
        "rarity": "1/10T",
        "category": "Nature Rune",
        "max": "500k for Rune Speed, 7.5B for Tickets",
        "stats": "Ticket Perks Upgrade (Rune Bulk) + x1.05 Rune Speed (MAX x25k) + x2.5 Tickets (MAX x10B)"
    },
    "Aether": {
        "rarity": "1/15B",
        "category": "Polychrome Rune",
        "max": "9K",
        "stats": "Rune Luck (MAX x10) + Talent Upgrade (Prisms Talent Tree, Hidden from a big rock on right side)"
    },
    "Vexed": {
        "rarity": "1/50B",
        "category": "Polychrome Rune",
        "max": "40",
        "stats": "x1.05 Tickets (MAX x3) + Talent Upgrade (Realm 2, Hidden close of Cyro Rune on Right side from a floating island)"
    },
    "Blizzard": {
        "rarity": "1/100B",
        "category": "Arctic Rune",
        "max": "6",
        "stats": "x1.05 Rune Bulk (MAX x1.3) + Ticket Perk (Rune Luck)"
    },
    "Kingslayer": {
        "rarity": "1/250B",
        "category": "ORDER",
        "max": "400",
        "stats": "x25K Orbs [EXPONENTIAL] (MAX x1NoNg) + x1.25 Rune Luck (MAX x100) + x1.25 Rune Speed (MAX x100)",
        "effect": "+0.25x rune luck/speed per rune"
    }
    # Add more runes as needed
}

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in!')

@bot.command(name='rune')
async def get_rune_info(ctx, *, rune_name: str):
    """Get information about a specific rune"""
    # Try to find the rune (case insensitive)
    rune_info = None
    found_name = None
    
    for name, info in runes_data.items():
        if name.lower() == rune_name.lower():
            rune_info = info
            found_name = name
            break
        elif rune_name.lower() in name.lower():
            rune_info = info
            found_name = name
            break
    
    if not rune_info:
        # Try partial match
        for name, info in runes_data.items():
            if rune_name.lower() in name.lower():
                rune_info = info
                found_name = name
                break
    
    if not rune_info:
        await ctx.send(f"Rune '{rune_name}' not found. Try another name!")
        return
    
    # Create embed response
    embed = discord.Embed(
        title=f"{found_name} Rune",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Rarity", value=rune_info.get("rarity", "N/A"), inline=True)
    embed.add_field(name="Category", value=rune_info.get("category", "N/A"), inline=True)
    embed.add_field(name="Max Value", value=rune_info.get("max", "N/A"), inline=False)
    embed.add_field(name="Stats", value=rune_info.get("stats", "N/A"), inline=False)
    
    if "formula" in rune_info:
        embed.add_field(name="Formula", value=rune_info["formula"], inline=False)
    
    if "effect" in rune_info:
        embed.add_field(name="Effect", value=rune_info["effect"], inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='runes')
async def list_runes(ctx):
    """List all available runes"""
    rune_list = "\n".join([f"• {name}" for name in runes_data.keys()])
    
    embed = discord.Embed(
        title="Available Runes",
        description=rune_list,
        color=discord.Color.green()
    )
    
    await ctx.send(embed=embed)

@bot.command(name='category')
async def list_category_runes(ctx, *, category: str):
    """List runes by category (Basic, Color, Nature, etc.)"""
    category_runes = []
    category_lower = category.lower()
    
    for name, info in runes_data.items():
        if info.get("category", "").lower() == category_lower:
            category_runes.append(f"• {name} ({info.get('rarity', 'N/A')})")
    
    if not category_runes:
        await ctx.send(f"No runes found in category '{category}'")
        return
    
    rune_list = "\n".join(category_runes)
    
    embed = discord.Embed(
        title=f"{category} Runes",
        description=rune_list,
        color=discord.Color.purple()
    )
    
    await ctx.send(embed=embed)

# Run the bot
bot.run('MTQwMzA5ODAzMTU2MTM3OTkzMg.Ge0J6u._XBDfty_a_0mpXX3dP1C_6o5MGAjx4hZu2GEDA')
