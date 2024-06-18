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
SETTINGS_FILE = "./PloitZ/settings.json"

# Initialize settings with an empty dictionary
settings = {}


def load_settings():
    global settings
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                print("Settings loaded successfully.")
        else:
            save_settings()  # Create an empty settings file if it doesn't exist
    except json.JSONDecodeError:
        settings = {}  # Initialize with empty dictionary if file is empty or invalid
    except Exception as e:
        print(f"Error loading settings: {e}")


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

    try:
        guild = await client.fetch_guild(payload.guild_id)
        if guild is None:
            return

        member = await guild.fetch_member(payload.user_id)
        if member is None:
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        await member.add_roles(role)
    except discord.Forbidden:
        print("Bot doesn't have permissions to add roles.")
    except discord.HTTPException:
        print("Failed to add role due to Discord API issue.")
    except Exception as e:
        print(f"Error adding role: {e}")


# ban command
@client.tree.command(name="ban", description="Bans a user from the server.")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def ban_user(
    interaction: discord.Interaction, user: discord.User, reason: str = None
):
    try:
        await interaction.guild.ban(user, reason=reason)
        await interaction.response.send_message(
            f"{user.name} has been banned.", ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to ban users.", ephemeral=True
        )
    except discord.HTTPException:
        await interaction.response.send_message(
            "Failed to ban the user. Please try again later.", ephemeral=True
        )


# kick command
@client.tree.command(name="kick", description="Kicks a user from the server.")
@app_commands.checks.has_permissions(kick_members=True)
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def kick_user(
    interaction: discord.Interaction, user: discord.User, reason: str = None
):
    try:
        await interaction.guild.kick(user, reason=reason)
        await interaction.response.send_message(
            f"{user.name} has been kicked.", ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to kick users.", ephemeral=True
        )
    except discord.HTTPException:
        await interaction.response.send_message(
            "Failed to kick the user. Please try again later.", ephemeral=True
        )


# mute command


@client.tree.command(name="mute", description="Mutes a user for a specified duration.")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def mute_user(
    interaction: discord.Interaction,
    user: discord.Member,
    duration: str,
    reason: str = None,
):
    # Implement mute logic here
    await interaction.response.send_message(
        "Mute command is not implemented yet.", ephemeral=True
    )


# unmute


@client.tree.command(name="unmute", description="Unmutes a user.")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def unmute_user(interaction: discord.Interaction, user: discord.Member):
    # Implement unmute logic here
    await interaction.response.send_message(
        "Unmute command is not implemented yet.", ephemeral=True
    )


# warn


@client.tree.command(name="warn", description="Issues a warning to a user.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def warn_user(
    interaction: discord.Interaction, user: discord.Member, reason: str
):
    # Implement warn logic here
    await interaction.response.send_message(
        "Warn command is not implemented yet.", ephemeral=True
    )


# clear


@client.tree.command(
    name="clear", description="Deletes a specified number of messages from a channel."
)
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def clear_messages(interaction: discord.Interaction, number: int):
    # Implement clear messages logic here
    await interaction.response.send_message(
        "Clear command is not implemented yet.", ephemeral=True
    )


# lock channel
@client.tree.command(
    name="lock", description="Locks a channel, preventing users from sending messages."
)
@app_commands.checks.has_permissions(manage_channels=True)
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def lock_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    # Implement lock channel logic here
    await interaction.response.send_message(
        "Lock command is not implemented yet.", ephemeral=True
    )


# unlock channel


@client.tree.command(name="unlock", description="Unlocks a channel.")
@app_commands.checks.has_permissions(manage_channels=True)
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def unlock_channel(
    interaction: discord.Interaction, channel: discord.TextChannel
):
    # Implement unlock channel logic here
    await interaction.response.send_message(
        "Unlock command is not implemented yet.", ephemeral=True
    )


# Run the bot with the token
client.run(TOKEN)
