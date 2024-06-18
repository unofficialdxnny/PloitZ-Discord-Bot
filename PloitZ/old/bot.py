import discord
from discord import FFmpegPCMAudio
from discord.ext import commands
from discord import app_commands
import asyncio
from dotenv import load_dotenv
import os
from gtts import gTTS
import nacl
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
from supabase import create_client, Client


# Load environment variables from .env file
load_dotenv()

# Retrieve bot token and other sensitive information from environment variables
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))
UNVERIFIED_ROLE_ID = int(os.getenv("UNVERIFIED_ROLE_ID"))
VERIFIED_ROLE_ID = int(os.getenv("VERIFIED_ROLE_ID"))
VERIFICATION_CHANNEL_ID = int(os.getenv("VERIFICATION_CHANNEL_ID"))
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# Define intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True  # Enable reaction intents
intents.messages = True  # Enable message intents

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "outtmpl": "downloads/%(title)s.%(ext)s",
    "quiet": True,
}

# Create the bot with necessary intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Spotify credentials
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# Spotify client authorization
sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET
    )
)

# Store the verification message ID globally
verification_message_id = None
support_ticket_message_id = None

# Level data storage
# Level data storage
level_data = {}

# Define the levels at which members will be notified
LEVEL_NOTIFICATIONS = [5, 10, 15]  # Example: notify at levels 5, 10, 15


@bot.event
async def on_ready():
    print(f"Bot {bot.user} is ready!")
    bot.loop.create_task(save_levels_task())  # Schedule the task

    try:
        guild = discord.Object(id=GUILD_ID)
        s = await bot.tree.sync(guild=guild)
        print(f"Synced {len(s)} commands to guild {GUILD_ID}!")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    print(f"Logged in as {bot.user.name}")
    global level_data
    servers = len(bot.guilds)
    members = sum(guild.member_count - 1 for guild in bot.guilds)
    activity = discord.Activity(
        type=discord.ActivityType.watching, name=f"{members} Members"
    )
    await bot.change_presence(activity=activity)

    global verification_message_id, support_ticket_message_id

    # Send the verification message if it doesn't already exist
    verification_channel = bot.get_channel(VERIFICATION_CHANNEL_ID)
    if verification_channel:
        print(
            f"Verification channel found: {verification_channel.name} ({verification_channel.id})"
        )
        async for message in verification_channel.history(limit=100):
            if (
                message.author == bot.user
                and message.embeds
                and "Please react to this message with ✅ to verify"
                in message.embeds[0].description
            ):
                verification_message_id = message.id
                print(f"Found existing verification message: {verification_message_id}")
                break
        else:
            # Create embed message for verification
            embed = discord.Embed(
                title="Server Verification",
                description="Please react to this message with ✅ to verify and gain access to the rest of the server.",
                color=discord.Color.blue(),
            )
            try:
                verification_message = await verification_channel.send(embed=embed)
                await verification_message.add_reaction("✅")
                verification_message_id = verification_message.id
                print(f"Created new verification message: {verification_message_id}")
            except discord.DiscordException as e:
                print(f"Failed to send verification message: {e}")
    else:
        print(f"Verification channel with ID {VERIFICATION_CHANNEL_ID} not found.")

    # Ensure the support ticket message is present
    ticket_channel = bot.get_channel(1250193098504409158)
    if ticket_channel:
        async for message in ticket_channel.history(limit=100):
            if (
                message.author == bot.user
                and message.embeds
                and message.embeds[0].title == "PloitZ Support Ticket"
            ):
                support_ticket_message_id = message.id
                print(
                    f"Existing support ticket message found: {support_ticket_message_id}"
                )
                break
        else:
            embed = discord.Embed(
                title="PloitZ Support Ticket",
                description="To create a ticket react with 📩",
                color=discord.Color.blue(),
            )
            try:
                ticket_message = await ticket_channel.send(embed=embed)
                await ticket_message.add_reaction("📩")
                support_ticket_message_id = ticket_message.id
                print(
                    f"Created new support ticket message: {support_ticket_message_id}"
                )
            except discord.DiscordException as e:
                print(f"Failed to send support ticket message: {e}")
    else:
        print(f"Ticket channel with ID 1250193098504409158 not found.")

    # Start the task to periodically save levels
    bot.loop.create_task(save_levels_task())


@bot.event
async def on_member_join(member):
    print(f"Member joined: {member.name}")
    # Assign unverified role to the new member
    unverified_role = member.guild.get_role(UNVERIFIED_ROLE_ID)
    await member.add_roles(unverified_role)


@bot.event
async def on_message(message):
    if not message.author.bot:  # Ignore messages from bots
        # Update level data for the user
        user_id = message.author.id
        if user_id not in level_data:
            level_data[user_id] = {"messages": 0, "level": 0}

        # Increment message count
        level_data[user_id]["messages"] += 1

        # Check if user leveled up
        messages = level_data[user_id]["messages"]
        level = messages // 10  # Example: 1 level per 10 messages

        if level > level_data[user_id]["level"]:
            # Level up occurred
            level_data[user_id]["level"] = level
            await message.channel.send(
                f"Congratulations {message.author.mention}, you leveled up to level {level}!"
            )

            # Check if this level has a special notification
            if level in LEVEL_NOTIFICATIONS:
                await message.channel.send(
                    f"Level {level} special notification for {message.author.mention}!"
                )

    await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(payload):
    print(
        f"Reaction added: user_id={payload.user_id}, message_id={payload.message_id}, emoji={payload.emoji}"
    )

    if payload.message_id == verification_message_id:
        print("Verification message reaction detected")
        if str(payload.emoji) == "✅":
            guild = bot.get_guild(payload.guild_id)
            if guild:
                member = guild.get_member(payload.user_id)
                if member:
                    # Add the verified role and remove the unverified role
                    verified_role = guild.get_role(VERIFIED_ROLE_ID)
                    unverified_role = guild.get_role(UNVERIFIED_ROLE_ID)
                    if verified_role and unverified_role:
                        try:
                            await member.add_roles(verified_role)
                            await member.remove_roles(unverified_role)
                            print(f"Verified {member.name} (ID: {member.id})")
                        except discord.DiscordException as e:
                            print(
                                f"Failed to update roles for {member.name} (ID: {member.id}): {e}"
                            )
                    else:
                        print(
                            f"Roles not found: verified_role={verified_role}, unverified_role={unverified_role}"
                        )
                else:
                    print(f"Member not found: user_id={payload.user_id}")
            else:
                print(f"Guild not found: guild_id={payload.guild_id}")
        else:
            print(f"Emoji does not match: emoji={payload.emoji}")
    elif payload.message_id == support_ticket_message_id:
        print("Support ticket message reaction detected")
        if str(payload.emoji) == "📩":
            guild = bot.get_guild(payload.guild_id)
            if guild:
                member = guild.get_member(payload.user_id)
                if member:
                    # Create a new ticket channel
                    ticket_category = discord.utils.get(
                        guild.categories, id=TICKET_CATEGORY_ID
                    )
                    if ticket_category:
                        existing_channel = discord.utils.get(
                            guild.text_channels, name=f"ticket-{member.id}"
                        )
                        if not existing_channel:
                            ticket_channel = await guild.create_text_channel(
                                f"ticket-{member.name}", category=ticket_category
                            )
                            await ticket_channel.set_permissions(
                                guild.default_role,
                                send_messages=False,
                                read_messages=False,
                            )
                            await ticket_channel.set_permissions(
                                member,
                                send_messages=True,
                                read_messages=True,
                                add_reactions=True,
                                embed_links=True,
                                attach_files=True,
                                read_message_history=True,
                                external_emojis=True,
                            )
                            await ticket_channel.send(
                                embed=discord.Embed(
                                    title="PloitZ Support Ticket",
                                    description="Please describe your issue.",
                                    color=discord.Color.blue(),
                                )
                            )
                            print(
                                f"Created ticket channel for {member.name} (ID: {member.id})"
                            )
                        else:
                            print(
                                f"Ticket channel already exists for {member.name} (ID: {member.id})"
                            )
                    else:
                        print(
                            f"Ticket category with ID {TICKET_CATEGORY_ID} not found."
                        )
                else:
                    print(f"Member not found: user_id={payload.user_id}")
            else:
                print(f"Guild not found: guild_id={payload.guild_id}")
        else:
            print(f"Emoji does not match: emoji={payload.emoji}")
    else:
        print(f"Message ID does not match: message_id={payload.message_id}")


# Define a slash command to open a support ticket
@bot.tree.command(
    name="ticket",
    description="Open a support ticket",
    guild=discord.Object(id=GUILD_ID),
)
async def ticket(interaction: discord.Interaction):
    guild = interaction.guild
    author = interaction.user

    # Check if the user already has a ticket open
    existing_channel = discord.utils.get(
        guild.text_channels, name=f"ticket-{author.id}"
    )
    if existing_channel:
        await interaction.response.send_message(
            f"You already have an open ticket: {existing_channel.mention}",
            ephemeral=True,
        )
    else:
        # Get the ticket category
        ticket_category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
        if ticket_category:
            # Create a new ticket channel under the specified category
            ticket_channel = await guild.create_text_channel(
                f"ticket-{author.name}", category=ticket_category
            )
            await ticket_channel.set_permissions(
                guild.default_role, send_messages=False, read_messages=False
            )
            await ticket_channel.set_permissions(
                author,
                send_messages=True,
                read_messages=True,
                add_reactions=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True,
                external_emojis=True,
            )

            # Send a message in the ticket channel
            embed = discord.Embed(
                title="PloitZ Support Ticket",
                description="Please describe your issue.",
                color=discord.Color.blue(),
            )
            await ticket_channel.send(
                f"{author.mention}, your ticket has been created.", embed=embed
            )
            await interaction.response.send_message(
                f"Your ticket has been created: {ticket_channel.mention}",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Ticket category not found. Please contact an administrator.",
                ephemeral=True,
            )


# Define a slash command to close the ticket
@bot.tree.command(
    name="close",
    description="Close the support ticket",
    guild=discord.Object(id=GUILD_ID),
)
async def close(interaction: discord.Interaction):
    channel = interaction.channel
    author = interaction.user

    print(
        f"Attempting to close channel '{channel.name}' in category '{channel.category_id}'"
    )

    # Ensure the channel belongs to the specified category
    if channel.category_id == 1250194498789576834:
        # Check if the author has permission to manage channels
        if author.guild_permissions.manage_channels:
            try:
                await channel.delete()
                print(f"Closed channel '{channel.name}' successfully")
                await interaction.response.send_message(
                    "The ticket has been closed.", ephemeral=True
                )
            except discord.Forbidden:
                print(f"I don't have permission to delete channel '{channel.name}'")
                await interaction.response.send_message(
                    "I don't have permission to close this ticket.", ephemeral=True
                )
            except discord.HTTPException as e:
                print(f"Failed to delete channel '{channel.name}': {e}")
                await interaction.response.send_message(
                    "Failed to close the ticket. Please try again later.",
                    ephemeral=True,
                )
        else:
            print(f"User '{author.name}' does not have manage_channels permission")
            await interaction.response.send_message(
                "You do not have permission to close this ticket.", ephemeral=True
            )
    else:
        print(f"Channel '{channel.name}' does not belong to the specified category")
        await interaction.response.send_message(
            "You can only close tickets in the specified category.", ephemeral=True
        )


@bot.tree.command(
    name="rename",
    description="Rename a support ticket",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(
    from_name="Current ticket channel name",
    to_name="New ticket channel name",
)
async def rename(interaction: discord.Interaction, from_name: str, to_name: str):
    author = interaction.user
    # Check if the author has permission to rename ticket channels

    if author.guild_permissions.administrator:
        # Find the existing ticket channel
        existing_channel = discord.utils.get(
            interaction.guild.text_channels, name=from_name
        )
        if existing_channel:
            try:
                await existing_channel.edit(name=to_name)
                await interaction.response.send_message(
                    f"Ticket channel '{from_name}' renamed to '{to_name}'.",
                    ephemeral=True,
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I don't have permission to rename channels.", ephemeral=True
                )
            except discord.HTTPException:
                await interaction.response.send_message(
                    "Failed to rename the channel. Please try again later.",
                    ephemeral=True,
                )
        else:
            await interaction.response.send_message(
                f"Ticket channel '{from_name}' not found.", ephemeral=True
            )
    else:
        await interaction.response.send_message(
            "You do not have permission to rename ticket channels.", ephemeral=True
        )


# Define a slash command to kick a member
@bot.tree.command(
    name="kick",
    description="Kick a member from the server",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(member="Member to kick")
async def kick(interaction: discord.Interaction, member: discord.Member):
    author = interaction.user

    # Check if the author has permission to kick members
    if author.guild_permissions.kick_members:
        try:
            await member.kick(reason="Requested by moderator")
            await interaction.response.send_message(
                f"{member.display_name} has been kicked from the server.",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"I don't have permission to kick {member.display_name}.",
                ephemeral=True,
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                f"Failed to kick {member.display_name}. Please try again later.",
                ephemeral=True,
            )
    else:
        await interaction.response.send_message(
            "You do not have permission to kick members.", ephemeral=True
        )


# Define a slash command to ban a member
@bot.tree.command(
    name="ban",
    description="Ban a member from the server",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(member="Member to ban")
async def ban(interaction: discord.Interaction, member: discord.Member):
    author = interaction.user

    # Check if the author has permission to ban members
    if author.guild_permissions.ban_members:
        try:
            await member.ban(reason="Requested by moderator", delete_message_days=7)
            await interaction.response.send_message(
                f"{member.display_name} has been banned from the server.",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"I don't have permission to ban {member.display_name}.", ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                f"Failed to ban {member.display_name}. Please try again later.",
                ephemeral=True,
            )
    else:
        await interaction.response.send_message(
            "You do not have permission to ban members.", ephemeral=True
        )


# Define a slash command to unban a member
@bot.tree.command(
    name="unban",
    description="Unban a member from the server",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(user_id="ID of the user to unban")
async def unban(interaction: discord.Interaction, user_id: str):
    author = interaction.user

    # Check if the author has permission to unban members
    if not author.guild_permissions.ban_members:
        await interaction.response.send_message(
            "You do not have permission to unban members.", ephemeral=True
        )
        return

    guild = interaction.guild

    try:
        user_id = int(user_id)
    except ValueError:
        await interaction.response.send_message(
            "Invalid user ID. Please provide a valid user ID.", ephemeral=True
        )
        return

    banned_users = await guild.bans()
    user = discord.utils.find(lambda u: u.user.id == user_id, banned_users)

    if user is None:
        await interaction.response.send_message(
            "User not found in the ban list.", ephemeral=True
        )
    else:
        try:
            await guild.unban(user.user)
            await interaction.response.send_message(
                f"{user.user.name} has been unbanned from the server.", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"I don't have permission to unban {user.user.name}.", ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                f"Failed to unban {user.user.name}. Please try again later.",
                ephemeral=True,
            )


@bot.command(name="say")
async def say(ctx, *, phrase: str):
    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel
        vc = await voice_channel.connect()
        tts = gTTS(text=phrase, lang="en")
        tts.save("phrase.mp3")
        vc.play(discord.FFmpegPCMAudio("phrase.mp3"), after=lambda e: print("done", e))
        while vc.is_playing():
            await asyncio.sleep(1)
        await vc.disconnect()
    else:
        await ctx.send("You are not in a voice channel!")


@bot.tree.command(name="say")
@app_commands.describe(phrase="The phrase you want the bot to say.")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def slash_say(interaction: discord.Interaction, phrase: str):
    """Make the bot say something in a voice channel."""
    if interaction.user.voice:
        await interaction.response.defer()  # Acknowledge the interaction immediately
        voice_channel = interaction.user.voice.channel
        vc = await voice_channel.connect()
        tts = gTTS(text=phrase, lang="en")
        tts.save("phrase.mp3")
        vc.play(discord.FFmpegPCMAudio("phrase.mp3"), after=lambda e: print("done", e))
        while vc.is_playing():
            await asyncio.sleep(1)
        await vc.disconnect()
        await interaction.followup.send(
            f"Saying: {phrase}"
        )  # Use followup to send the message after defer
    else:
        await interaction.response.send_message("You are not in a voice channel!")


# Define the clear command
@bot.tree.command(
    name="clear",
    description="Clear a specified number of messages from the channel.",
    guild=discord.Object(id=GUILD_ID),
)
async def clear(interaction: discord.Interaction, number_of_messages: int):
    # Acknowledge the interaction immediately
    await interaction.response.defer(ephemeral=True)

    # Check if the user has manage messages permission
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.followup.send(
            "You do not have permission to use this command.", ephemeral=True
        )
        return

    # Check if the number_of_messages is a valid number
    if number_of_messages <= 0:
        await interaction.followup.send(
            "Please specify a positive number of messages to delete.", ephemeral=True
        )
        return

    # Get the channel from the interaction
    channel = interaction.channel

    # Delete messages
    try:
        deleted = await channel.purge(limit=number_of_messages)
        await interaction.followup.send(
            f"Deleted {len(deleted)} messages.", ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"Failed to delete messages: {e}", ephemeral=True
        )


# Define a slash command to display help
# @bot.tree.command(
#     name="help", description="List all available commands", guild=[GUILD_ID]
# )
# async def help(interaction: discord.Interaction):
#     embed = discord.Embed(title="Help", description="List of available commands:")
#     embed.add_field(name="/ticket", value="Create a new support ticket", inline=False)
#     embed.add_field(
#         name="/close", value="Close the current support ticket", inline=False
#     )
#     embed.add_field(
#         name="/rename", value="Rename the current support ticket channel", inline=False
#     )
#     embed.add_field(name="/kick", value="Kick a member from the server", inline=False)
#     embed.add_field(name="/ban", value="Ban a member from the server", inline=False)
#     embed.add_field(name="/unban", value="Unban a member from the server", inline=False)
#     embed.add_field(
#         name="/say",
#         value="Make the bot join a voice channel and say a phrase",
#         inline=False,
#     )
#     embed.add_field(
#         name="/clear", value="Clear a specified number of messages", inline=False
#     )
#     embed.add_field(name="/help", value="List all available commands", inline=False)
#     await interaction.response.send_message(embed=embed, ephemeral=True)


# # Example: Task to periodically save levels to a file or database
# async def save_levels_task():
#     while True:
#         save_levels_to_file(level_data)
#         await asyncio.sleep(10)  # Save every 10 seconds


# # Example: Function to save levels to a file (implement as per your storage needs)
# def save_levels_to_file(level_data):
#     with open("levels.txt", "w") as file:
#         for member_id, data in level_data.items():
#             file.write(f"{member_id}:{data['messages']}:{data['level']}\n")


# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class LevelingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.level_data = level_data

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user = message.author
        if user.id not in self.level_data:
            self.level_data[user.id] = {"xp": 0, "level": 1}

        self.level_data[user.id]["xp"] += 10

        if self.has_leveled_up(user):
            self.level_data[user.id]["level"] += 1
            await self.send_level_up_message(user)

    def has_leveled_up(self, user):
        xp = self.level_data[user.id]["xp"]
        required_xp = self.calculate_required_xp(self.level_data[user.id]["level"])
        return xp >= required_xp

    async def send_level_up_message(self, user):
        level = self.level_data[user.id]["level"]
        await user.send(
            f"Congratulations, {user.mention}! You've leveled up to level {level}."
        )

    def calculate_required_xp(self, level):
        # Example XP formula: XP required doubles every level
        return 100 * (2 ** (level - 1))


async def save_levels_task():
    while True:
        save_levels_to_supabase(level_data)
        await asyncio.sleep(600)  # Save every 10 minutes


def save_levels_to_supabase(level_data):
    for member_id, data in level_data.items():
        try:
            response = Client.table("profiles").insert(
                {
                    "user_id": member_id,
                    "xp": data.get("xp", 0),
                    "level": data.get("level", 0),
                }
            )
            if response.error:
                print(f"Error upserting data: {response.error}")
            else:
                print(f"Upsert successful: {response.data}")
        except Exception as e:
            print(f"Exception occurred: {e}")


# Register the LevelingSystem cog
bot.add_cog(LevelingSystem(bot))


# Run the bot with the token
bot.run(TOKEN)
