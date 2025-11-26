import os
import discord
from discord import ActivityType

# ========= CONFIG VIA ENVIRONMENT VARIABLES =========
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
# ====================================================

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True  # allows tracking deaf/mute changes
intents.members = True       # needed so the bot can DM users

client = discord.Client(intents=intents)

# user_id -> original_channel_id
previous_channels: dict[int, int] = {}


def is_streaming(member: discord.Member) -> bool:
    """Return True if the member is streaming (Go Live or external stream)."""
    # member.voice may be None if they're not in voice; getattr covers that
    if getattr(member.voice, "self_stream", False):
        return True
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


@client.event
async def on_ready():
    print(f"Deafen mover bot online: {client.user}")
    for guild in client.guilds:
        target = get_deafened_channel(guild)
        print(f"- {guild.name}: AFK = {target.name if target else 'None'}")


@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # Ignore bots entirely
    if member.bot:
        return

    # Streaming users should not be moved
    if is_streaming(member):
        return

    # User joined a channel while already deafened
    joined_while_deafened = (
        before.channel is None and after.channel is not None and (after.self_deaf or after.deaf)
    )

    # User deafened after being in a channel
    just_deafened = (
        (not before.self_deaf and after.self_deaf) or (not before.deaf and after.deaf)
    )

    # User undeafened
    just_undeafened = (
        (before.self_deaf and not after.self_deaf) or (before.deaf and not after.deaf)
    )

    target = get_deafened_channel(member.guild)
    if not isinstance(target, discord.VoiceChannel):
        print("No AFK channel found.")
        return

    # ===== moved out of AFK while still deafened =====
    moved_out_while_deafened = (
        before.channel is not None
        and after.channel is not None
        and before.channel.id == target.id
        and after.channel.id != target.id
        and (after.self_deaf or after.deaf)
    )

    if moved_out_while_deafened:
        # Save the channel they were moved to so we can move them back there after undeafen
        previous_channels[member.id] = after.channel.id
        try:
            await member.move_to(target)
            try:
                await member.send(
                    "You are still deafened, so you cannot be outside AFK. "
                    "You were moved back to AFK — please undeafen to join voice channels."
                )
            except discord.Forbidden:
                # can't DM them, ignore
                pass
        except Exception as e:
            print(f"Move failed (moved-out-while-deafened): {e}")
        return

    # ===== Joined while deafened =====
    if joined_while_deafened:
        # record the channel they attempted to join so we can send them there after undeafen
        previous_channels[member.id] = after.channel.id
        if after.channel.id != target.id:
            try:
                await member.move_to(target)
                try:
                    await member.send(
                        "You have been automatically moved to AFK. Please undeafen before joining a voice room. Doing so now will automatically bring you to the voice room you tried to enter."
                    )
                except discord.Forbidden:
                    pass
            except Exception as e:
                print(f"Move failed (join-deafened): {e}")
        return

    # ===== Just deafened =====
    if just_deafened:
        if after.channel is None:
            return
        # save the channel they were in so they can be returned there after undeafen
        previous_channels[member.id] = after.channel.id
        if after.channel.id != target.id:
            try:
                await member.move_to(target)
            except Exception as e:
                print(f"Move failed (deafened): {e}")
        return

    # ===== Just undeafened (move back) =====
    if just_undeafened:
        original_id = previous_channels.pop(member.id, None)
        if original_id is None:
            return
        # only move back if they're currently in AFK (we moved them there earlier)
        if after.channel is None or after.channel.id != target.id:
            return
        original = member.guild.get_channel(original_id)
        if isinstance(original, discord.VoiceChannel):
            try:
                await member.move_to(original)
            except Exception as e:
                print(f"Move back failed: {e}")


if __name__ == "__main__":
    if not BOT_TOKEN:
        raise RuntimeError("You must set DISCORD_TOKEN")
    client.run(BOT_TOKEN)
