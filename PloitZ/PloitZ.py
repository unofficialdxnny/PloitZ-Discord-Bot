import random
import os
import json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime, timedelta
import asyncio
import aiohttp
import random
from gtts import gTTS
import time
import itertools
from discord.ui import View, Button
import sys
import subprocess


# os.system("cls")
# load_dotenv(dotenv_path="./data/config/.env")
# # Replace environment variables with direct values
# TOKEN = os.getenv("TOKEN")
# SERVER_ID = os.getenv("SERVER_ID")
# WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
# RULES_CHANNEL_ID = int(os.getenv("RULES_CHANNEL_ID"))
# VERIFICATION_CHANNEL_ID = int(os.getenv("VERIFICATION_CHANNEL_ID"))
# MEMBERS_ROLE_ID = int(os.getenv("MEMBERS_ROLE_ID"))
# UNVERIFIED_ROLE_ID = int(os.getenv("UNVERIFIED_ROLE_ID"))
# TICKETS_CATEGORY = int(os.getenv("TICKETS_CATEGORY"))
# MUTED_ROLE_ID = int(os.getenv("MUTED_ROLE_ID"))
# GENERAL_CHANNEL_ID = int(os.getenv("GENERAL_CHANNEL_ID"))
# MEMBER_CHANNEL_ID = int(os.getenv("MEMBER_CHANNEL_ID"))
# BOT_CHANNEL_ID = int(os.getenv("BOT_CHANNEL_ID"))

load_dotenv(dotenv_path="./data/config/.env")

TOKEN = f"{os.getenv("TOKEN")}"  

SERVER_ID = 1250141995243143270
WELCOME_CHANNEL_ID = 1250141995872026693
RULES_CHANNEL_ID = 1250141995872026691
VERIFICATION_CHANNEL_ID = 1250522865372238026
MEMBERS_ROLE_ID = 1250145163888824371
UNVERIFIED_ROLE_ID = 1250530085073846334
TICKETS_CATEGORY = 1250194498789576834
MUTED_ROLE_ID = 1252701676712890369
GENERAL_CHANNEL_ID = 1250141995872026689
MEMBER_CHANNEL_ID = 1250535823049228328
BOT_CHANNEL_ID = 1250535955396432005
LINKS_ROLE_ID = 1256386441068417104
REACTION_EMOJI = "✅"


# Initialize bot
intents = discord.Intents.default()
intents.reactions = True  # Enable reaction intents
intents.guilds = True  # Enable guild intents
intents.messages = True  # Enable message intents
intents.message_content = True
intents.members = True  # Enable member intents
intents.presences = True  # Enable presence intents
intents.guild_messages = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

    try:
        # Sync global commands
        synced_global = await bot.tree.sync()
        print(f"Successfully synced {len(synced_global)} global command(s)")

        """
        Creates a verification message in the designated verification channel.

        If a verification message already exists in the channel, it will be reused.
        Otherwise, a new message will be created with a verification embed and a reaction.

        Args:
            VERIFICATION_CHANNEL_ID (int): The ID of the verification channel.
            REACTION_EMOJI (str): The emoji to use for the verification reaction.

        Returns:
            None

        Raises:
            discord.HTTPException: If there is an error sending the verification message.
        """

        verification_channel = bot.get_channel(VERIFICATION_CHANNEL_ID)
        if not verification_channel:
            print(f"Verification channel with ID {VERIFICATION_CHANNEL_ID} not found.")
            return

        # Check if there is an existing verification message
        verification_message = None
        async for message in verification_channel.history():
            if message.author == bot.user and any(
                reaction.emoji == REACTION_EMOJI for reaction in message.reactions
            ):
                verification_message = message
                break

        if verification_message is None:
            # Create an embed for the verification message
            embed = discord.Embed(
                title="Verification",
                description="React with ✅ to verify yourself and gain access to the server.",
                color=discord.Color.from_rgb(254, 254, 254),
            )

            # Send the verification embed message
            try:
                verification_message = await verification_channel.send(embed=embed)
                await verification_message.add_reaction(REACTION_EMOJI)
                print(f"Created verification message in #{verification_channel.name}")
            except discord.HTTPException as e:
                print(f"Failed to create verification message: {e}")

                # verification system end

        # Update bot presence with dynamic member count
        member_count = sum(guild.member_count for guild in bot.guilds)
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name=f"/help | {member_count} Members"
            )
        )

    except Exception as e:
        print(f"Error syncing global commands: {e}")

    try:
        # Sync guild-specific commands
        test_guild = discord.Object(id=SERVER_ID)
        synced_guild = await bot.tree.sync(guild=test_guild)
        print(f"Successfully synced {len(synced_guild)} guild command(s) in {SERVER_ID}")
    except Exception as e:
        print(f"Error syncing guild commands: {e}")



@bot.event
async def on_raw_reaction_add(payload):
    """
    Event handler for when a reaction is added to a message.
    
    Grants the members role to a user who reacts with the expected emoji in the verification channel.
    
    Args:
        payload (discord.RawReactionActionEvent): The reaction event payload.
    
    Returns:
        None
    
    Raises:
        discord.Forbidden: If the bot does not have permission to add roles to the user.
        discord.HTTPException: If there is an error adding the role to the user.
    """
    # Check if the reaction is added to a message in the verification channel
    if payload.channel_id != VERIFICATION_CHANNEL_ID:
        return

    # Check if the reaction is the expected emoji and from a non-bot user
    if str(payload.emoji) == REACTION_EMOJI and not payload.member.bot:
        guild = bot.get_guild(payload.guild_id)
        if guild:
            member = guild.get_member(payload.user_id)
            if member:
                # Grant the members role to the reacting user
                members_role = guild.get_role(MEMBERS_ROLE_ID)
                if members_role:
                    try:
                        await member.add_roles(members_role)
                        print(
                            f"Granted {members_role.name} role to {member.display_name}."
                        )
                    except discord.Forbidden:
                        print(
                            f"Bot does not have permission to add roles to {member.display_name}."
                        )
                    except discord.HTTPException as e:
                        print(f"Failed to add role to {member.display_name}: {e}")


@bot.event
async def on_member_join(member):
    # Fetch the welcome channel
    welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)

    if welcome_channel:
        # Fetch member's avatar URL
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url

        # Create an embed for the welcome message
        embed = discord.Embed(
            title=f"Welcome to {member.guild.name}, @{member.name}!",
            description=f"We are glad you joined us. Please read the rules in <#{RULES_CHANNEL_ID}> and enjoy your stay!",
            color=discord.Color.from_rgb(254, 254, 254),
        )
        embed.set_thumbnail(url=avatar_url)  # Set member's avatar as thumbnail
        embed.set_footer(
            text=f"Joined {member.guild.name} | {member.guild.member_count} members"
        )

        # Send the welcome message to the welcome channel
        try:
            await welcome_channel.send(embed=embed)
        except discord.HTTPException as e:
            print(f"Failed to send welcome message: {e}")
    else:
        print(f"Welcome channel with ID {WELCOME_CHANNEL_ID} not found.")


@bot.event
async def on_member_remove(member):
    # Fetch the welcome channel
    welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)

    if welcome_channel:
        # Fetch member's avatar URL
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url

        # Create an embed for the leave message
        embed = discord.Embed(
            title=f"Goodbye, {member.name}!",
            description=f"{member.name} has left the server. We wont miss you!",
            color=discord.Color.red(),  # Change color to red to indicate departure
        )
        embed.set_thumbnail(url=avatar_url)  # Set member's avatar as thumbnail
        embed.set_footer(
            text=f"Left {member.guild.name} | {member.guild.member_count} members"
        )

        # Send the leave message to the welcome channel
        try:
            await welcome_channel.send(embed=embed)
        except discord.HTTPException as e:
            print(f"Failed to send leave message: {e}")
    else:
        print(f"Welcome channel with ID {WELCOME_CHANNEL_ID} not found.")


def admin_only():
    async def predicate(interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You do not have permission to use this command."
            )
            return False
        return True

    return app_commands.check(predicate)


# Assuming the bot is already initialized elsewhere
# bot = commands.Bot(command_prefix="!")

# Commands data embedded directly in the Python file
COMMANDS_DATA = {
    "General": [
        {"name": "help", "description": "Show all available commands."},
        {"name": "avatar", "description": "Get the avatar of a user."},
        {"name": "snapify", "description": "Get information about Snapify app."},
        {"name": "ticket", "description": "Create A ticket in the server!"}
    ],
    "Moderation": [
        {"name": "mute", "description": "Mute a user indefinitely."},
        {"name": "unmute", "description": "Unmute a user."},
        {"name": "muted", "description": "List all currently muted users."},
        {"name": "warn", "description": "Warn a user with a reason."},
        {"name": "clear", "description": "Clear a specified number of messages."},
        {"name": "lock", "description": "Lock a channel."},
        {"name": "unlock", "description": "Unlock a channel."},
        {"name": "purge", "description": "Delete a specified number of messages from a user."},
        {"name": "addrole", "description": "Add a role to a user."},
        {"name": "removerole", "description": "Remove a role from a user."}
    ],
    "Admin": [
        {"name": "Restart", "description": "Restarts the bot"},
        {"name": "ban", "description": "Bans a user from the server."},
        {"name": "kick", "description": "Kicks a user from the server."},
        {"name": "roleinfo", "description": "Get information about a role."},
        {"name": "snapify_update", "description": "Update Snapify information."},
        {"name": "nick", "description": "Change a user's nickname."},
        {"name": "removerole", "description": "Remove a role from a user."},
        {"name": "slowmode", "description": "Set slowmode in a channel."},
        {"name": "reaction_role", "description": "Get a role by clicking a button"},
        {"name": "create_role", "description": "Creates a role easily"},
        {"name": "delete_role", "description": "Deletes a role easily"},
    ]
}

@bot.tree.command(name="help", description="Show all available commands.")
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def help_command(interaction: discord.Interaction):
    commands_data = COMMANDS_DATA

    # Check if the user has admin privileges
    is_admin = interaction.user.guild_permissions.administrator

    embed = discord.Embed(
        title="PloitZ Bot Commands",
        description="Here are the available commands categorized:",
        color=discord.Color.from_rgb(254, 254, 254),
    )

    for category, commands_list in commands_data.items():
        if commands_list:
            # If the user is not an admin, filter out the 'Moderation' category
            if not is_admin and category in ["Moderation", "Events", "Admin"]:
                continue

            command_list_str = "\n".join(
                f"`/{command['name']}` - {command['description']}"
                for command in commands_list
            )
            embed.add_field(name=category, value=command_list_str, inline=False)

    try:
        # Simulate typing effect
        async with interaction.channel.typing():
            # Check if the embed is too large
            if len(embed.to_dict().get('description', '')) > 2000:
                # Send in chunks if description is too long
                embed.description = embed.description[:2000]
                await interaction.response.send_message(embed=embed)
                # Adjust if necessary based on your needs
            else:
                await interaction.response.send_message(embed=embed)
                
    except discord.HTTPException as e:
        print(f"Failed to send help embed: {e}")
        await interaction.response.send_message("An error occurred while sending the help message.")

'''
SHUTDOWN tickets service as it is old (Discord Forums is a neater way and more organised)
'''

# @bot.tree.command(name="ticket", description="Create a support ticket.")
# @app_commands.guilds(discord.Object(id=SERVER_ID))
# async def ticket(interaction: discord.Interaction, problem: str):
#     guild = interaction.guild
#     user = interaction.user

#     # Ensure TICKETS_CATEGORY is an integer
#     category_id = int(TICKETS_CATEGORY)

#     # Fetch the category object
#     category = discord.utils.get(guild.categories, id=category_id)

#     if category is None:
#         await interaction.response.send_message(
#             "Category not found. Please configure the bot correctly."
#         )
#         return

#     # Check for existing ticket by checking if the channel name starts with the user's name
#     existing_ticket = None
#     for channel in category.text_channels:
#         if channel.name.startswith(f"{user.name.lower()}-"):
#             existing_ticket = channel
#             break

#     if existing_ticket:
#         await interaction.response.send_message(
#             f"You already have an open ticket: {existing_ticket.mention}",
#             ephemeral=True,
#         )
#         return

#     # Create a channel name based on the user's name and problem
#     channel_name = f"{user.name.lower()}-{problem.lower().replace(' ', '-')}"
#     overwrites = {
#         guild.default_role: discord.PermissionOverwrite(read_messages=False),
#         guild.me: discord.PermissionOverwrite(read_messages=True),
#         user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
#     }

#     try:
#         # Create the support ticket channel under the specified category
#         ticket_channel = await guild.create_text_channel(
#             channel_name, category=category, overwrites=overwrites
#         )
#     except discord.Forbidden:
#         await interaction.response.send_message(
#             "I don't have permission to create channels."
#         )
#         return
#     except discord.HTTPException:
#         await interaction.response.send_message(
#             "Failed to create support ticket channel. Please try again later.",
#             ephemeral=True,
#         )
#         return

#     # Create an embed with the user's problem
#     embed = discord.Embed(
#         title="Support Ticket",
#         description=f"**User:** {user.mention}\n**Problem:** {problem}",
#         color=discord.Color.from_rgb(254, 254, 254),
#     )

#     # Send the embed to the support ticket channel
#     try:
#         await ticket_channel.send(embed=embed)
#         await interaction.response.send_message(
#             f"Support ticket created in {ticket_channel.mention}."
#         )
#     except discord.HTTPException:
#         await interaction.response.send_message(
#             "Failed to send embed message to support ticket channel."
#         )


# @bot.tree.command(name="close", description="Close a support ticket.")
# @app_commands.guilds(discord.Object(id=SERVER_ID))
# async def close(interaction: discord.Interaction):
#     guild = interaction.guild
#     author = interaction.user

#     # Check if the command is used in a ticket channel
#     if interaction.channel.category_id != TICKETS_CATEGORY:
#         await interaction.response.send_message(
#             "/close may only be used in a ticket channel."
#         )
#         return

#     # Check if the author is an admin
#     if not author.guild_permissions.administrator:
#         await interaction.response.send_message(
#             "You must be an admin to use this command."
#         )
#         return

#     # Fetch the category object for tickets
#     category = discord.utils.get(guild.categories, id=TICKETS_CATEGORY)

#     if category is None:
#         await interaction.response.send_message(
#             "Tickets category not found. Please configure the bot correctly."
#         )
#         return

#     # Get list of ticket channels under the category
#     ticket_channels = [
#         channel
#         for channel in category.channels
#         if isinstance(channel, discord.TextChannel)
#     ]

#     if not ticket_channels:
#         await interaction.response.send_message(
#             "No ticket channels found in the tickets category."
#         )
#         return

#     # Attempt to delete the current channel
#     try:
#         await interaction.channel.delete()
#         await interaction.response.send_message(
#             f"Successfully closed {interaction.channel.name}."
#         )
#     except discord.Forbidden:
#         await interaction.response.send_message(
#             "I do not have permission to delete this channel."
#         )
#     except discord.HTTPException:
#         await interaction.response.send_message(
#             "Failed to delete the channel. Please try again later."
#         )


# Slash command to get user avatar
@bot.tree.command(name="avatar", description="Get the avatar of a user.")
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def avatar(interaction: discord.Interaction, user: discord.Member = None):
    # Use the interaction user if no user is mentioned
    user = user or interaction.user
    
    # Fetch avatar URL
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

    # Create an embed with the avatar image
    embed = discord.Embed(
        title=f"Avatar of {user.name}",
        color=discord.Color.from_rgb(254, 254, 254),
    )
    embed.set_image(url=avatar_url)

    # Send the embed as a response to the interaction
    await interaction.response.send_message(embed=embed)


# ban command
@bot.tree.command(name="ban", description="Bans a user from the server.")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def ban_user(
    interaction: discord.Interaction, user: discord.User, reason: str = None
):
    try:
        await interaction.guild.ban(user, reason=reason)
        await interaction.response.send_message(
            f"{interaction.user.mention} has banned {user.mention} for {reason or 'No reason provided'}."
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to ban users."
        )
    except discord.HTTPException:
        await interaction.response.send_message(
            "Failed to ban the user. Please try again later."
        )


# kick command
@bot.tree.command(name="kick", description="Kicks a user from the server.")
@app_commands.checks.has_permissions(kick_members=True)
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def kick_user(
    interaction: discord.Interaction, user: discord.User, reason: str = None
):
    try:
        await interaction.guild.kick(user, reason=reason)
        await interaction.response.send_message(
            f"{interaction.user.mention} has kicked {user.mention} for {reason or 'No reason provided'}."
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to kick users."
        )
    except discord.HTTPException:
        await interaction.response.send_message(
            "Failed to kick the user. Please try again later."
        )


# # Slash command to check bot ping
# @bot.tree.command(name="ping", description="Check the bot's ping.")
# @app_commands.checks.has_permissions(manage_messages=True)
# @app_commands.guilds(discord.Object(id=SERVER_ID))
# async def ping(interaction: discord.Interaction):
#     latency = bot.latency * 1000  # Convert to milliseconds
#     await interaction.response.send_message(f"Pong! {latency:.2f}ms")


# A dictionary to store the roles of muted users
muted_users_roles = {}


@bot.tree.command(name="mute", description="Mute a user indefinitely.")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def mute(interaction: discord.Interaction, user: discord.Member):
    guild = interaction.guild
    muted_role = guild.get_role(MUTED_ROLE_ID)

    if not muted_role:
        await interaction.response.send_message(
            "Muted role not found. Please set up a role with the appropriate permissions."
        )
        return

    # Store the user's current roles and remove them
    user_roles = user.roles[1:]  # Exclude @everyone role
    muted_users_roles[user.id] = user_roles

    try:
        await user.remove_roles(*user_roles)
        await user.add_roles(muted_role)
        await interaction.response.send_message(f"Muted {user.mention} indefinitely.")
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to mute this user."
        )
    except discord.HTTPException:
        await interaction.response.send_message(
            "Failed to mute the user. Please try again later."
        )


@bot.tree.command(name="unmute", description="Unmute a user.")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def unmute(interaction: discord.Interaction, user: discord.Member):
    guild = interaction.guild
    muted_role = guild.get_role(MUTED_ROLE_ID)

    if not muted_role:
        await interaction.response.send_message(
            "Muted role not found. Please set up a role with the appropriate permissions."
        )
        return

    if user.id not in muted_users_roles:
        await interaction.response.send_message(f"{user.mention} is not muted.")
        return

    # Retrieve and restore the user's roles
    user_roles = muted_users_roles.pop(user.id, [])

    try:
        await user.remove_roles(muted_role)
        await user.add_roles(*user_roles)
        await interaction.response.send_message(f"Unmuted {user.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to unmute this user."
        )
    except discord.HTTPException:
        await interaction.response.send_message(
            "Failed to unmute the user. Please try again later."
        )


@bot.tree.command(name="muted", description="List all currently muted users.")
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def muted(interaction: discord.Interaction):
    guild = interaction.guild
    muted_role = guild.get_role(MUTED_ROLE_ID)
    if not muted_role:
        await interaction.response.send_message(
            "Muted role not found. Please set up a role with the appropriate permissions."
        )
        return

    # Find all members with the muted role
    muted_members = [member for member in guild.members if muted_role in member.roles]

    if not muted_members:
        await interaction.response.send_message("No users are currently muted.")
        return

    # Prepare embed message with muted users list
    embed = discord.Embed(
        title="Currently Muted Users",
        description="List of users currently muted in the server.",
        color=discord.Color.from_rgb(254, 254, 254),
    )

    muted_names = "\n".join([member.display_name for member in muted_members])
    embed.add_field(name="Muted Users", value=muted_names, inline=False)

    try:
        await interaction.response.send_message(embed=embed)
    except discord.HTTPException as e:
        print(f"Failed to send muted users list: {e}")


@bot.tree.command(name="warn", description="Warn a user with a reason.")
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    # Send warning message in server channel
    try:
        await interaction.response.send_message(
            f"{user.mention}, you have been warned: {reason}"
        )
    except discord.HTTPException as e:
        print(f"Failed to send warning message in server channel: {e}")

    # Send warning message via DM
    try:
        await user.send(f"You have been warned in the server for: {reason}")
        await interaction.response.send_message(
            f"Warning sent to {user.mention} via DM."
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            f"Failed to send warning to {user.mention} via DM. They may have DMs disabled."
        )
    except discord.HTTPException as e:
        print(f"Failed to send warning message via DM: {e}")


@bot.tree.command(name="clear", description="Clear a specified number of messages.")
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def clear(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("Please specify a positive integer.")
        return

    await interaction.response.defer(ephemeral=True)  # Acknowledge the interaction

    try:
        # Perform message deletion
        deleted = await interaction.channel.purge(limit=amount + 1)
        # Send ephemeral message indicating successful deletion
        await interaction.followup.send(f"Deleted {len(deleted) - 1} message(s).")
    except discord.Forbidden:
        await interaction.followup.send("I do not have permission to delete messages.")
    except discord.HTTPException as e:
        await interaction.followup.send(f"Failed to delete messages. Error: {e}")
    except asyncio.TimeoutError:
        await interaction.followup.send("Command timed out. Please try again.")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {type(e).__name__} - {e}")


"""
removed these commands as get rate limited from discord

"""
# A dictionary to store the original permissions of channels before they were locked
original_permissions = {}


# @bot.tree.command(name="lock", description="Lock a channel.")
# @app_commands.guilds(discord.Object(id=SERVER_ID))
# async def lock(interaction: discord.Interaction, channel: discord.TextChannel):
#     guild = interaction.guild

#     # Store the original permissions of the channel
#     original_permissions[channel.id] = channel.overwrites_for(guild.default_role)

#     try:
#         await channel.set_permissions(guild.default_role, send_messages=False)
#         await interaction.response.send_message(
#             f"🔒 Channel {channel.mention} has been locked on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
#         )
#     except discord.Forbidden:
#         await interaction.response.send_message(
#             "I do not have permission to manage channel permissions."
#         )
#     except Exception as e:
#         await interaction.response.send_message(
#             f"An error occurred: {type(e).__name__} - {e}"
#         )


# @bot.tree.command(name="unlock", description="Unlock a channel.")
# @app_commands.guilds(discord.Object(id=SERVER_ID))
# async def unlock(interaction: discord.Interaction, channel: discord.TextChannel):
#     guild = interaction.guild

#     try:
#         # Restore the original permissions of the channel if they were stored
#         if channel.id in original_permissions:
#             await channel.set_permissions(
#                 guild.default_role, overwrite=original_permissions[channel.id]
#             )
#             del original_permissions[
#                 channel.id
#             ]  # Remove from dictionary after restoring
#         else:
#             # Default behavior if no original permissions were stored
#             await channel.set_permissions(guild.default_role, send_messages=True)

#         await interaction.response.send_message(
#             f"🔓 Channel {channel.mention} has been unlocked on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
#         )
#     except discord.Forbidden:
#         await interaction.response.send_message(
#             "I do not have permission to manage channel permissions."
#         )
#     except Exception as e:
#         await interaction.response.send_message(
#             f"An error occurred: {type(e).__name__} - {e}"
#         )


@bot.tree.command(name="roleinfo", description="Get information about a role.")
@app_commands.guilds(discord.Object(id=SERVER_ID))
@app_commands.describe(role="Select a role to get information about")
async def roleinfo(interaction: discord.Interaction, role: str):
    guild = interaction.guild
    selected_role = discord.utils.get(guild.roles, name=role)

    if selected_role is None:
        await interaction.response.send_message(f"Role '{role}' not found.")
        return

    embed = discord.Embed(
        title=f"Role Info: {selected_role.name}", color=selected_role.color
    )
    embed.add_field(name="Role ID", value=selected_role.id)
    embed.add_field(name="Color", value=str(selected_role.color))
    embed.add_field(
        name="Created At", value=selected_role.created_at.strftime("%Y-%m-%d %H:%M:%S")
    )
    embed.add_field(name="Position", value=selected_role.position)
    embed.add_field(name="Mentionable", value=str(selected_role.mentionable))
    embed.add_field(name="Managed", value=str(selected_role.managed))
    embed.add_field(
        name="Permissions",
        value=", ".join(perm[0] for perm in selected_role.permissions if perm[1]),
    )

    await interaction.response.send_message(embed=embed)


@roleinfo.autocomplete("role")
async def role_autocomplete(interaction: discord.Interaction, current: str):
    roles = interaction.guild.roles
    return [
        app_commands.Choice(name=role.name, value=role.name)
        for role in roles
        if current.lower() in role.name.lower()
    ]


@bot.tree.command(name="nick", description="Change a user's nickname.")
@app_commands.guilds(discord.Object(id=SERVER_ID))
@admin_only()
async def nick(
    interaction: discord.Interaction, user: discord.Member, *, nickname: str
):
    try:
        await user.edit(nick=nickname)
        await interaction.response.send_message(
            f"Changed nickname for {user.mention} to `{nickname}`"
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to change that user's nickname."
        )
    except discord.HTTPException as e:
        await interaction.response.send_message(
            f"Failed to change nickname. Error: {e}"
        )


@bot.tree.command(name="addrole", description="Add a role to a user.")
@app_commands.guilds(discord.Object(id=SERVER_ID))
@admin_only()
async def addrole(
    interaction: discord.Interaction, user: discord.Member, role: discord.Role
):
    try:
        await user.add_roles(role)
        await interaction.response.send_message(
            f"Added role {role.name} to {user.mention}"
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to add roles."
        )
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Failed to add role. Error: {e}")


@bot.tree.command(name="removerole", description="Remove a role from a user.")
@app_commands.guilds(discord.Object(id=SERVER_ID))
@admin_only()
async def removerole(
    interaction: discord.Interaction, user: discord.Member, role: discord.Role
):
    try:
        await user.remove_roles(role)
        await interaction.response.send_message(
            f"Removed role {role.name} from {user.mention}"
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to remove roles."
        )
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Failed to remove role. Error: {e}")


@bot.tree.command(name="slowmode", description="Set slowmode in a channel.")
@app_commands.guilds(discord.Object(id=SERVER_ID))
@admin_only()
async def slowmode(interaction: discord.Interaction, seconds: int):
    try:
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(
            f"Set slowmode to {seconds} seconds in {interaction.channel.mention}"
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to set slowmode in this channel."
        )
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Failed to set slowmode. Error: {e}")


LINKS_ROLE_ID = 1256386441068417104


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check if the message contains a link
    if "http://" in message.content or "https://" in message.content:
        # Get the roles of the user
        user_roles = message.author.roles

        # Check if the user has the "links" role
        has_links_role = any(role.id == LINKS_ROLE_ID for role in user_roles)

        if not has_links_role:
            # If the user does not have the role, delete the message
            await message.delete()
            # Optionally, send a message to the user explaining why their message was deleted
            await message.channel.send(
                f"{message.author.mention}, you are not allowed to send links in this server.",
                delete_after=10,
            )

    await bot.process_commands(message)


# Command: /purge
@bot.tree.command(
    name="purge", description="Delete a specified number of messages from a user."
)
@app_commands.describe(
    user="The user whose messages will be deleted.",
    amount="The number of messages to delete.",
)
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def cmd_purge(
    interaction: discord.Interaction, user: discord.Member, amount: int
):
    # Check if the user has permission to manage messages
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "You do not have permission to use this command."
        )
        return

    # Ensure interaction is responded to in time
    await interaction.response.defer(ephemeral=True)

    def is_user_message(message):
        return message.author == user

    # Perform the purge operation
    deleted = await interaction.channel.purge(limit=amount, check=is_user_message)

    # Send a confirmation message after purging
    await interaction.followup.send(
        f"Deleted {len(deleted)} messages from {user.mention}."
    )


# services commands

# snapify

snapify_file_path = "./data/services/Snapify/Snapify.json"


# Load Snapify information from JSON file
def load_snapify_info():
    try:
        with open(snapify_file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "title": "Snapify - Snapscore Booster",
            "description": "Boost your Snapscore with Snapify!",
            "features": "Increase your Snapscore quickly and easily.",
            "how_to_use": "Simply install the Snapify app and follow the instructions.",
            "image_url": "https://repository-images.githubusercontent.com/540961388/908c0ce5-f9f9-45d4-be36-6e485ae33111",
            "private_message": "Thank you for your interest in Snapify! Check the server for more details. Here is your Snapify release... https://github.com/unofficialdxnny/Snapify",
        }
    except json.JSONDecodeError:
        return {}


# Save Snapify information to JSON file
def save_snapify_info(info):
    with open(snapify_file_path, "w") as file:
        json.dump(info, file, indent=4)


@bot.tree.command(name="snapify_update", description="Update Snapify information.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def snapify_update(
    interaction: discord.Interaction,
    title: str = None,
    description: str = None,
    features: str = None,
    how_to_use: str = None,
    image_url: str = None,
    private_message: str = None,
):
    # Load current Snapify info
    snapify_info = load_snapify_info()

    # Update fields if provided
    if title is not None:
        snapify_info["title"] = title
    if description is not None:
        snapify_info["description"] = description
    if features is not None:
        snapify_info["features"] = features
    if how_to_use is not None:
        snapify_info["how_to_use"] = how_to_use
    if image_url is not None:
        snapify_info["image_url"] = image_url
    if private_message is not None:
        snapify_info["private_message"] = private_message

    # Save updated information
    save_snapify_info(snapify_info)

    await interaction.response.send_message("Snapify information updated successfully.")


@bot.tree.command(name="snapify", description="Get information about Snapify app")
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def snapify(interaction: discord.Interaction):
    # Load Snapify info
    snapify_info = load_snapify_info()

    # Create an embedded message with Snapify information
    embed = discord.Embed(
        title=snapify_info.get("title", "Snapify - Snapscore Booster"),
        description=snapify_info.get(
            "description", "Boost your Snapscore with Snapify!"
        ),
        color=discord.Color.from_rgb(254, 254, 254),
    )
    embed.add_field(
        name="Features",
        value=snapify_info.get(
            "features", "Increase your Snapscore quickly and easily."
        ),
    )
    embed.add_field(
        name="How to Use",
        value=snapify_info.get(
            "how_to_use", "Simply install the Snapify app and follow the instructions."
        ),
    )
    embed.set_image(
        url=snapify_info.get(
            "image_url",
            "https://repository-images.githubusercontent.com/540961388/908c0ce5-f9f9-45d4-be36-6e485ae33111",
        )
    )

    # Send the embed message in the server
    await interaction.response.send_message("Check out Snapify!", embed=embed)

    # Send a private message to the user
    try:
        await interaction.user.send(
            snapify_info.get(
                "private_message",
                "Thank you for your interest in Snapify! Check the server for more details. Here is your Snapify release... https://github.com/unofficialdxnny/Snapify",
            )
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "Failed to send a private message. They may have DMs disabled."
        )


@bot.tree.command(name="reaction_role", description="Get a role by clicking a button")
@app_commands.guilds(discord.Object(id=SERVER_ID))
async def reaction_role(
    interaction: discord.Interaction, role: discord.Role, emoji: str
):
    # Check if the user is an admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "You do not have permission to use this command. Admins only.", ephemeral=True
        )
        return
    view = View()

    # Check if the emoji is a custom emoji or a standard emoji
    if emoji.startswith("<") and emoji.endswith(">"):
        # Custom emoji
        try:
            # Extract the emoji name and ID
            emoji_name = emoji.split(":")[1]
            emoji_id = int(emoji.split(":")[2][:-1])
            custom_emoji = discord.PartialEmoji(name=emoji_name, id=emoji_id)
        except (IndexError, ValueError):
            await interaction.response.send_message(
                "Invalid custom emoji format. Please use the format <:name:id>."
            )
            return
    else:
        # Standard emoji
        custom_emoji = emoji

    async def button_callback(interaction: discord.Interaction):
        if role not in interaction.user.roles:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(
                    f"You have been given the {role.mention} role!", ephemeral=True
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I do not have permission to add this role.", ephemeral=True
                )
            except discord.HTTPException:
                await interaction.response.send_message(
                    "Failed to add the role. Please try again later.", ephemeral=True
                )
        else:
            await interaction.response.send_message("You already have this role.", ephemeral=True)

    button = Button(label="Get Role", emoji=custom_emoji)
    button.callback = button_callback  # Assign the callback to the button

    view.add_item(button)

    await interaction.response.send_message(
        f"Click the button to get the {role.mention} role!", view=view
    )


current_directory = os.getcwd()
current_file = os.path.join(current_directory, "PloitZ", "bot.py")


@bot.tree.command(name="reload", description="Restart the bot.")
@app_commands.guilds(discord.Object(id=SERVER_ID))
@admin_only()
async def restart(interaction: discord.Interaction):
    await interaction.response.send_message("Restarting...")
    os.system(f"python {current_file}")
    os._exit(1)




@bot.tree.command(name="create_role", description="Creates a role easily")
@app_commands.guilds(discord.Object(id=SERVER_ID))
@admin_only()
async def create_role(interaction: discord.Interaction, name: str):
    guild = interaction.guild
    await guild.create_role(name=name)
    await interaction.response.send_message(f'Role `{name}` has been created')


@bot.tree.command(name="delete_role", description="Deletes a role easily")
@app_commands.guilds(discord.Object(id=SERVER_ID))
@admin_only()
async def delete_role(interaction: discord.Interaction, role: str):
    guild = interaction.guild
    selected_role = discord.utils.get(guild.roles, name=role)
    if selected_role:
        await selected_role.delete()
        await interaction.response.send_message(f'Role `{role}` has been deleted')
    else:
        await interaction.response.send_message(f'Role `{role}` not found')


@delete_role.autocomplete("role")
async def role_autocomplete(interaction: discord.Interaction, current: str):
    roles = interaction.guild.roles
    return [
        app_commands.Choice(name=role.name, value=role.name)
        for role in roles
        if current.lower() in role.name.lower()
    ]


# Run the bot
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"An error occurred: {e}")
