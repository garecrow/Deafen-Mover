import os
import asyncio
import discord
from discord import ActivityType

# ========= CONFIG VIA ENVIRONMENT VARIABLES =========
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
# ====================================================

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.members = True

client = discord.Client(intents=intents)

# user_id -> original_channel_id
previous_channels: dict[int, int] = {}


def is_streaming(member: discord.Member, voice_state: discord.VoiceState | None = None) -> bool:
    """Return True if the member is streaming (Go Live or external stream)."""
    # Check the voice state first if provided
    if voice_state and getattr(voice_state, "self_stream", False):
        return True
    # Check activities
    for activity in member.activities or []:
        if isinstance(activity, discord.Streaming):
            return True
        if getattr(activity, "type", None) == ActivityType.streaming:
            return True
    return False


def get_deafened_channel(guild: discord.Guild) -> discord.VoiceChannel | None:
    """Return the AFK channel (guild AFK or one named 'afk')."""
    if guild.afk_channel:
        return guild.afk_channel
    for ch in guild.voice_channels:
        if ch.name.lower() == "afk":
            return ch
    return None


async def move_if_still_deafened(member: discord.Member, target: discord.VoiceChannel, delay: int = 10):
    """Wait for delay, then move the member to AFK if still deafened."""
    await asyncio.sleep(delay)
    # Check if still deafened AND not streaming before moving
    if (member.voice and (member.voice.self_deaf or member.voice.deaf) 
            and member.voice.channel.id != target.id
            and not is_streaming(member, member.voice)):
        try:
            await member.move_to(target)
        except Exception as e:
            print(f"Delayed move failed: {e}")


@client.event
async def on_ready():
    print(f"Deafen mover bot online: {client.user}")
    for guild in client.guilds:
        target = get_deafened_channel(guild)
        print(f"- {guild.name}: AFK = {target.name if target else 'None'}")


@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return

    target = get_deafened_channel(member.guild)
    if not isinstance(target, discord.VoiceChannel):
        print(f"No AFK channel found in guild {member.guild.name}.")
        return

    # ===== Streaming state checks =====
    was_streaming = is_streaming(member, before)
    is_currently_streaming = is_streaming(member, after)

    # ===== Stopped streaming while deafened =====
    stopped_streaming_while_deafened = was_streaming and not is_currently_streaming and (after.self_deaf or after.deaf)
    if stopped_streaming_while_deafened and after.channel and after.channel.id != target.id:
        previous_channels[member.id] = after.channel.id
        asyncio.create_task(move_if_still_deafened(member, target, delay=10))
        return

    # ===== Joined while deafened =====
    joined_while_deafened = before.channel is None and after.channel and (after.self_deaf or after.deaf)
    # Check if streaming when joining (should not move if streaming)
    if joined_while_deafened and not is_currently_streaming:
        previous_channels[member.id] = after.channel.id
        if after.channel.id != target.id:
            try:
                await member.move_to(target)
                try:
                    await member.send(
                        "You have been automatically moved to AFK. Please undeafen before joining a voice room. Doing so now will automatically bring you to the voice room you wanted."
                    )
                except discord.Forbidden:
                    pass
            except Exception as e:
                print(f"Move failed (join-deafened): {e}")
        return

    # ===== Just deafened =====
    just_deafened = (not before.self_deaf and after.self_deaf) or (not before.deaf and after.deaf)
    # Don't move if currently streaming
    if just_deafened and after.channel and not is_currently_streaming:
        previous_channels[member.id] = after.channel.id
        if after.channel.id != target.id:
            try:
                await member.move_to(target)
            except Exception as e:
                print(f"Move failed (just deafened): {e}")
        return

    # ===== Just undeafened =====
    just_undeafened = (before.self_deaf and not after.self_deaf) or (before.deaf and not after.deaf)
    if just_undeafened:
        original_id = previous_channels.pop(member.id, None)
        if original_id and after.channel and after.channel.id == target.id:
            original = member.guild.get_channel(original_id)
            if isinstance(original, discord.VoiceChannel):
                try:
                    await member.move_to(original)
                except Exception as e:
                    print(f"Move back failed: {e}")

    # ===== Moved out of AFK while still deafened =====
    moved_out_while_deafened = (
        before.channel and after.channel
        and before.channel.id == target.id
        and after.channel.id != target.id
        and (after.self_deaf or after.deaf)
    )
    # Don't move back if currently streaming
    if moved_out_while_deafened and not is_currently_streaming:
        previous_channels[member.id] = after.channel.id
        try:
            await member.move_to(target)
            try:
                await member.send(
                    "You are still deafened, so you cannot be outside AFK. Undeafen yourself, and you will be moved there automatically."
                )
            except discord.Forbidden:
                pass
        except Exception as e:
            print(f"Move failed (moved-out-while-deafened): {e}")
        return


if __name__ == "__main__":
    if not BOT_TOKEN:
        raise RuntimeError("You must set DISCORD_TOKEN")
    client.run(BOT_TOKEN)
