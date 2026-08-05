import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# --- CONFIGURATION CONSTANTS ---
CATEGORY_ID = 1522626376161558538
PAID_AD_CATEGORY_ID = 1525507984950558810 # Your designated Paid Ad category
LOG_CHANNEL_ID = 1522652867587080363       # Your exact logging channel ID
FLIGHT_BLACKLIST_LOG_CHANNEL_ID = 1522653117680980099
BLACKLIST_ROLE_ID = 1534613908201930832
PROOF_ALLOWED_ROLE_ID = 1522615900904230932
RYANAIR_BLUE = discord.Color.from_rgb(0, 53, 146)  # Official Ryanair Blue Hex #003592
PANEL_ALLOWED_ROLE_ID = 1522589316109566094        # Only this role can use /sendticketpanel

# Role Lists
STAFF_GENERAL_PARTNER = [1522599274712666172, 1522606600823640256, 1522615792716222554]
STAFF_FLIGHT_OPS = [1522599274712666172, 1522606600823640256, 1522615900904230932]
STAFF_MARKETING = [1522599274712666172, 1522606600823640256, 1522616172548198662]

# Explicit restriction lists for your new commands
BOD_ALLOWED_ROLES = [1522599274712666172, 1522606600823640256]

ALL_STAFF_ROLES = list(set(STAFF_GENERAL_PARTNER + STAFF_FLIGHT_OPS + STAFF_MARKETING))

# Emojis
EMOJI_GENERAL = "<:RY_Information:1522911729560850462>"
EMOJI_PARTNERSHIP = "<:RY_Partnership:1522912936849440828>"
EMOJI_FLIGHT_OPS = "<:RY_Plane:1522960336792195252>"

# Logging Emojis
LOG_EMOJI_TICKET_BY = "<:RY_Members:1522908832823509012>"
LOG_EMOJI_INFO = "<:RY_Info:1522908603168587936>"
LOG_EMOJI_TICKET_NAME = "<:RY_UnderDevelopement:1522908449003012126>"
LOG_EMOJI_CLOSED_BY = "<:RY_Training:1522912390256263258>"

# Provided Image URL
MAIN_PANEL_IMAGE = "https://cdn.discordapp.com/attachments/1522625378466791557/1525503730659623044/content.png?ex=6a539f8f&is=6a524e0f&hm=fe95d31cdae1ea2f2a840cfb6fb862ff999b705df88d7088c6a50cda9245587a"


# --- GLOBAL HELPER FOR SENDING LOGS ---
async def send_ticket_log(bot: commands.Bot, guild: discord.Guild, channel: discord.TextChannel, closed_by: discord.Member):
    """Parses ticket channel metadata and dispatches a log to the logging channel."""
    log_channel = bot.get_channel(LOG_CHANNEL_ID) or await bot.fetch_channel(LOG_CHANNEL_ID)
    if not log_channel:
        print(f"❌ Could not find log channel with ID {LOG_CHANNEL_ID}")
        return

    # Extract Owner ID from the channel topic metadata
    owner_mention = "Unknown User"
    category_name = "Unknown Category"
    
    if channel.topic and "Ticket Owner:" in channel.topic:
        try:
            parts = channel.topic.split(" | ")
            owner_id = int(parts[0].split("Ticket Owner: ")[1])
            category_name = parts[1].split("Category: ")[1]
            owner_mention = f"<@{owner_id}>"
        except Exception:
            pass

    embed = discord.Embed(
        title="✈️ Ryanair Support System • Terminal Archive Log",
        color=RYANAIR_BLUE,
        timestamp=datetime.utcnow()
    )
    embed.set_image(url=MAIN_PANEL_IMAGE)
    embed.set_footer(text="Ryanair Logs • Operations Data Security", icon_url="https://i.imgur.com/8Qj8n8L.png")

    embed.add_field(name=f"{LOG_EMOJI_TICKET_NAME} Ticket Name", value=f"`#{channel.name}`", inline=True)
    embed.add_field(name=f"{LOG_EMOJI_INFO} Division Category", value=f"**{category_name}**", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name=f"{LOG_EMOJI_TICKET_BY} Ticket Opened By", value=owner_mention, inline=True)
    embed.add_field(name=f"{LOG_EMOJI_CLOSED_BY} Closed By", value=closed_by.mention, inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    try:
        await log_channel.send(embed=embed)
    except Exception as e:
        print(f"❌ Failed to send log message: {e}")


# --- IN-TICKET CONTROL PERSISTENT VIEW ---
class TicketControlView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket_btn")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 **Ticket Closed:** Logging data and removing terminal in 3 seconds...", ephemeral=False)
        await send_ticket_log(self.bot, interaction.guild, interaction.channel, interaction.user)
        await asyncio.sleep(3)
        await interaction.channel.delete()


# --- POPUP REASON MODAL ---
class TicketReasonModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, category_name: str, staff_roles: list, ping_roles: list):
        super().__init__(title=f"Open {category_name} Support")
        self.bot = bot
        self.category_name = category_name
        self.staff_roles = staff_roles
        self.ping_roles = ping_roles
        
        self.reason = discord.ui.TextInput(
            label="Reason for support opening",
            style=discord.TextStyle.paragraph,
            placeholder="Please detail your request or flight query here...",
            required=True,
            max_length=500
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)
        
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("❌ Error: The Ryanair ticket category channel could not be found.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
        }
        
        for role_id in self.staff_roles:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)

        channel_name = f"{self.category_name.lower().replace(' ', '-')}-{interaction.user.name}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket Owner: {interaction.user.id} | Category: {self.category_name}"
        )

        ping_mentions = " ".join([f"<@&{r_id}>" for r_id in self.ping_roles])
        
        embed = discord.Embed(
            title="✈️ Ryanair Customer Support Operations",
            description=(
                f"Welcome to your **{self.category_name}** support portal, {interaction.user.mention}.\n\n"
                f"Our assigned ground team has been systematically pinged. Please lay out any additional information below "
                f"so our crew can resolve your query efficiently.\n\n"
                f"**Initial Flight/Inquiry Reason:**\n```\n{self.reason.value}\n```"
            ),
            color=RYANAIR_BLUE
        )
        embed.set_thumbnail(url="https://i.imgur.com/8Qj8n8L.png")
        embed.set_footer(text="Ryanair Operations • Always Care, Always Low Fares", icon_url="https://i.imgur.com/8Qj8n8L.png")

        await ticket_channel.send(content=f"{interaction.user.mention} {ping_mentions}", embed=embed, view=TicketControlView(self.bot))
        await interaction.followup.send(f"✅ Ticket opened successfully! View here: {ticket_channel.mention}", ephemeral=True)


# --- MAIN TICKETING SELECTION HUB PANEL ---
class TicketPanelView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="General Support", style=discord.ButtonStyle.secondary, emoji=EMOJI_GENERAL, custom_id="panel_general")
    async def general_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketReasonModal(self.bot, "General Support", STAFF_GENERAL_PARTNER, [1522615792716222554]))

    @discord.ui.button(label="Partnership Division", style=discord.ButtonStyle.secondary, emoji=EMOJI_PARTNERSHIP, custom_id="panel_partnership")
    async def partnership_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketReasonModal(self.bot, "Partnership", STAFF_GENERAL_PARTNER, [1522615792716222554]))

    @discord.ui.button(label="Flight Operations", style=discord.ButtonStyle.secondary, emoji=EMOJI_FLIGHT_OPS, custom_id="panel_flight_ops")
    async def flight_ops_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketReasonModal(self.bot, "Flight Operations", STAFF_FLIGHT_OPS, [1522615900904230932]))


# --- THE COG CLASS ---
class RyanairSupport(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketPanelView(self.bot))
        self.bot.add_view(TicketControlView(self.bot))
        print("✈️ Ryanair Support: Persistent accessory views registered successfully.")

    # Staff Check Helpers
    def is_staff(self, ctx: commands.Context):
        user_role_ids = [role.id for role in ctx.author.roles]
        return any(r_id in user_role_ids for r_id in ALL_STAFF_ROLES)

    def is_general_or_partner_staff(self, ctx: commands.Context):
        user_role_ids = [role.id for role in ctx.author.roles]
        return any(r_id in user_role_ids for r_id in STAFF_GENERAL_PARTNER)

    def is_bod_staff(self, ctx: commands.Context):
        user_role_ids = [role.id for role in ctx.author.roles]
        return any(r_id in user_role_ids for r_id in BOD_ALLOWED_ROLES)

    def is_staff_interaction(self, interaction: discord.Interaction):
        user_role_ids = [role.id for role in interaction.user.roles]
        return any(r_id in user_role_ids for r_id in ALL_STAFF_ROLES)

    # --- SLASH COMMAND: DEPLOY EMBED PANEL ---
    @app_commands.guilds(discord.Object(id=1522589073741578340))
    @app_commands.command(name="sendticketpanel", description="Sends the custom Ryanair ticket panel message.")
    async def send_ticket_panel(self, interaction: discord.Interaction):
        has_role = any(role.id == PANEL_ALLOWED_ROLE_ID for role in interaction.user.roles)
        if not has_role:
            await interaction.response.send_message("❌ You do not hold the required Ryanair Administration role permissions to deploy this system.", ephemeral=True)
            return

        embed = discord.Embed(
            title="✈️ Ryanair Digital Support Center",
            description=(
                "Welcome to the **Ryanair Support Hub**. Please open an official communication channel "
                "with our administrative staff by choosing the appropriate flight division button below.\n\n"
                f"{EMOJI_GENERAL} **General Support** — General inquiries, scheduling, baggage, and booking changes.\n"
                f"{EMOJI_PARTNERSHIP} **Partnership Division** — Branding queries, commercial relations, and partnership requests.\n"
                f"{EMOJI_FLIGHT_OPS} **Flight Operations** — Route logistics, career assignments, and operations infrastructure.\n\n"
                "⚠️ *Please choose accurately to ensure your terminal goes straight to the correct department.*"
            ),
            color=RYANAIR_BLUE
        )
        embed.set_image(url=MAIN_PANEL_IMAGE)
        embed.set_footer(text="Ryanair Admin Portal • Low Fares. Made Simple.", icon_url="https://i.imgur.com/8Qj8n8L.png")
        
        await interaction.response.send_message("✅ Dispatching customer support matrix...", ephemeral=True)
        await interaction.channel.send(embed=embed, view=TicketPanelView(self.bot))

    @app_commands.guilds(discord.Object(id=1522589073741578340))
    @app_commands.command(name="flightblacklist", description="Create a flight blacklist entry and assign the blacklist role.")
    @app_commands.describe(
        target_user="The user to blacklist",
        reason="Why they are being blacklisted",
        duration="Blacklist duration",
        proof="Attach image proof for the blacklist"
    )
    @app_commands.choices(duration=[
        app_commands.Choice(name="1 week", value="1 week"),
        app_commands.Choice(name="2 weeks", value="2 weeks"),
        app_commands.Choice(name="1 month", value="1 month"),
        app_commands.Choice(name="3 months", value="3 months"),
        app_commands.Choice(name="permanent", value="permanent")
    ])
    async def flightblacklist(
        self,
        interaction: discord.Interaction,
        target_user: discord.Member,
        duration: str,
        reason: str,
        proof: Optional[discord.Attachment] = None
    ):
        if not any(role.id == PROOF_ALLOWED_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message(
                "❌ You need the proper proof management role to use this command.",
                ephemeral=True
            )
            return

        if not proof or not proof.content_type.startswith("image"):
            await interaction.response.send_message(
                "❌ Please attach an image proof when running this command.",
                ephemeral=True
            )
            return

        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command must be used from within the server.",
                ephemeral=True
            )
            return

        now = datetime.utcnow()
        expires_at = None
        if duration == "1 week":
            expires_at = now + timedelta(weeks=1)
        elif duration == "2 weeks":
            expires_at = now + timedelta(weeks=2)
        elif duration == "1 month":
            expires_at = now + timedelta(days=30)
        elif duration == "3 months":
            expires_at = now + timedelta(days=90)

        if expires_at:
            duration_value = f"{duration} — expires <t:{int(expires_at.timestamp())}:F>"
        else:
            duration_value = "permanent"

        embed = discord.Embed(
            description=(
                "## <:RY_Logo:1525996886534783111> | Flight Blacklist\n"
                f"User: {target_user.mention}\n"
                f"Logger: {interaction.user.mention}\n"
                f"Duration: {duration_value}\n"
                f"Reason: {reason}"
            )
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1522625378466791557/1525503730659623044/content.png?ex=6a74950f&is=6a73438f&hm=ca5ccac32a7d401b8270024ab098e19f78cb55732a7966e973d48e9ffdd97150&")

        log_channel = interaction.guild.get_channel(FLIGHT_BLACKLIST_LOG_CHANNEL_ID)
        if not log_channel:
            try:
                log_channel = await self.bot.fetch_channel(FLIGHT_BLACKLIST_LOG_CHANNEL_ID)
            except Exception:
                log_channel = None

        try:
            blacklist_role = interaction.guild.get_role(BLACKLIST_ROLE_ID)
            if blacklist_role:
                await target_user.add_roles(blacklist_role, reason=f"Blacklisted by {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to assign blacklist role: {e}",
                ephemeral=True
            )
            return

        if log_channel:
            await log_channel.send(content=f"{target_user.mention}", embed=embed)
            await interaction.response.send_message(
                f"✅ Blacklist recorded and sent to {log_channel.mention}.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "✅ Blacklist recorded, but could not find the log channel.",
                ephemeral=True
            )


    # --- PREFIX UTILITY CHAT COMMANDS ---
    @app_commands.describe(
        target_user="The user to blacklist",
        logger="The staff member logging the blacklist",
        duration="The blacklist duration"
    )
    @app_commands.choices(duration=[
        app_commands.Choice(name="1 week", value="1 week"),
        app_commands.Choice(name="2 weeks", value="2 weeks"),
        app_commands.Choice(name="1 month", value="1 month"),
        app_commands.Choice(name="permanent", value="permanent")
    ])
    async def blacklist(self, interaction: discord.Interaction, target_user: discord.Member, logger: discord.Member, duration: str):
        if not self.is_staff_interaction(interaction):
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🚫 User Blacklisted",
            description=(
                f"**Blacklisted User:** {target_user.mention}\n"
                f"**Logged By:** {logger.mention}\n"
                f"**Duration:** {duration}\n"
            ),
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Ryanair Enforcement Log")

        await interaction.response.send_message(embed=embed)


    # --- PREFIX UTILITY CHAT COMMANDS ---

    # !bod Command
    @commands.command(name="bod")
    async def bod(self, ctx: commands.Context):
        if not self.is_bod_staff(ctx):
            return

        if not ctx.channel.topic or "Ticket Owner:" not in ctx.channel.topic:
            await ctx.send("❌ This command must be executed within an open ticket channel.")
            return

        guild = ctx.guild
        try:
            owner_id = int(ctx.channel.topic.split("Ticket Owner: ")[1].split(" |")[0])
            owner = guild.get_member(owner_id)
        except:
            await ctx.send("❌ Error fetching metadata tracking for this channel owner.")
            return

        # Explicitly build clean overwrites isolating ONLY the two requested roles
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False)
        }
        
        if owner:
            overwrites[owner] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)

        for role_id in BOD_ALLOWED_ROLES:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)

        await ctx.channel.edit(overwrites=overwrites)
        await ctx.send("🔒 **Board of Directors Override:** Channel permissions updated. This ticket is now visible **only** to the Board of Directors and the ticket owner.")

    # !paidad Command
    @commands.command(name="paidad")
    async def paidad(self, ctx: commands.Context):
        if not self.is_bod_staff(ctx):
            return

        if not ctx.channel.topic or "Ticket Owner:" not in ctx.channel.topic:
            await ctx.send("❌ This command must be executed within an open ticket channel.")
            return

        guild = ctx.guild
        target_category = guild.get_channel(PAID_AD_CATEGORY_ID)
        
        if not target_category or not isinstance(target_category, discord.CategoryChannel):
            await ctx.send("❌ Error: The targeted Paid Advertisement category channel could not be found.")
            return

        try:
            owner_id = int(ctx.channel.topic.split("Ticket Owner: ")[1].split(" |")[0])
            owner = guild.get_member(owner_id)
        except:
            await ctx.send("❌ Error indexing metadata tracking for this channel owner.")
            return

        new_name = f"paid-ad-{owner.name if owner else 'user'}"
        
        try:
            # Shift categories and update the ticket name
            await ctx.channel.edit(category=target_category, name=new_name)
            await ctx.send(f"💸 **Paid Advertisement Conversion:** Channel moved to **{target_category.name}** and renamed to `#{new_name}`.")
        except Exception as e:
            await ctx.send(f"❌ Failed to execute paid advertisement shift: {e}")

    # !rename Command
    @commands.command(name="rename")
    async def rename(self, ctx: commands.Context, *, new_name: str = None):
        if not self.is_staff(ctx):
            return

        if not ctx.channel.topic or "Ticket Owner:" not in ctx.channel.topic:
            await ctx.send("❌ This command must be executed within an open ticket channel.")
            return

        if not new_name:
            await ctx.send("❌ Please provide a new name. Usage: `!rename <name>`")
            return

        sanitized_name = new_name.lower().replace(" ", "-")
        old_name = ctx.channel.name
        
        try:
            await ctx.channel.edit(name=sanitized_name)
            await ctx.send(f"🔄 **Terminal Designation Updated:** Channel renamed from `#{old_name}` to `#{sanitized_name}` by {ctx.author.mention}.")
        except Exception as e:
            await ctx.send(f"❌ Structural rename action failed: {e}")

    # !marketing-app Command
    @commands.command(name="marketing-app")
    async def marketing_app(self, ctx: commands.Context):
        if not self.is_general_or_partner_staff(ctx):
            return

        if not ctx.channel.topic or "Ticket Owner:" not in ctx.channel.topic:
            await ctx.send("❌ This command must be executed within an open ticket channel.")
            return

        try:
            owner_id = int(ctx.channel.topic.split("Ticket Owner: ")[1].split(" |")[0])
        except:
            await ctx.send("❌ Error indexing metadata tracking for this channel owner.")
            return

        guild = ctx.guild
        owner = guild.get_member(owner_id)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False)
        }
        
        if owner:
            overwrites[owner] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
            
        for role_id in STAFF_MARKETING:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)

        new_channel_name = f"marketing-app-{owner.name if owner else 'user'}"
        await ctx.channel.edit(name=new_channel_name, overwrites=overwrites)
        await ctx.send("🔄 **Ticket Type Escalated:** This channel has been successfully converted into a secure **Marketing Application**.")

    # !introduction Command
    @commands.command(name="introduction")
    async def introduction(self, ctx: commands.Context):
        if not self.is_staff(ctx):
            return
        await ctx.message.delete()
        await ctx.send(f"✈️ Hello, my name is **{ctx.author.display_name}** with the **Ryanair Flight Administration & Management Team**. I will be assisting you through this channel today. How can our team help you out?")

    # !done Command
    @commands.command(name="done")
    async def done(self, ctx: commands.Context):
        if not self.is_staff(ctx):
            return
        await ctx.message.delete()
        await ctx.send("👋 Hey there! Is there anything else our crew can help you with today? Please let us know if you have any additional questions or require further support before we conclude this station session!")

    # !inactivity Command
    @commands.command(name="inactivity")
    async def inactivity(self, ctx: commands.Context):
        if not self.is_staff(ctx):
            return
        await ctx.message.delete()
        
        user_mention = "Customer"
        if ctx.channel.topic and "Ticket Owner: " in ctx.channel.topic:
            try:
                owner_id = int(ctx.channel.topic.split("Ticket Owner: ")[1].split(" |")[0])
                user_mention = f"<@{owner_id}>"
            except:
                pass

        await ctx.send(
            f"Hello {user_mention},\n\n"
            f"Just checking in on behalf of Ryanair Terminal Management, as this support communication has been completely inactive for some time. We want to guarantee your flight questions or issues have been fully resolved and that you are not left waiting.\n\n"
            f"If we do not receive a follow-up response from you within the next **24 hours**, this ticket will automatically lock and archive to ensure our support system queues stay clean and operational.\n\n"
            f"If you still need active assistance, simply drop a reply right here and we will be glad duly to jump back in! Otherwise, no action is needed, and the terminal will safely clear out on its own.\n\n"
            f"Thank you for understanding!"
        )

    # !close Command
    @commands.command(name="close")
    async def close(self, ctx: commands.Context):
        if not self.is_staff(ctx):
            return
        await ctx.send("🔒 **Closing Ticket:** Logging data and removing terminal in 3 seconds...")
        await send_ticket_log(self.bot, ctx.guild, ctx.channel, ctx.author)
        await asyncio.sleep(3)
        await ctx.channel.delete()


# --- COG SETUP FUNCTION ---
async def setup(bot: commands.Bot):
    await bot.add_cog(RyanairSupport(bot))