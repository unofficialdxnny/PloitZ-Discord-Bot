import discord
from discord.ext import commands
from discord import app_commands
import random
from gtts import gTTS
import os
import asyncio


class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.audio_dir = os.path.join(os.path.dirname(__file__), "..", "audio")
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

    def generate_tts_audio(self, text, filename):
        # List of available languages for gTTS
        languages = ["en", "es", "fr", "de", "it"]
        lang = random.choice(languages)

        tts = gTTS(text=text, lang=lang)
        tts.save(filename)

    @app_commands.guilds(*[discord.Object(id=guild_id) for guild_id in GUILD_IDS])
    @app_commands.command(name="say", description="Say a phrase in a random voice")
    async def say(self, interaction: discord.Interaction, phrase: str):
        voice_channel = (
            interaction.user.voice.channel if interaction.user.voice else None
        )

        if not voice_channel:
            await interaction.response.send_message(
                "You need to be in a voice channel to use this command.", ephemeral=True
            )
            return

        # Generate TTS audio file
        audio_file = os.path.join(self.audio_dir, f"{interaction.id}.mp3")
        self.generate_tts_audio(phrase, audio_file)

        # Connect to voice channel and play audio
        vc = await voice_channel.connect()
        vc.play(
            discord.FFmpegPCMAudio(audio_file),
            after=lambda e: print(f"Finished playing: {e}"),
        )

        # Wait for the audio to finish playing
        while vc.is_playing():
            await asyncio.sleep(1)

        # Disconnect and clean up
        await vc.disconnect()
        os.remove(audio_file)

        await interaction.response.send_message(f"Said the phrase: {phrase}")


async def setup(bot):
    await bot.add_cog(TTS(bot))
