import os
import discord

# ========= CONFIG VIA ENVIRONMENT VARIABLES =========
# These must be set in Railway's "Variables" settings
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
DEAFENED_CHANNEL_ID = int(os.getenv("DEAFENED_CHANNEL_ID", "0"))
# ====================================================

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True  # lets us see deafen/undeafen

client = discord.Client(intents=intents)

# user_id -> original_channel_id
previous_channels = {}


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("Deafen mover bot is running.")


@client.event
async def on_voice_state_update(member, before, after):
    # Ignore bots
    if member.bot:
        return

    # Only act on the one server we care about
    if member.guild.id != GUILD_ID:
        return

    just_deafened = (not before.self_deaf and after.self_deaf)
    just_undeafened = (before.self_deaf and not after.self_deaf)

    # CASE 1: user just self-deafened
    if just_deafened:
        # If they're not in a voice channel, nothing to do
        if after.channel is None:
            return

        # Remember where they were
        previous_channels[member.id] = after.channel.id

        # Get the special "deafened" channel
        target = member.guild.get_channel(DEAFENED_CHANNEL_ID)
        if not isinstance(target, discord.VoiceChannel):
            print("ERROR: DEAFENED_CHANNEL_ID is not a valid voice channel.")
            return

        # If they're already in that channel, don't move
        if after.channel.id == DEAFENED_CHANNEL_ID:
            return

        try:
            await member.move_to(target)
            print(f"Moved {member.display_name} to deafened channel.")
        except discord.Forbidden:
            print("Missing permission to move members.")
        except discord.HTTPException as e:
            print(f"Failed to move member: {e}")

    # CASE 2: user just self-undeafened
    elif just_undeafened:
        original_id = previous_channels.pop(member.id, None)
        if original_id is None:
            return

        # They must be currently in the deafened channel for us to move them back
        if after.channel is None or after.channel.id != DEAFENED_CHANNEL_ID:
            return

        original = member.guild.get_channel(original_id)
        if not isinstance(original, discord.VoiceChannel):
            # original channel deleted or invalid
            return

        # If somehow already there, do nothing
        if after.channel.id == original.id:
            return

        try:
            await member.move_to(original)
            print(f"Moved {member.display_name} back to {original.name}.")
        except discord.Forbidden:
            print("Missing permission to move members back.")
        except discord.HTTPException as e:
            print(f"Failed to move member back: {e}")


if __name__ == "__main__":
    if not BOT_TOKEN:
        raise RuntimeError("You must set DISCORD_TOKEN, GUILD_ID, and DEAFENED_CHANNEL_ID env vars.")
    if not GUILD_ID or not DEAFENED_CHANNEL_ID:
        raise RuntimeError("GUILD_ID and DEAFENED_CHANNEL_ID must be non-zero integers.")
    client.run(BOT_TOKEN)

