import discord
from discord import app_commands
from discord.ext import commands

# --- CONFIGURATION CONSTANTS ---
RYANAIR_BLUE = discord.Color.from_rgb(0, 53, 146)  # Official Corporate Ryanair Blue
CAREERS_ADMIN_ROLE_ID = 1522599274712666172        # Strict access role ID required for commands
GUILD_ID = 1522589073741578340                     # Your Server Guild ID

# Global Image Asset
MAIN_PANEL_IMAGE = "https://cdn.discordapp.com/attachments/1522625378466791557/1525503730659623044/content.png?ex=6a539f8f&is=6a524e0f&hm=fe95d31cdae1ea2f2a840cfb6fb862ff999b705df88d7088c6a50cda9245587a"


# --- DYNAMIC RECRUITMENT INTERFACE GENERATOR ---
def generate_recruitment_panels(status_dict: dict):
    """Generates two embeds and corresponding views based on the recruitment status matrix matching the layout criteria."""
    
    # ---------------------------------------------------------
    # PANEL 1: MAIN CREW CAREERS
    # ---------------------------------------------------------
    careers_embed = discord.Embed(
        title=" ",
        description=(
            "# Careers\n\n"
            "> At Ryanair, efficiency, safety, and operational superiority drive our workforce strategy. "
            "We strive to create a healthy and rewarding work environment for our employees. Our global network "
            "demands high-performance standards, absolute punctuality, and an unwavering commitment to procedural "
            "excellence across all flight operational routes.\n\n"
            "> We thrive on change and trust our people to help us achieve our mission, celebrating each "
            "other's successes and inspiring one another when things are harder than normal. At Ryanair, "
            "we don't just care about our customers, we care about each other too. Joining our flight crew means "
            "entering a fast-paced environment where logistics and hospitality blend seamlessly.\n\n"
            "> If a position you're interested in is currently unavailable, we encourage you to stay connected and "
            "watch for future openings through our corporate communications channels. New training slots and flight deck "
            "assignments open systematically based on seasonal route updates and global network infrastructure expansion plans.\n\n"
            "### Pilot Applications\n"
            "Take command of modern aircraft and lead the way in delivering exceptional flight experiences.\n\n"
            "### Cabin Crew Applications\n"
            "Provide comfort and safety to passengers while upholding professionalism and hospitality.\n\n"
            "### Ground Crew Applications\n"
            "Support vital operations that keep our airline running — from logistics to event coordination."
        ),
        color=RYANAIR_BLUE
    )
    careers_embed.set_image(url=MAIN_PANEL_IMAGE)
    
    careers_view = discord.ui.View()
    
    # Pilot Button
    p_open = status_dict['pilot'] == 'open'
    careers_view.add_item(discord.ui.Button(
        label="Pilot Applications" if p_open else "Pilot Applications (Unavailable)", 
        style=discord.ButtonStyle.link if p_open else discord.ButtonStyle.secondary, 
        url="https://www.youtube.com" if p_open else None, 
        disabled=not p_open
    ))
    
    # Cabin Crew Button
    c_open = status_dict['cabin'] == 'open'
    careers_view.add_item(discord.ui.Button(
        label="Cabin Crew Applications" if c_open else "Cabin Crew Applications (Unavailable)", 
        style=discord.ButtonStyle.link if c_open else discord.ButtonStyle.secondary, 
        url="https://www.youtube.com" if c_open else None, 
        disabled=not c_open
    ))
    
    # Ground Crew Button
    g_open = status_dict['ground'] == 'open'
    careers_view.add_item(discord.ui.Button(
        label="Ground Crew Applications" if g_open else "Ground Crew Applications (Unavailable)", 
        style=discord.ButtonStyle.link if g_open else discord.ButtonStyle.secondary, 
        url="https://www.youtube.com" if g_open else None, 
        disabled=not g_open
    ))

    # ---------------------------------------------------------
    # PANEL 2: MANAGEMENT & ADMINISTRATION
    # ---------------------------------------------------------
    mgmt_embed = discord.Embed(
        title=" ",
        description=(
            "# Management Team\n\n"
            "> The backbone of corporate operations demands meticulous planners, system architects, and strategic analysts. "
            "Our administrative sectors work tirelessly behind the scenes to streamline communications, coordinate crew "
            "schedules, audit protocol logs, and manage network expansions. These positions require seasoned leadership, "
            "impeccable problem-solving faculties, and complete professional dedication to the Ryanair operations matrix.\n\n"
            "### Flight Operations\n"
            "Coordinate flights, organise exciting events, and ensure smooth operations across Ryanair's network!\n\n"
            "### Human Resources\n"
            "Manage employee applications, support tickets and support Ryanair as a moderator!\n\n"
            "### Marketing Division\n"
            "Develop branding vectors, oversee commercial relations, and manage network expansions."
        ),
        color=RYANAIR_BLUE
    )
    mgmt_embed.set_footer(text="Ryanair Recruitment Portal • Low Fares. Made Simple.", icon_url="https://i.imgur.com/8Qj8n8L.png")
    
    mgmt_view = discord.ui.View()
    
    # Flight Operations Button
    f_open = status_dict['flight_ops'] == 'open'
    mgmt_view.add_item(discord.ui.Button(
        label="Flight Operations" if f_open else "Flight Operations (Unavailable)", 
        style=discord.ButtonStyle.link if f_open else discord.ButtonStyle.secondary, 
        url="https://www.youtube.com" if f_open else None, 
        disabled=not f_open
    ))
    
    # Human Resources Button
    hr_open = status_dict['hr'] == 'open'
    mgmt_view.add_item(discord.ui.Button(
        label="Human Resources" if hr_open else "Human Resources (Unavailable)", 
        style=discord.ButtonStyle.link if hr_open else discord.ButtonStyle.secondary, 
        url="https://www.youtube.com" if hr_open else None, 
        disabled=not hr_open
    ))

    # Marketing Division Button (Routes directly to your chosen discord target link channel path)
    mkt_open = status_dict['marketing'] == 'open'
    mgmt_view.add_item(discord.ui.Button(
        label="Marketing Division" if mkt_open else "Marketing Division (Unavailable)", 
        style=discord.ButtonStyle.link if mkt_open else discord.ButtonStyle.secondary, 
        url="https://discord.com/channels/@me/1525500488420950066" if mkt_open else None, 
        disabled=not mkt_open
    ))

    return careers_embed, careers_view, mgmt_embed, mgmt_view


# --- THE COG CLASS ---
class RyanairCareers(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Core data tracking for application states
        self.app_states = {
            "pilot": "closed",
            "cabin": "closed",
            "ground": "closed",
            "flight_ops": "closed",
            "hr": "closed",
            "marketing": "closed"
        }

    # Helper verification to enforce strict administrative role barriers
    def check_careers_admin(self, interaction: discord.Interaction) -> bool:
        return any(role.id == CAREERS_ADMIN_ROLE_ID for role in interaction.user.roles)


    # --- SLASH COMMANDS: CAREERS SECTOR SYSTEM ---

    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="sendcareers", description="Deploys the customized Ryanair career hub panel layout.")
    async def send_careers(self, interaction: discord.Interaction):
        if not self.check_careers_admin(interaction):
            await interaction.response.send_message("❌ Access Denied: Requires Ryanair Management credentials.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        c_embed, c_view, m_embed, m_view = generate_recruitment_panels(self.app_states)
        
        await interaction.channel.send(embed=c_embed, view=c_view)
        await interaction.channel.send(embed=m_embed, view=m_view)
        await interaction.followup.send("✅ Career layouts matched and dispatched successfully.", ephemeral=True)


    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="openapp", description="Opens a recruitment sector interface option.")
    @app_commands.choices(sector=[
        app_commands.Choice(name="Pilot Sector", value="pilot"),
        app_commands.Choice(name="Cabin Crew Sector", value="cabin"),
        app_commands.Choice(name="Ground Crew Sector", value="ground"),
        app_commands.Choice(name="Flight Operations Leadership", value="flight_ops"),
        app_commands.Choice(name="Human Resources Sector", value="hr"),
        app_commands.Choice(name="Marketing Division", value="marketing")
    ])
    async def open_app(self, interaction: discord.Interaction, sector: str):
        if not self.check_careers_admin(interaction):
            await interaction.response.send_message("❌ Access Denied: Requires Ryanair Management credentials.", ephemeral=True)
            return

        self.app_states[sector] = "open"
        await interaction.response.send_message(f"✅ Sector `{sector}` status changed to OPEN. Run /sendcareers to deploy updated layout vectors.", ephemeral=True)


    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="closeapp", description="Closes a recruitment sector interface option.")
    @app_commands.choices(sector=[
        app_commands.Choice(name="Pilot Sector", value="pilot"),
        app_commands.Choice(name="Cabin Crew Sector", value="cabin"),
        app_commands.Choice(name="Ground Crew Sector", value="ground"),
        app_commands.Choice(name="Flight Operations Leadership", value="flight_ops"),
        app_commands.Choice(name="Human Resources Sector", value="hr"),
        app_commands.Choice(name="Marketing Division", value="marketing")
    ])
    async def close_app(self, interaction: discord.Interaction, sector: str):
        if not self.check_careers_admin(interaction):
            await interaction.response.send_message("❌ Access Denied: Requires Ryanair Management credentials.", ephemeral=True)
            return

        self.app_states[sector] = "closed"
        await interaction.response.send_message(f"🔒 Sector `{sector}` status changed to CLOSED. Run /sendcareers to deploy updated layout vectors.", ephemeral=True)


# --- COG SETUP FUNCTION ---
async def setup(bot: commands.Bot):
    await bot.add_cog(RyanairCareers(bot))