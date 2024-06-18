import os
import json
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("TOKEN")
TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID", ""))  # Add your test guild ID here

# File to store settings
SETTINGS_FILE = "settings.json"

# Load existing settings or initialize an empty dictionary
settings = {}


def load_settings():
    global settings
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
            print("Settings loaded successfully.")
    else:
        save_settings()  # Create an empty settings file if it doesn't exist


def save_settings():
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
        print("Settings saved successfully.")
    except Exception as e:
        print(f"Error saving settings: {e}")


# Load settings on startup
load_settings()

# Initialize bot
intents = discord.Intents.default()
intents.reactions = True  # Enable reaction intents
intents.guilds = True  # Enable guild intents
intents.messages = True  # Enable message intents
client = commands.Bot(command_prefix="!", intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    try:
        # Sync global commands
        synced_global = await client.tree.sync()
        print(f"Successfully synced {len(synced_global)} global command(s)")
    except Exception as e:
        print(f"Error syncing global commands: {e}")

    try:
        # Sync guild-specific commands
        test_guild = discord.Object(id=TEST_GUILD_ID)
        synced_guild = await client.tree.sync(guild=test_guild)
        print(
            f"Successfully synced {len(synced_guild)} guild command(s) in {TEST_GUILD_ID}"
        )
    except Exception as e:
        print(f"Error syncing guild commands: {e}")


# Command to set the verification channel
@client.tree.command(
    name="set_verification_channel", description="Set the verification channel"
)
@app_commands.checks.has_permissions(administrator=True)
@app_commands.guilds(
    discord.Object(id=TEST_GUILD_ID)
)  # Ensure this command is specific to the test guild
async def set_verification_channel(
    interaction: discord.Interaction, channel: discord.TextChannel
):
    guild_id = str(interaction.guild.id)
    settings[guild_id] = settings.get(guild_id, {})
    settings[guild_id]["verification_channel"] = channel.id
    save_settings()
    await interaction.response.send_message(
        f"Verification channel set to {channel.mention}", ephemeral=True
    )


# Command to set the verification role
@client.tree.command(
    name="set_verification_role", description="Set the verification role"
)
@app_commands.checks.has_permissions(administrator=True)
@app_commands.guilds(
    discord.Object(id=TEST_GUILD_ID)
)  # Ensure this command is specific to the test guild
async def set_verification_role(interaction: discord.Interaction, role: discord.Role):
    guild_id = str(interaction.guild.id)
    settings[guild_id] = settings.get(guild_id, {})
    settings[guild_id]["verification_role"] = role.id
    save_settings()
    await interaction.response.send_message(
        f"Verification role set to {role.name}", ephemeral=True
    )


# Command to start the verification process
@client.tree.command(
    name="start_verification", description="Start the verification process"
)
@app_commands.checks.has_permissions(administrator=True)
@app_commands.guilds(
    discord.Object(id=TEST_GUILD_ID)
)  # Ensure this command is specific to the test guild
async def start_verification(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    settings[guild_id] = settings.get(guild_id, {})
    if not settings[guild_id].get("verification_channel") or not settings[guild_id].get(
        "verification_role"
    ):
        await interaction.response.send_message(
            "Verification channel or role is not set up.", ephemeral=True
        )
        return

    channel = client.get_channel(settings[guild_id]["verification_channel"])
    if not channel:
        await interaction.response.send_message(
            "Verification channel not found.", ephemeral=True
        )
        return

    try:
        verification_message = await channel.send(
            "React to this message to verify yourself!"
        )
        settings[guild_id]["verification_message"] = verification_message.id
        save_settings()
        await verification_message.add_reaction("✅")
        await interaction.response.send_message(
            "Verification process started!", ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to send messages in the verification channel.",
            ephemeral=True,
        )
    except discord.HTTPException:
        await interaction.response.send_message(
            "Failed to send verification message. Please try again later.",
            ephemeral=True,
        )


@client.event
async def on_raw_reaction_add(payload):
    if payload.member.bot:
        return

    guild_id = str(payload.guild_id)
    if guild_id not in settings:
        return

    message_id = settings[guild_id].get("verification_message")
    role_id = settings[guild_id].get("verification_role")

    if not message_id or not role_id:
        return

    if payload.message_id != message_id:
        return

    guild = client.get_guild(payload.guild_id)
    role = guild.get_role(role_id)

    if role:
        member = guild.get_member(payload.user_id)
        await member.add_roles(role)


# Run the bot with the token
client.run(TOKEN)
