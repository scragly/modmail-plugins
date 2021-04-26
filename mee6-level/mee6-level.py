from discord import Embed
from discord.ext import commands
from mee6_py_api import API

from core import checks
from core.models import PermissionLevel


class Mee6Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = API(self.bot.config['guild_id'])

    @checks.thread_only()
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @commands.command()
    async def level(self, ctx):
        level = await self.api.levels.get_user_level(ctx.thread.id, dont_use_cache=True)
        if level is not None:
            embed = Embed(
                colour=ctx.bot.main_color,
                description=f"MEE6 Level: {level}"
            )
        else:
            embed = Embed(
                colour=ctx.bot.error_color,
                description="MEE6 level not found."
            )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Mee6Level(bot))
