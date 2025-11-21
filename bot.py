import os
import discord
from discord import ActivityType

# ========= CONFIG VIA ENVIRONMENT VARIABLES =========
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
# ====================================================

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True  # lets us see deafen/undeafen

client = discord.Client(intents=intents)

# user_id -> original_channel_id
previous_channels: dict[int, int] = {}


def is_streaming(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> bool:
    """
    Returns True if the user is streaming in any way we care about:
    - Go Live in a voice channel (self_stream)
    - Discord "Streaming" activity (e.g., Twitch)
    """
    # Go Live in the current voice channel
    if getattr(after, "self_stream", False):
        return True

    # Any streaming activity on the member
    for activity in member.activities or []:
        if isinstance(activity, discord.Streaming):
            return True
        if getattr(activity, "type", None) == ActivityType.streaming:
            return True

    return False


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("Watching all guilds the bot is a member of.")
    for guild in client.guilds:
        target = get_deafened_channel(guild)
        target_desc = target.name if target else "<no AFK channel found>"
        print(f" - {guild.name} (ID: {guild.id}) -> AFK channel: {target_desc}")
    print("Deafen mover bot is running.")


def get_deafened_channel(guild: discord.Guild) -> discord.VoiceChannel | None:
    """Return the AFK voice channel for this guild, if any."""
    if guild.afk_channel:
        return guild.afk_channel

    for channel in guild.voice_channels:
        if channel.name.lower() == "afk":
            return channel

    return None


@client.event
async def on_voice_state_update(member, before, after):
    # Ignore bots
    if member.bot:
        return

    # Debug line so you can see events in Railway logs
    print(
        f"[VS] member={member} guild={member.guild.id} | "
        f"self_deaf {before.self_deaf}->{after.self_deaf} | "
        f"deaf {before.deaf}->{after.deaf} | "
        f"self_stream {getattr(before, 'self_stream', None)}->{getattr(after, 'self_stream', None)} | "
        f"chan {getattr(before.channel, 'id', None)}->{getattr(after.channel, 'id', None)}"
    )

    # If user is streaming, never move them
    if is_streaming(member, before, after):
        print(f"[VS] {member} is streaming, not moving them.")
        return

    # Trigger on either self-deafen OR server-deafen
    just_deafened = (
        (not before.self_deaf and after.self_deaf)
        or (not before.deaf and after.deaf)
    )
    just_undeafened = (
        (before.self_deaf and not after.self_deaf)
        or (before.deaf and not after.deaf)
    )

    # CASE 1: user just deafened
    if just_deafened:
        print(f"[VS] {member} just deafened")

        # If they're not in a voice channel, nothing to do
        if after.channel is None:
            print("[VS] User is not in a voice channel, ignoring")
            return

        # Remember where they were
        previous_channels[member.id] = after.channel.id

        # Get the special "deafened" channel (server AFK channel)
        target = get_deafened_channel(member.guild)
        if not isinstance(target, discord.VoiceChannel):
            print("[VS] ERROR: No AFK voice channel found for this server.")
            return

        # If they're already in that channel, don't move
        if after.channel.id == target.id:
            print("[VS] User already in deafened channel, not moving")
            return

        try:
            await member.move_to(target)
            print(f"[VS] Moved {member.display_name} to deafened channel.")
        except discord.Forbidden:
            print("[VS] Missing permission to move members.")
        except discord.HTTPException as e:
            print(f"[VS] Failed to move member: {e}")

    # CASE 2: user just undeafened
    elif just_undeafened:
        print(f"[VS] {member} just undeafened")

        original_id = previous_channels.pop(member.id, None)
        if original_id is None:
            print("[VS] No stored original channel for this user, not moving back")
            return

        # They must be currently in the deafened channel for us to move them back
        target = get_deafened_channel(member.guild)
        if after.channel is None or not target or after.channel.id != target.id:
            print("[VS] User is not in deafened channel anymore, not moving back")
            return

        original = member.guild.get_channel(original_id)
        if not isinstance(original, discord.VoiceChannel):
            # original channel deleted or invalid
            print("[VS] Original channel no longer exists or is not a voice channel")
            return

        # If somehow already there, do nothing
        if after.channel.id == original.id:
            print("[VS] User already in original channel, not moving back")
            return

        try:
            await member.move_to(original)
            print(f"[VS] Moved {member.display_name} back to {original.name}.")
        except discord.Forbidden:
            print("[VS] Missing permission to move members back.")
        except discord.HTTPException as e:
            print(f"[VS] Failed to move member back: {e}")


if __name__ == "__main__":
    missing = []
    if not BOT_TOKEN:
        missing.append("DISCORD_TOKEN")

    if missing:
        raise RuntimeError("You must set env vars: " + ", ".join(missing))

    client.run(BOT_TOKEN)

