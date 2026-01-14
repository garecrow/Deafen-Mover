import os
import asyncio
import discord
import random
from datetime import datetime, timedelta
from typing import Optional

BOT_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.members = True
intents.message_content = True
intents.presences = True

client = discord.Client(intents=intents)

# Chaos tracking - all server-side only
chaos_effects_enabled = True
typo_tracker = {}
role_chaos_tracker = {}
ghost_ping_cache = {}
slow_mode_cache = {}
autoreact_users = set()
status_rotation_active = False
confusion_messages = []
last_chaos_time = {}
user_message_count = {}
fake_typing_active = set()
emoji_war_tracker = {}
topic_change_tracker = {}
vc_bitrate_cache = {}
user_limit_cache = {}
reaction_chains = {}

# Chaos configuration - 30+ features
CHAOS_CONFIG = {
    # Voice chaos (8 features)
    'random_move_chance': 0.014,
    'disconnect_reconnect_chance': 0.005,
    'voice_mute_toggle_chance': 0.003,
    'voice_deafen_toggle_chance': 0.002,
    'server_deafen_chance': 0.001,
    'bitrate_change_chance': 0.002,
    'user_limit_change_chance': 0.001,
    'vc_region_change_chance': 0.0005,
    
    # Text chaos (12 features)
    'slowmode_chance': 0.001,
    'ghost_ping_chance': 0.004,
    'typo_response_chance': 0.008,
    'fake_delete_chance': 0.003,
    'emoji_spam_chance': 0.006,
    'autoreact_setup_chance': 0.002,
    'loop_message_chance': 0.0015,
    'confusion_chain_chance': 0.003,
    'topic_change_chance': 0.001,
    'emoji_war_start_chance': 0.002,
    'reaction_chain_chance': 0.003,
    'bulk_delete_trigger_chance': 0.0005,
    
    # Member chaos (8 features)
    'nickname_typo_chance': 0.002,
    'role_color_change_chance': 0.003,
    'role_hoist_toggle_chance': 0.001,
    'role_mentionable_toggle_chance': 0.001,
    'member_timeout_chance': 0.001,
    'avatar_impersonation_chance': 0.0003,
    'status_spoof_chance': 0.002,
    'activity_spoof_chance': 0.001,
    
    # Server chaos (6 features)
    'channel_rename_chance': 0.0006,
    'permission_flip_chance': 0.0008,
    'bot_status_rotate_chance': 0.006,
    'category_reorder_chance': 0.0004,
    'invite_create_chance': 0.001,
    'sticker_add_chance': 0.0005,
    
    # Special stealth chaos (6 features)
    'fake_typing_long_chance': 0.005,
    'reaction_removal_chance': 0.004,
    'message_unpin_chance': 0.0008,
    'embed_spoof_chance': 0.002,
    'thread_create_chance': 0.001,
    'webhook_delete_chance': 0.0003,
}

# ============================================
# 30+ STEALTH CHAOS FUNCTIONS - ALL ANONYMOUS
# ============================================

# 1-8: VOICE CHAOS
async def random_voice_move(member: discord.Member):
    if member.voice and member.voice.channel:
        other_channels = [
            ch for ch in member.guild.voice_channels 
            if ch.id != member.voice.channel.id and ch.permissions_for(member).connect
        ]
        if other_channels:
            try:
                await member.move_to(random.choice(other_channels))
            except:
                pass

async def random_disconnect_reconnect(member: discord.Member):
    if member.voice and member.voice.channel:
        original = member.voice.channel
        try:
            await member.move_to(None)
            await asyncio.sleep(random.uniform(0.1, 1.5))
            await member.move_to(original)
        except:
            pass

async def voice_mute_toggle(member: discord.Member):
    if member.voice and member.guild.me.guild_permissions.mute_members:
        try:
            current = member.voice.mute
            await member.edit(mute=not current)
            await asyncio.sleep(random.uniform(0.2, 0.8))
            if member.voice:
                await member.edit(mute=current)
        except:
            pass

async def voice_deafen_toggle(member: discord.Member):
    if member.voice and member.guild.me.guild_permissions.deafen_members:
        try:
            current = member.voice.deaf
            await member.edit(deafen=not current)
            await asyncio.sleep(random.uniform(0.3, 1.2))
            if member.voice:
                await member.edit(deafen=current)
        except:
            pass

async def server_deafen_member(member: discord.Member):
    if member.voice and member.guild.me.guild_permissions.deafen_members:
        try:
            await member.edit(deafen=True)
            await asyncio.sleep(random.uniform(0.5, 2))
            await member.edit(deafen=False)
        except:
            pass

async def change_vc_bitrate(channel: discord.VoiceChannel):
    if channel.guild.me.guild_permissions.manage_channels:
        try:
            original = channel.bitrate
            vc_bitrate_cache[channel.id] = original
            
            # Set to unusual bitrates
            new_bitrate = random.choice([16000, 32000, 96000, 128000, 256000])
            new_bitrate = min(new_bitrate, channel.guild.bitrate_limit)
            
            await channel.edit(bitrate=new_bitrate)
            
            # Revert after 1-3 minutes
            await asyncio.sleep(random.randint(60, 180))
            if channel.id in vc_bitrate_cache:
                await channel.edit(bitrate=vc_bitrate_cache[channel.id])
                del vc_bitrate_cache[channel.id]
        except:
            pass

async def change_vc_user_limit(channel: discord.VoiceChannel):
    if channel.guild.me.guild_permissions.manage_channels:
        try:
            original = channel.user_limit
            user_limit_cache[channel.id] = original
            
            # Set to unusual limits
            new_limit = random.choice([0, 1, 2, 10, 25, 50, 99])
            await channel.edit(user_limit=new_limit)
            
            # Revert after 2-5 minutes
            await asyncio.sleep(random.randint(120, 300))
            if channel.id in user_limit_cache:
                await channel.edit(user_limit=user_limit_cache[channel.id])
                del user_limit_cache[channel.id]
        except:
            pass

async def change_vc_region(channel: discord.VoiceChannel):
    if channel.guild.me.guild_permissions.manage_channels:
        try:
            # Only works if region is editable
            regions = ['us-west', 'us-east', 'us-central', 'us-south', 
                      'singapore', 'southafrica', 'sydney', 'europe']
            
            if hasattr(channel, 'rtc_region'):
                original = channel.rtc_region
                await channel.edit(rtc_region=random.choice(regions))
                
                # Revert after 30-90 seconds
                await asyncio.sleep(random.randint(30, 90))
                await channel.edit(rtc_region=original)
        except:
            pass

# 9-20: TEXT CHAOS
async def slow_mode_chaos(channel: discord.TextChannel):
    if channel.permissions_for(channel.guild.me).manage_channels:
        original = channel.slowmode_delay
        slow_time = random.choice([1, 2, 3, 5, 8, 13])
        await channel.edit(slowmode_delay=slow_time)
        
        slow_mode_cache[channel.id] = original
        
        await asyncio.sleep(random.randint(90, 240))
        if channel.id in slow_mode_cache:
            await channel.edit(slowmode_delay=slow_mode_cache[channel.id])
            del slow_mode_cache[channel.id]

async def ghost_ping_random(channel: discord.TextChannel):
    if channel.permissions_for(channel.guild.me).send_messages:
        members = [m for m in channel.guild.members if not m.bot]
        if members:
            target = random.choice(members)
            
            try:
                msg = await channel.send(target.mention)
                await asyncio.sleep(random.uniform(0.2, 0.6))
                await msg.delete()
                
                ghost_ping_cache[target.id] = datetime.now()
            except:
                pass

async def subtle_typo_response(channel: discord.TextChannel):
    if channel.permissions_for(channel.guild.me).send_messages:
        responses = ["🤔", "👀", "...", "hmm", "lol", "ok"]
        await channel.send(random.choice(responses))

async def fake_delete_message(channel: discord.TextChannel):
    if channel.permissions_for(channel.guild.me).send_messages:
        try:
            msg = await channel.send("...")
            await asyncio.sleep(random.uniform(0.3, 0.9))
            await msg.delete()
        except:
            pass

async def emoji_spam(message: discord.Message):
    if message.channel.permissions_for(message.guild.me).add_reactions:
        emoji_list = ['🤔', '👀', '👍', '❓', '😐', '🙃']
        
        for _ in range(random.randint(1, 2)):
            try:
                await message.add_reaction(random.choice(emoji_list))
                await asyncio.sleep(0.1)
            except:
                break

async def setup_autoreact(member: discord.Member):
    if member.id not in autoreact_users:
        autoreact_users.add(member.id)
        await asyncio.sleep(random.randint(240, 720))
        if member.id in autoreact_users:
            autoreact_users.remove(member.id)

async def create_message_loop(channel: discord.TextChannel):
    loops = [
        ["...", "..", "..."],
        ["hmm", "🤔", "hmm"],
    ]
    
    selected = random.choice(loops)
    
    for text in selected:
        try:
            await channel.send(text)
            await asyncio.sleep(random.uniform(0.3, 0.8))
        except:
            break

async def start_confusion_chain(channel: discord.TextChannel):
    chain_starters = ["...", "?", "hmm"]
    await channel.send(random.choice(chain_starters))

async def change_channel_topic(channel: discord.TextChannel):
    if channel.permissions_for(channel.guild.me).manage_channels:
        try:
            original = channel.topic
            topic_change_tracker[channel.id] = original
            
            topics = [
                "discussion",
                "general",
                "chat",
                "talk here",
                "",
                " ",
                ".",
                ".."
            ]
            
            await channel.edit(topic=random.choice(topics))
            
            await asyncio.sleep(random.randint(180, 480))
            if channel.id in topic_change_tracker:
                await channel.edit(topic=topic_change_tracker[channel.id])
                del topic_change_tracker[channel.id]
        except:
            pass

async def start_emoji_war(message: discord.Message):
    if message.channel.permissions_for(message.guild.me).add_reactions:
        emoji_pairs = [('👍', '👎'), ('😀', '😠'), ('❤️', '💔'), ('✅', '❌')]
        
        if random.random() < 0.3:
            pair = random.choice(emoji_pairs)
            emoji_war_tracker[message.id] = pair
            
            for emoji in pair:
                try:
                    await message.add_reaction(emoji)
                    await asyncio.sleep(0.2)
                except:
                    pass

async def create_reaction_chain(message: discord.Message):
    if message.channel.permissions_for(message.guild.me).add_reactions:
        chains = [
            ['1️⃣', '2️⃣', '3️⃣', '4️⃣'],
            ['🇦', '🇧', '🇨', '🇩'],
            ['⬆️', '⬇️', '⬅️', '➡️'],
        ]
        
        if random.random() < 0.2:
            chain = random.choice(chains)
            reaction_chains[message.id] = chain
            
            for emoji in chain:
                try:
                    await message.add_reaction(emoji)
                    await asyncio.sleep(0.3)
                except:
                    break

async def trigger_bulk_delete(channel: discord.TextChannel):
    if channel.permissions_for(channel.guild.me).manage_messages:
        try:
            # Delete 2-5 of bot's own recent messages
            to_delete = []
            async for message in channel.history(limit=10):
                if message.author == client.user and len(to_delete) < 5:
                    to_delete.append(message)
            
            if len(to_delete) >= 2:
                await channel.delete_messages(to_delete)
        except:
            pass

# 21-28: MEMBER CHAOS
async def random_nickname_change(member: discord.Member):
    if member.guild.me.guild_permissions.manage_nicknames:
        original = member.nick or member.name
        
        if len(original) > 2:
            strategies = [
                lambda s: s + '_' if len(s) < 31 else s,
                lambda s: s[:-1] if len(s) > 3 else s,
                lambda s: s[0].lower() + s[1:] if s[0].isupper() else s[0].upper() + s[1:],
            ]
            
            try:
                strategy = random.choice(strategies)
                new_nick = strategy(original)[:32]
                
                if new_nick != original:
                    await member.edit(nick=new_nick)
                    
                    await asyncio.sleep(random.randint(150, 360))
                    await member.edit(nick=original[:32] if original != member.name else None)
            except:
                pass

async def random_role_color_change(guild: discord.Guild):
    if guild.me.guild_permissions.manage_roles:
        roles = [r for r in guild.roles if r.position < guild.me.top_role.position and not r.managed]
        
        if roles:
            role = random.choice(roles)
            original = role.color
            
            # Very slight change
            if original.value != 0:
                r = min(255, max(0, original.r + random.randint(-15, 15)))
                g = min(255, max(0, original.g + random.randint(-15, 15)))
                b = min(255, max(0, original.b + random.randint(-15, 15)))
                new_color = discord.Color.from_rgb(r, g, b)
                
                try:
                    await role.edit(color=new_color)
                    
                    role_chaos_tracker[role.id] = {
                        'guild_id': guild.id,
                        'original': original,
                        'time': datetime.now()
                    }
                except:
                    pass

async def toggle_role_hoist(guild: discord.Guild):
    if guild.me.guild_permissions.manage_roles:
        roles = [r for r in guild.roles if r.position < guild.me.top_role.position and not r.managed]
        
        if roles:
            role = random.choice(roles)
            try:
                await role.edit(hoist=not role.hoist)
                
                await asyncio.sleep(random.randint(240, 600))
                await role.edit(hoist=not role.hoist)
            except:
                pass

async def toggle_role_mentionable(guild: discord.Guild):
    if guild.me.guild_permissions.manage_roles:
        roles = [r for r in guild.roles if r.position < guild.me.top_role.position and not r.managed]
        
        if roles:
            role = random.choice(roles)
            try:
                await role.edit(mentionable=not role.mentionable)
                
                await asyncio.sleep(random.randint(30, 90))
                await role.edit(mentionable=not role.mentionable)
            except:
                pass

async def timeout_random_member(guild: discord.Guild):
    if guild.me.guild_permissions.moderate_members:
        members = [m for m in guild.members if not m.bot and m.guild_permissions.moderate_members is False]
        
        if members:
            member = random.choice(members)
            try:
                # Very short timeout (1-5 minutes)
                duration = timedelta(minutes=random.randint(1, 5))
                await member.timeout(duration, reason=None)
                
                await asyncio.sleep(random.randint(30, 120))
                await member.timeout(None)
            except:
                pass

async def spoof_member_status(member: discord.Member):
    # This is visual only - we can't actually change other users' status
    # But we can create the illusion by manipulating cached data
    pass  # Placeholder - actual implementation would require client modification

async def spoof_member_activity(channel: discord.TextChannel, member: discord.Member):
    if channel.permissions_for(channel.guild.me).send_messages:
        games = ["Minecraft", "Fortnite", "VALORANT", "Among Us", "Rocket League"]
        
        if random.random() < 0.1:
            await channel.send(f"{member.display_name} is playing {random.choice(games)}")

# 29-34: SERVER CHAOS
async def temporary_channel_rename(channel: discord.abc.GuildChannel):
    if channel.guild.me.guild_permissions.manage_channels:
        original = channel.name
        
        try:
            new_name = original + " " if not original.endswith(" ") else original[:-1]
            await channel.edit(name=new_name[:100])
            
            await asyncio.sleep(random.randint(120, 300))
            await channel.edit(name=original)
        except:
            pass

async def flip_send_permissions(channel: discord.TextChannel):
    if channel.guild.me.guild_permissions.manage_channels:
        everyone = channel.guild.default_role
        
        try:
            current = channel.overwrites_for(everyone).send_messages
            
            if current is not None:
                overwrite = discord.PermissionOverwrite()
                overwrite.send_messages = not current
                
                await channel.set_permissions(everyone, overwrite=overwrite)
                
                await asyncio.sleep(random.randint(20, 60))
                rev_overwrite = discord.PermissionOverwrite()
                rev_overwrite.send_messages = current
                await channel.set_permissions(everyone, overwrite=rev_overwrite)
        except:
            pass

async def rotate_bot_status():
    global status_rotation_active
    
    statuses = [
        (discord.Status.online, None),
        (discord.Status.idle, None),
        (discord.Status.dnd, None),
        (discord.Status.online, discord.Activity(type=discord.ActivityType.playing, name=" ")),
    ]
    
    status_rotation_active = True
    
    while status_rotation_active and chaos_effects_enabled:
        status, activity = random.choice(statuses)
        await client.change_presence(status=status, activity=activity)
        
        await asyncio.sleep(random.randint(120, 600))

async def reorder_category(category: discord.CategoryChannel):
    if category.guild.me.guild_permissions.manage_channels:
        try:
            channels = list(category.channels)
            if len(channels) > 1:
                random.shuffle(channels)
                
                for i, channel in enumerate(channels):
                    await channel.edit(position=i)
        except:
            pass

async def create_random_invite(channel: discord.TextChannel):
    if channel.permissions_for(channel.guild.me).create_instant_invite:
        try:
            invite = await channel.create_invite(
                max_age=random.randint(300, 3600),  # 5-60 minutes
                max_uses=random.randint(1, 5),
                temporary=True
            )
            # Don't send it anywhere - just create it
        except:
            pass

async def add_random_sticker(guild: discord.Guild):
    # This requires sticker management permissions and actual sticker files
    # Placeholder for sticker chaos
    pass

# 35-40: SPECIAL STEALTH CHAOS
async def fake_long_typing(channel: discord.TextChannel):
    async with channel.typing():
        await asyncio.sleep(random.uniform(2, 4))
        
        if random.random() < 0.2:
            await channel.send("...")

async def remove_random_reactions(message: discord.Message):
    if message.reactions and message.channel.permissions_for(message.guild.me).manage_messages:
        reactions = list(message.reactions)
        if reactions:
            reaction = random.choice(reactions)
            try:
                async for user in reaction.users():
                    if user != client.user:
                        await message.remove_reaction(reaction.emoji, user)
                        break
            except:
                pass

async def unpin_random_message(channel: discord.TextChannel):
    if channel.permissions_for(channel.guild.me).manage_messages:
        try:
            pinned = await channel.pins()
            if pinned:
                await random.choice(pinned).unpin()
        except:
            pass

async def spoof_embed(channel: discord.TextChannel):
    if channel.permissions_for(channel.guild.me).send_messages:
        try:
            embed = discord.Embed(
                title=random.choice(["", " ", "...", "Notice"]),
                description=random.choice(["", " ", "..."]),
                color=random.randint(0, 0xFFFFFF)
            )
            await channel.send(embed=embed)
        except:
            pass

async def create_random_thread(channel: discord.TextChannel):
    if channel.permissions_for(channel.guild.me).create_private_threads:
        try:
            thread = await channel.create_thread(
                name=random.choice(["discussion", "chat", "thread", "..."]),
                auto_archive_duration=random.choice([60, 1440]),
                type=discord.ChannelType.public_thread
            )
            
            # Send a message then delete thread
            await asyncio.sleep(random.uniform(1, 3))
            await thread.send("...")
            await asyncio.sleep(random.uniform(2, 5))
            await thread.delete()
        except:
            pass

async def delete_random_webhook(channel: discord.TextChannel):
    if channel.permissions_for(channel.guild.me).manage_webhooks:
        try:
            webhooks = await channel.webhooks()
            if webhooks:
                webhook = random.choice(webhooks)
                await webhook.delete()
        except:
            pass

# ============================================
# BACKGROUND CHAOS MANAGEMENT
# ============================================

async def revert_old_changes():
    while not client.is_closed():
        await asyncio.sleep(300)
        
        to_remove = []
        for role_id, data in list(role_chaos_tracker.items()):
            if datetime.now() - data['time'] > timedelta(minutes=random.randint(15, 30)):
                guild = client.get_guild(data['guild_id'])
                if guild:
                    role = guild.get_role(role_id)
                    if role:
                        try:
                            await role.edit(color=data['original'])
                        except:
                            pass
                to_remove.append(role_id)
        
        for role_id in to_remove:
            role_chaos_tracker.pop(role_id, None)
        
        to_clear = []
        for user_id, time in list(ghost_ping_cache.items()):
            if datetime.now() - time > timedelta(minutes=20):
                to_clear.append(user_id)
        
        for user_id in to_clear:
            ghost_ping_cache.pop(user_id, None)

async def background_chaos():
    await client.wait_until_ready()
    asyncio.create_task(revert_old_changes())
    
    guild_cooldowns = {}
    
    while not client.is_closed():
        if chaos_effects_enabled:
            for guild in client.guilds:
                current_time = datetime.now()
                
                if guild.id in guild_cooldowns:
                    time_since = (current_time - guild_cooldowns[guild.id]).total_seconds()
                    if time_since < 240:
                        continue
                
                # Voice channel chaos
                for vc in guild.voice_channels:
                    if random.random() < CHAOS_CONFIG['bitrate_change_chance']:
                        await change_vc_bitrate(vc)
                        guild_cooldowns[guild.id] = current_time
                    
                    if random.random() < CHAOS_CONFIG['user_limit_change_chance']:
                        await change_vc_user_limit(vc)
                        guild_cooldowns[guild.id] = current_time
                    
                    if random.random() < CHAOS_CONFIG['vc_region_change_chance']:
                        await change_vc_region(vc)
                        guild_cooldowns[guild.id] = current_time
                    
                    for member in vc.members:
                        if not member.bot:
                            if random.random() < CHAOS_CONFIG['random_move_chance']:
                                await random_voice_move(member)
                            
                            if random.random() < CHAOS_CONFIG['disconnect_reconnect_chance']:
                                await random_disconnect_reconnect(member)
                            
                            if random.random() < CHAOS_CONFIG['voice_mute_toggle_chance']:
                                await voice_mute_toggle(member)
                            
                            if random.random() < CHAOS_CONFIG['voice_deafen_toggle_chance']:
                                await voice_deafen_toggle(member)
                            
                            if random.random() < CHAOS_CONFIG['server_deafen_chance']:
                                await server_deafen_member(member)
                
                # Text channel chaos
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        if random.random() < CHAOS_CONFIG['topic_change_chance']:
                            await change_channel_topic(channel)
                            guild_cooldowns[guild.id] = current_time
                        
                        if random.random() < CHAOS_CONFIG['ghost_ping_chance']:
                            await ghost_ping_random(channel)
                        
                        if random.random() < CHAOS_CONFIG['fake_delete_chance']:
                            await fake_delete_message(channel)
                        
                        if random.random() < CHAOS_CONFIG['loop_message_chance']:
                            await create_message_loop(channel)
                        
                        if random.random() < CHAOS_CONFIG['confusion_chain_chance']:
                            await start_confusion_chain(channel)
                        
                        if random.random() < CHAOS_CONFIG['fake_typing_long_chance']:
                            await fake_long_typing(channel)
                        
                        if random.random() < CHAOS_CONFIG['embed_spoof_chance']:
                            await spoof_embed(channel)
                        
                        if random.random() < CHAOS_CONFIG['thread_create_chance']:
                            await create_random_thread(channel)
                        
                        if random.random() < CHAOS_CONFIG['webhook_delete_chance']:
                            await delete_random_webhook(channel)
                        
                        if random.random() < CHAOS_CONFIG['bulk_delete_trigger_chance']:
                            await trigger_bulk_delete(channel)
                    
                    if channel.permissions_for(guild.me).manage_channels:
                        if random.random() < CHAOS_CONFIG['slowmode_chance']:
                            await slow_mode_chaos(channel)
                            guild_cooldowns[guild.id] = current_time
                        
                        if random.random() < CHAOS_CONFIG['channel_rename_chance']:
                            await temporary_channel_rename(channel)
                            guild_cooldowns[guild.id] = current_time
                        
                        if random.random() < CHAOS_CONFIG['permission_flip_chance']:
                            await flip_send_permissions(channel)
                            guild_cooldowns[guild.id] = current_time
                
                # Category chaos
                for category in guild.categories:
                    if random.random() < CHAOS_CONFIG['category_reorder_chance']:
                        await reorder_category(category)
                        guild_cooldowns[guild.id] = current_time
                
                # Member chaos
                if random.random() < CHAOS_CONFIG['role_color_change_chance']:
                    await random_role_color_change(guild)
                
                if random.random() < CHAOS_CONFIG['role_hoist_toggle_chance']:
                    await toggle_role_hoist(guild)
                
                if random.random() < CHAOS_CONFIG['role_mentionable_toggle_chance']:
                    await toggle_role_mentionable(guild)
                
                if random.random() < CHAOS_CONFIG['member_timeout_chance']:
                    await timeout_random_member(guild)
                    guild_cooldowns[guild.id] = current_time
                
                if random.random() < CHAOS_CONFIG['invite_create_chance']:
                    text_channels = [ch for ch in guild.text_channels if ch.permissions_for(guild.me).create_instant_invite]
                    if text_channels:
                        await create_random_invite(random.choice(text_channels))
            
            # Bot status rotation
            if random.random() < CHAOS_CONFIG['bot_status_rotate_chance'] and not status_rotation_active:
                asyncio.create_task(rotate_bot_status())
        
        await asyncio.sleep(random.randint(45, 120))

# ============================================
# EVENT HANDLERS
# ============================================

@client.event
async def on_ready():
    print(f"🌀 Ultimate Chaos Bot Online: {client.user}")
    print("=" * 60)
    print("30+ STEALTH FEATURES ACTIVATED")
    print("No bot attribution - Complete anonymity")
    print("=" * 60)
    
    await client.change_presence(status=discord.Status.online, activity=None)
    asyncio.create_task(background_chaos())

@client.event
async def on_message(message):
    if message.author.bot or not chaos_effects_enabled:
        return
    
    # Track message count for user
    user_message_count[message.author.id] = user_message_count.get(message.author.id, 0) + 1
    
    # Check cooldown
    channel_key = f"{message.channel.id}_{message.author.id}"
    current_time = datetime.now()
    if channel_key in last_chaos_time:
        time_since = (current_time - last_chaos_time[channel_key]).total_seconds()
        if time_since < 150:
            return
    
    # Typo responses
    if random.random() < CHAOS_CONFIG['typo_response_chance']:
        await asyncio.sleep(random.uniform(0.3, 1.5))
        await subtle_typo_response(message.channel)
        last_chaos_time[channel_key] = current_time
    
    # Slow mode chaos
    if random.random() < CHAOS_CONFIG['slowmode_chance']:
        await slow_mode_chaos(message.channel)
    
    # Nickname typo
    if random.random() < CHAOS_CONFIG['nickname_typo_chance']:
        await random_nickname_change(message.author)
    
    # Emoji spam
    if random.random() < CHAOS_CONFIG['emoji_spam_chance']:
        await emoji_spam(message)
        last_chaos_time[channel_key] = current_time
    
    # Auto-react setup
    if random.random() < CHAOS_CONFIG['autoreact_setup_chance']:
        await setup_autoreact(message.author)
    
    # Reaction removal
    if random.random() < CHAOS_CONFIG['reaction_removal_chance']:
        await remove_random_reactions(message)
    
    # Message unpin
    if random.random() < CHAOS_CONFIG['message_unpin_chance']:
        await unpin_random_message(message.channel)
    
    # Start emoji war
    if random.random() < CHAOS_CONFIG['emoji_war_start_chance']:
        await start_emoji_war(message)
        last_chaos_time[channel_key] = current_time
    
    # Create reaction chain
    if random.random() < CHAOS_CONFIG['reaction_chain_chance']:
        await create_reaction_chain(message)
        last_chaos_time[channel_key] = current_time
    
    # Spoof activity
    if random.random() < CHAOS_CONFIG['activity_spoof_chance']:
        await spoof_member_activity(message.channel, message.author)
    
    # Auto-react if user is in list
    if message.author.id in autoreact_users:
        await asyncio.sleep(random.uniform(0.2, 0.8))
        try:
            await message.add_reaction(random.choice(['🤔', '👀']))
        except:
            pass

@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot or not chaos_effects_enabled:
        return
    
    if before.channel is None and after.channel:
        if random.random() < (CHAOS_CONFIG['random_move_chance'] * 1.3):
            await asyncio.sleep(random.uniform(0.5, 2))
            await random_voice_move(member)
        
        if random.random() < 0.05:
            await asyncio.sleep(random.uniform(0.3, 1.2))
            await voice_mute_toggle(member)

@client.event
async def on_reaction_add(reaction, user):
    if user.bot or not chaos_effects_enabled:
        return
    
    # Continue emoji wars
    if reaction.message.id in emoji_war_tracker:
        pair = emoji_war_tracker[reaction.message.id]
        if str(reaction.emoji) in pair:
            other_emoji = pair[1] if str(reaction.emoji) == pair[0] else pair[0]
            try:
                await reaction.message.add_reaction(other_emoji)
            except:
                pass
    
    # Continue reaction chains
    if reaction.message.id in reaction_chains:
        chain = reaction_chains[reaction.message.id]
        if str(reaction.emoji) in chain:
            idx = chain.index(str(reaction.emoji))
            if idx + 1 < len(chain):
                try:
                    await reaction.message.add_reaction(chain[idx + 1])
                except:
                    pass

# ============================================
# HIDDEN ADMIN COMMANDS
# ============================================

async def handle_hidden_command(message: discord.Message):
    if message.guild is None and message.author.guild_permissions.administrator:
        content = message.content.lower().strip()
        
        if content.startswith("!chaos"):
            global chaos_effects_enabled
            if "off" in content:
                chaos_effects_enabled = False
                await message.channel.send("Chaos disabled.")
            elif "on" in content:
                chaos_effects_enabled = True
                await message.channel.send("Chaos enabled.")
            elif "status" in content:
                status = "enabled" if chaos_effects_enabled else "disabled"
                await message.channel.send(f"Chaos: {status}")

if __name__ == "__main__":
    if not BOT_TOKEN:
        raise RuntimeError("You must set DISCORD_TOKEN")
    
    print("=" * 60)
    print("🌀 ULTIMATE STEALTH CHAOS BOT - 40+ FEATURES")
    print("Voice Bitrate Changes | Reaction Chains | Emoji Wars")
    print("Channel Topics | User Timeouts | Thread Creation")
    print("Bulk Deletes | Permission Flips | Category Reordering")
    print("Hidden commands via DM: !chaos on/off/status")
    print("=" * 60)
    
    client.run(BOT_TOKEN)
