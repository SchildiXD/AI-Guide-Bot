import discord
from discord.ext import commands
import pandas as pd
import os
import re
from flask import Flask
from threading import Thread
import uuid
import asyncio

# Create a unique instance ID for this bot instance
INSTANCE_ID = str(uuid.uuid4())[:8]
print(f"Starting bot instance: {INSTANCE_ID}")

# Flask web server to satisfy Render's port detection
app = Flask('')
app.instance_id = INSTANCE_ID

@app.route('/')
def home():
    return f"Bot is running! Instance: {INSTANCE_ID}"

def run():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # This is required for message commands

bot = commands.Bot(command_prefix='!', intents=intents)

# Track active instances
active_instances = {INSTANCE_ID: asyncio.get_event_loop().time()}

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in! Instance: {INSTANCE_ID}')
    print(f'Loaded {len(runes_data)} runes')
    
    # Register this instance as active
    active_instances[INSTANCE_ID] = asyncio.get_event_loop().time()

@bot.event
async def on_message(message):
    # Prevent bot from responding to itself
    if message.author == bot.user:
        return
    
    # Only process messages if this is the most recent instance
    current_time = asyncio.get_event_loop().time()
    
    # Clean up old instances (older than 60 seconds)
    expired_instances = []
    for instance_id, start_time in active_instances.items():
        if current_time - start_time > 60:
            expired_instances.append(instance_id)
    
    for expired in expired_instances:
        del active_instances[expired]
    
    # Only process if this is the most recent instance
    if active_instances:
        most_recent_instance = max(active_instances.keys(), key=lambda x: active_instances[x])
        if INSTANCE_ID != most_recent_instance:
            return
    
    # Process commands
    await bot.process_commands(message)

# Function to parse the Excel file and extract rune data
def load_runes_from_excel():
    runes = {}
    
    try:
        # Check if file exists
        if not os.path.exists('BROT13.xlsx'):
            print("ERROR: BROT13.xlsx file not found!")
            return {}
        
        print("Loading runes from BROT13.xlsx...")
        df = pd.read_excel('BROT13.xlsx', sheet_name='Better Rune Order (T13 Late Gam', header=None)
        print(f"Successfully loaded Excel file with {len(df)} rows")
        
        # Parse the data to extract rune information
        current_category = ""
        
        for index, row in df.iterrows():
            # Skip empty rows
            if row.isna().all():
                continue
                
            # Convert row to list and filter out NaN values
            row_data = [str(cell) for cell in row if pd.notna(cell)]
            
            # Look for category headers (rows that contain "Rune:")
            for cell in row_data:
                if "Rune:" in cell and not cell.startswith("http"):
                    current_category = cell.strip()
                    break
            
            # Look for rune entries (cells that contain rarity patterns like "1/")
            for cell in row_data:
                if "1/" in cell and not cell.startswith("http"):
                    # Extract rune name and rarity
                    # Pattern: (rarity) RuneName or Rarity RuneName
                    match = re.search(r'[([]?(1/[\d.]+[A-Za-z]*)[)\]]?\s+([A-Za-z\s]+)', cell)
                    if match:
                        rarity = match.group(1)
                        rune_name = match.group(2).strip()
                        
                        # Get stats from the next row if available
                        stats = "Stats not found in spreadsheet"
                        if index + 1 < len(df):
                            next_row = df.iloc[index + 1]
                            next_row_data = [str(cell) for cell in next_row if pd.notna(cell)]
                            if next_row_data:
                                # Look for stats in the same column or nearby
                                for next_cell in next_row_data:
                                    if "Stats:" in next_cell or ("x" in next_cell and len(next_cell) > 10):
                                        stats = next_cell.replace("Stats:", "").strip()
                                        break
                        
                        runes[rune_name] = {
                            "rarity": rarity,
                            "category": current_category if current_category else "Unknown",
                            "stats": stats
                        }
                    
        print(f"Loaded {len(runes)} runes from spreadsheet")
        return runes
    
    except Exception as e:
        print(f"Error loading runes from Excel: {e}")
        # Return sample data if Excel parsing fails
        return {
            "Bloom": {
                "rarity": "1/7.5B",
                "category": "Color Rune",
                "stats": "1k Boost Spheres [No Limit] + Talent Upgrade (Prisms Talent Tree)"
            },
            "Mystery": {
                "rarity": "1/1T",
                "category": "Basic Rune",
                "stats": "x1 Rune Bulk (MAX x5) + -0.1s RToken Cooldown (MAX -60s)"
            }
        }

# Load runes when bot starts
runes_data = load_runes_from_excel()

# Remove default help command to prevent duplicates
bot.remove_command('help')

@bot.command(name='ping')
async def ping(ctx):
    """Check if the bot is responsive"""
    latency = bot.latency * 1000  # Convert to milliseconds
    await ctx.send(f'Pong! Latency: {latency:.2f}ms (Instance: {INSTANCE_ID})')

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
    embed.add_field(name="Stats", value=rune_info.get("stats", "N/A"), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='runes')
async def list_runes(ctx):
    """List all available runes"""
    if not runes_data:
        await ctx.send("No runes data available.")
        return
        
    rune_list = "\n".join([f"• {name} ({info.get('rarity', 'N/A')})" for name, info in list(runes_data.items())[:20]])
    
    embed = discord.Embed(
        title="Available Runes (First 20)",
        description=rune_list,
        color=discord.Color.green()
    )
    
    await ctx.send(embed=embed)

@bot.command(name='category')
async def list_category_runes(ctx, *, category: str):
    """List runes by category"""
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

@bot.command(name='search')
async def search_runes(ctx, *, query: str):
    """Search for runes by name or rarity"""
    matching_runes = []
    query_lower = query.lower()
    
    for name, info in runes_data.items():
        if (query_lower in name.lower() or 
            query_lower in info.get("rarity", "").lower() or
            query_lower in info.get("category", "").lower()):
            matching_runes.append(f"• {name} ({info.get('rarity', 'N/A')}) - {info.get('category', 'N/A')}")
    
    if not matching_runes:
        await ctx.send(f"No runes found matching '{query}'")
        return
    
    # Limit to first 10 results
    rune_list = "\n".join(matching_runes[:10])
    
    embed = discord.Embed(
        title=f"Search Results for '{query}'",
        description=rune_list,
        color=discord.Color.orange()
    )
    
    await ctx.send(embed=embed)


@bot.command(name='latest')
async def latest_runes(ctx):
    """Show the latest recommended runes from the spreadsheet"""
    if not runes_data:
        await ctx.send("No runes data available.")
        return
    
    # Get runes from the "Recommended" section (first few rows)
    recommended_runes = [
        "Bloom", "Vexed", "Blizzard", "Aether", "Kingslayer", 
        "Mystery", "Thorn", "Divinity", "Abyssium", "Prosperity"
    ]
    
    rune_list = []
    for rune_name in recommended_runes[:8]:  # Show first 8
        if rune_name in runes_data:
            rarity = runes_data[rune_name].get("rarity", "N/A")
            rune_list.append(f"• **{rune_name}** ({rarity})")
    
    if not rune_list:
        await ctx.send("Could not load recommended runes.")
        return
    
    embed = discord.Embed(
        title="📈 Latest Recommended Runes",
        description="Top priority runes to grind:\n" + "\n".join(rune_list),
        color=discord.Color.teal()
    )
    
    embed.set_footer(text="Based on current T13 late game progression")
    
    await ctx.send(embed=embed)



@bot.command(name='help')
async def help_command(ctx):
    """Display help information"""
    embed = discord.Embed(
        title="Ascenders Incremental Bot Help",
        description="Commands for getting rune information:",
        color=discord.Color.gold()
    )
    
    embed.add_field(name="!rune [rune_name]", value="Get detailed information about a specific rune", inline=False)
    embed.add_field(name="!runes", value="List all available runes", inline=False)
    embed.add_field(name="!category [category]", value="List runes by category (Basic, Color, Nature, etc.)", inline=False)
    embed.add_field(name="!search [query]", value="Search for runes by name, rarity, or category", inline=False)
    embed.add_field(name="!ping", value="Check if the bot is responsive", inline=False)
    
    await ctx.send(embed=embed)

# Keep the bot running on the correct port for Render
if __name__ == "__main__":
    keep_alive()  # Start the web server
    bot.run(os.getenv('DISCORD_TOKEN'))  # Start the Discord bot