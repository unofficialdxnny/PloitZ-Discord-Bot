import os
import json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime, timedelta
import asyncio
import aiohttp


# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("TOKEN")
TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID", ""))  # Add your test guild ID here
TICKETS_CATEGORY = int(os.getenv("TICKETS_CATEGORY", ""))


# # File to store settings
# SETTINGS_FILE = "./PloitZ/settings.json"

# # Initialize settings with an empty dictionary
# settings = {}


# def load_settings():
#     global settings
#     try:
#         if os.path.exists(SETTINGS_FILE):
#             with open(SETTINGS_FILE, "r") as f:
#                 settings = json.load(f)
#                 print("Settings loaded successfully.")
#         else:
#             save_settings()  # Create an empty settings file if it doesn't exist
#     except json.JSONDecodeError:
#         settings = {}  # Initialize with empty dictionary if file is empty or invalid
#     except Exception as e:
#         print(f"Error loading settings: {e}")


# def save_settings():
#     try:
#         with open(SETTINGS_FILE, "w") as f:
#             json.dump(settings, f, indent=4)
#         print("Settings saved successfully.")
#     except Exception as e:
#         print(f"Error saving settings: {e}")


# # Load settings on startup
# load_settings()

# Initialize bot
intents = discord.Intents.default()
intents.reactions = True  # Enable reaction intents
intents.guilds = True  # Enable guild intents
intents.messages = True  # Enable message intents
intents.members = True  # Enable member intents
intents.presences = True  # Enable presence intents
intents.guild_messages = True
bot = commands.Bot(command_prefix="!", intents=intents)


WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
RULES_CHANNEL_ID = int(os.getenv("RULES_CHANNEL_ID"))
VERIFICATION_CHANNEL_ID = int(os.getenv("VERIFICATION_CHANNEL_ID"))
MEMBERS_ROLE_ID = int(os.getenv("MEMBERS_ROLE_ID"))
REACTION_EMOJI = "✅"
UNVERIFIED_ROLE_ID = int(os.getenv("UNVERIFIED_ROLE_ID"))
MUTED_ROLE_ID = int(os.getenv("MUTED_ROLE_ID", ""))


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    try:
        # Sync global commands
        synced_global = await bot.tree.sync()
        print(f"Successfully synced {len(synced_global)} global command(s)")

        verification_channel = bot.get_channel(VERIFICATION_CHANNEL_ID)
        if not verification_channel:
            print(f"Verification channel with ID {VERIFICATION_CHANNEL_ID} not found.")
            return

        # Check if there is an existing verification message
        verification_message = None
        async for message in verification_channel.history():
            if message.author == bot.user and REACTION_EMOJI in [
                reaction.emoji for reaction in message.reactions
            ]:
                verification_message = message
                break

        if verification_message is None:
            # Create an embed for the verification message
            embed = discord.Embed(
                title="Verification",
                description="React with ✅ to verify yourself and gain access to the server.",
                color=discord.Color.blue(),
            )

            # Send the verification embed message
            try:
                verification_message = await verification_channel.send(embed=embed)
                await verification_message.add_reaction(REACTION_EMOJI)
                print(f"Created verification message in #{verification_channel.name}")
            except discord.HTTPException as e:
                print(f"Failed to create verification message: {e}")

        servers = len(bot.guilds)
        members = sum(guild.member_count - 1 for guild in bot.guilds)

        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{members} members",
            )
        )

    except Exception as e:
        print(f"Error syncing global commands: {e}")

    try:
        # Sync guild-specific commands
        test_guild = discord.Object(id=TEST_GUILD_ID)
        synced_guild = await bot.tree.sync(guild=test_guild)
        print(
            f"Successfully synced {len(synced_guild)} guild command(s) in {TEST_GUILD_ID}"
        )
    except Exception as e:
        print(f"Error syncing guild commands: {e}")


@bot.event
async def on_raw_reaction_add(payload):
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
            title=f"Welcome to {member.guild.name}, {member.name}!",
            description=f"We are glad you joined us. Please read the rules in <#{RULES_CHANNEL_ID}> and enjoy your stay!",
            color=discord.Color.blue(),
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


# ban command
@bot.tree.command(name="ban", description="Bans a user from the server.")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
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
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
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


# Slash command to check bot ping
@bot.tree.command(name="ping", description="Check the bot's ping.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def ping(interaction: discord.Interaction):
    latency = bot.latency * 1000  # Convert to milliseconds
    await interaction.response.send_message(f"Pong! {latency:.2f}ms")


# Slash command to get user information
@bot.tree.command(name="user", description="Get information about a user.")
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def get_user_info(interaction: discord.Interaction, user: discord.Member = None):
    if user is None:
        await interaction.response.send_message("Please specify a user.")
        return

    # Basic Information
    username = user.name
    discriminator = user.discriminator
    user_id = user.id
    avatar_url = user

    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
    display_name = user.display_name

    # Timestamps
    created_at = user.created_at.strftime("%Y-%m-%d %H:%M:%S")
    joined_at = (
        user.joined_at.strftime("%Y-%m-%d %H:%M:%S")
        if user.joined_at
        else "Not available"
    )

    # Roles
    roles = [role.name for role in user.roles if role.name != "@everyone"]
    roles_str = ", ".join(roles) if roles else "No roles"

    # Status
    status = str(user.status).title()

    # Activities
    activities = []
    for activity in user.activities:
        if isinstance(activity, discord.Spotify):
            activities.append(f"Listening to {activity.title} by {activity.artist}")
        elif isinstance(activity, discord.Game):
            activities.append(f"Playing {activity.name}")
        elif isinstance(activity, discord.Streaming):
            activities.append(f"Streaming {activity.name}")
        elif isinstance(activity, discord.CustomActivity):
            activities.append(activity.name)
        elif isinstance(activity, discord.Activity):
            activities.append(f"{activity.type} {activity.name}")

    activities_str = "\n".join(activities) if activities else "None"

    # Other Info
    boosting_status = "Boosting" if user.premium_since else "Not Boosting"
    highest_role = user.top_role.name if user.top_role.name != "@everyone" else "None"
    permissions = [perm[0] for perm in user.guild_permissions if perm[1]]
    permissions_str = ", ".join(permissions) if permissions else "None"

    # Create an embed with user information
    embed = discord.Embed(
        title=f"User Information - {username}#{discriminator}",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow(),
    )
    embed.set_thumbnail(url=avatar_url)
    embed.add_field(name="Username", value=username)
    embed.add_field(name="Discriminator", value=discriminator)
    embed.add_field(name="User ID", value=user_id)
    embed.add_field(name="Avatar", value=f"[Link]({avatar_url})")
    embed.add_field(name="Display Name", value=display_name)
    embed.add_field(name="Created At", value=created_at)
    embed.add_field(name="Joined At", value=joined_at)
    embed.add_field(name="Roles", value=roles_str)
    embed.add_field(name="Status", value=status)
    embed.add_field(name="Boosting Status", value=boosting_status)
    embed.add_field(name="Highest Role", value=highest_role)
    embed.add_field(name="Permissions", value=permissions_str)
    embed.add_field(name="Activities", value=activities_str, inline=False)

    try:
        await interaction.response.send_message(embed=embed)
    except discord.HTTPException as e:
        print(f"Failed to send user info: {e}")


# Slash command to get user avatar
@bot.tree.command(name="avatar", description="Get the avatar of a user.")
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def avatar(interaction: discord.Interaction, user: discord.Member = None):
    # Ensure the user mentioned is a valid Discord user
    if user is not None:
        # Fetch avatar URL
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

        # Create an embed with the avatar image
        embed = discord.Embed(
            title=f"Avatar of {user.name}#{user.discriminator}",
            color=discord.Color.blue(),
        )
        embed.set_image(url=avatar_url)

        # Send the embed as a response to the interaction
        await interaction.response.send_message(embed=embed)
    else:
        # If user mention is invalid, respond with an error message
        await interaction.response.send_message(
            "Please mention a valid user.", ephemeral=True
        )


@bot.tree.command(name="serverinfo", description="Show information about the server.")
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def server_info(interaction: discord.Interaction):
    guild = interaction.guild

    if guild:
        # Fetching guild information
        guild_name = guild.name
        guild_id = guild.id
        guild_owner = guild.owner
        guild_created_at = guild.created_at.strftime("%Y-%m-%d %H:%M:%S")
        guild_member_count = guild.member_count
        guild_roles = ", ".join(
            role.name for role in guild.roles if role.name != "@everyone"
        )

        # Creating an embed with server information
        embed = discord.Embed(
            title=f"Server Information - {guild_name}", color=discord.Color.blue()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        embed.add_field(name="Server ID", value=guild_id, inline=False)
        embed.add_field(
            name="Owner",
            value=f"{guild_owner.name}#{guild_owner.discriminator}",
            inline=False,
        )
        embed.add_field(name="Created At", value=guild_created_at, inline=False)
        embed.add_field(name="Member Count", value=guild_member_count, inline=False)
        embed.add_field(name="Roles", value=guild_roles, inline=False)

        # Sending the embed as a response to the interaction
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(
            "Failed to fetch server information.", ephemeral=True
        )


@bot.tree.command(name="ticket", description="Create a support ticket.")
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def ticket(interaction: discord.Interaction, problem: str):
    guild = interaction.guild
    user = interaction.user  # Get the user who invoked the command

    # Specify the category ID where the ticket channels will be created
    category_id = TICKETS_CATEGORY

    # Fetch the category object
    category = discord.utils.get(guild.categories, id=category_id)

    if category is None:
        await interaction.response.send_message(
            "Category not found. Please configure the bot correctly."
        )
        return

    # Create channel name and permissions
    channel_name = f"{user.name.lower()}-{problem.lower().replace(' ', '-')}"
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

    try:
        # Create the support ticket channel under the specified category
        ticket_channel = await guild.create_text_channel(
            channel_name, category=category, overwrites=overwrites
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I don't have permission to create channels."
        )
        return
    except discord.HTTPException:
        await interaction.response.send_message(
            "Failed to create support ticket channel. Please try again later."
        )
        return

    # Create an embed with the user's problem
    embed = discord.Embed(
        title="Support Ticket",
        description=f"**User:** {user.mention}\n**Problem:** {problem}",
        color=discord.Color.blue(),
    )

    # Send the embed to the support ticket channel
    try:
        await ticket_channel.send(embed=embed)
        await interaction.response.send_message(
            f"Support ticket created in {ticket_channel.mention}."
        )
    except discord.HTTPException:
        await interaction.response.send_message(
            "Failed to send embed message to support ticket channel."
        )


@bot.tree.command(name="close", description="Close a support ticket.")
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def close(interaction: discord.Interaction):
    guild = interaction.guild
    author = interaction.user

    # Check if the command is used in a ticket channel
    if interaction.channel.category_id != TICKETS_CATEGORY:
        await interaction.response.send_message(
            "/close may only be used in a ticket channel."
        )
        return

    # Check if the author is an admin
    if not author.guild_permissions.administrator:
        await interaction.response.send_message(
            "You must be an admin to use this command."
        )
        return

    # Fetch the category object for tickets
    category = discord.utils.get(guild.categories, id=TICKETS_CATEGORY)

    if category is None:
        await interaction.response.send_message(
            "Tickets category not found. Please configure the bot correctly."
        )
        return

    # Get list of ticket channels under the category
    ticket_channels = [
        channel
        for channel in category.channels
        if isinstance(channel, discord.TextChannel)
    ]

    if not ticket_channels:
        await interaction.response.send_message(
            "No ticket channels found in the tickets category."
        )
        return

    # Attempt to delete the current channel
    try:
        await interaction.channel.delete()
        await interaction.response.send_message(
            f"Successfully closed {interaction.channel.name}."
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to delete this channel."
        )
    except discord.HTTPException:
        await interaction.response.send_message(
            "Failed to delete the channel. Please try again later."
        )


# Path to commands.json
COMMANDS_FILE = os.path.join(os.path.dirname(__file__), "commands.json")


# Read commands from commands.json
def read_commands():
    try:
        with open(COMMANDS_FILE, "r") as f:
            commands_data = json.load(f)
        return commands_data
    except FileNotFoundError:
        print(f"FileNotFoundError: '{COMMANDS_FILE}' not found.")
        return {}
    except json.JSONDecodeError:
        print(
            f"JSONDecodeError: Unable to parse '{COMMANDS_FILE}'. Check if the file contains valid JSON data."
        )
        return {}


@bot.tree.command(name="help", description="Show all available commands.")
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def help_command(interaction: discord.Interaction):
    commands_data = read_commands()

    embed = discord.Embed(
        title="PloitZ Bot Commands",
        description="Here are the available commands categorized:",
        color=discord.Color.blue(),
    )

    for category, commands_list in commands_data.items():
        if commands_list:  # Check if there are commands in this category
            command_list_str = "\n".join(
                f"`/{command['name']}` - {command['description']}"
                for command in commands_list
            )
            embed.add_field(name=category, value=command_list_str, inline=False)

    try:
        await interaction.response.send_message(embed=embed)
    except discord.HTTPException as e:
        print(f"Failed to send help embed: {e}")


# mute users
muted_users = {}


@bot.tree.command(name="mute", description="Mute a user indefinitely.")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def mute(interaction: discord.Interaction, user: discord.Member):
    guild = interaction.guild
    muted_role = guild.get_role(MUTED_ROLE_ID)
    if not muted_role:
        await interaction.response.send_message(
            "Muted role not found. Please set up a role with the appropriate permissions."
        )
        return

    # Mute the user
    try:
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
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def unmute(interaction: discord.Interaction, user: discord.Member):
    guild = interaction.guild
    muted_role = guild.get_role(MUTED_ROLE_ID)
    if not muted_role:
        await interaction.response.send_message(
            "Muted role not found. Please set up a role with the appropriate permissions."
        )
        return

    # Unmute the user
    try:
        await user.remove_roles(muted_role)
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
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
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
        color=discord.Color.blue(),
    )

    muted_names = "\n".join([member.display_name for member in muted_members])
    embed.add_field(name="Muted Users", value=muted_names, inline=False)

    try:
        await interaction.response.send_message(embed=embed)
    except discord.HTTPException as e:
        print(f"Failed to send muted users list: {e}")


@bot.tree.command(name="warn", description="Warn a user with a reason.")
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    # Send warning message in server channel
    try:
        await interaction.response.send_message(
            f"{user.mention}, you have been warned for: {reason}"
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
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def clear(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message(
            "Please specify a positive integer.", ephemeral=True
        )
        return

    await interaction.response.defer()  # Acknowledge the interaction

    try:
        # Perform message deletion
        deleted = await interaction.channel.purge(limit=amount + 1)

        # Send ephemeral message indicating successful deletion
        await interaction.followup.send(
            f"Deleted {len(deleted) - 1} message(s).", ephemeral=True
        )
    except discord.Forbidden:
        await interaction.followup.send(
            "I do not have permission to delete messages.", ephemeral=True
        )
    except discord.HTTPException as e:
        await interaction.followup.send(
            f"Failed to delete messages. Error: {e}", ephemeral=True
        )
    except asyncio.TimeoutError:
        await interaction.followup.send(
            "Command timed out. Please try again.", ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"An error occurred: {type(e).__name__} - {e}", ephemeral=True
        )


@bot.tree.command(name="lock", description="Lock a channel.")
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def lock(interaction: discord.Interaction, channel: discord.TextChannel):
    try:
        await channel.set_permissions(
            interaction.guild.default_role, send_messages=False
        )
        await interaction.response.send_message(
            f"🔒 Channel {channel.mention} has been locked on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to manage channel permissions.", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"An error occurred: {type(e).__name__} - {e}", ephemeral=True
        )


@bot.tree.command(name="unlock", description="Unlock a channel.")
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
async def unlock(interaction: discord.Interaction, channel: discord.TextChannel):
    try:
        await channel.set_permissions(
            interaction.guild.default_role, send_messages=True
        )
        await interaction.response.send_message(
            f"🔓 Channel {channel.mention} has been unlocked on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to manage channel permissions.", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"An error occurred: {type(e).__name__} - {e}", ephemeral=True
        )


@bot.tree.command(name="roleinfo", description="Get information about a role.")
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
@app_commands.describe(role="Select a role to get information about")
async def roleinfo(interaction: discord.Interaction, role: str):
    guild = interaction.guild
    selected_role = discord.utils.get(guild.roles, name=role)

    if selected_role is None:
        await interaction.response.send_message(
            f"Role '{role}' not found.", ephemeral=True
        )
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


@bot.tree.command(name="poll", description="Create a poll")
@app_commands.guilds(discord.Object(id=TEST_GUILD_ID))
@app_commands.describe(
    question="The poll question",
    option1="First option",
    option2="Second option",
    option3="Third option (optional)",
    option4="Fourth option (optional)",
)
async def poll(
    interaction: discord.Interaction,
    question: str,
    option1: str,
    option2: str,
    option3: str = None,
    option4: str = None,
):
    # Check if the user is an admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "You do not have permission to use this command."
        )
        return

    # Create the poll embed
    embed = discord.Embed(
        title="Poll", description=question, color=discord.Color.blue()
    )
    options = [option1, option2, option3, option4]
    options = [opt for opt in options if opt]  # Filter out None values

    for i, option in enumerate(options, 1):
        embed.add_field(name=f"Option {i}", value=option, inline=False)

    # Send the poll and add reactions
    poll_message = await interaction.channel.send(embed=embed)
    reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

    for i in range(len(options)):
        await poll_message.add_reaction(reactions[i])

    await interaction.response.send_message("Poll created successfully!")


# Run the bot with the token
bot.run(TOKEN)
