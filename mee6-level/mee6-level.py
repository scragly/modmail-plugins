from discord import Embed
from discord.ext import commands
from mee6_py_api import API

from core import checks
from core.models import PermissionLevel


class Mee6Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = API(self.bot.config['guild_id'])
        self.db = bot.api.get_plugin_partition(self)

    @checks.has_permissions(PermissionLevel.ADMIN)
    @commands.command()
    async def set_level_msg(self, ctx, *, message=None):
        """
        Sets a message to add to level responses.

        Can be useful as a quick reference for role/perk level requirements,
        and supports the same variables as `freply`.

        To remove any existing message, run the command without any arguments.
        """
        await self.db.find_one_and_update(
            {"_id": "mee6-level"},
            {"$set": {"level-msg": message}},
            upsert=True,
        )

        embed = Embed(
            colour=ctx.bot.main_color,
            title="Level message has been set to the following:",
            description=message or Embed.Empty
        )
        await ctx.send(embed=embed)

    async def get_level_msg(self):
        """Returns the configured message to include with level responses."""
        config = await self.db.find_one({"_id": "mee6-level"})
        if config is None:
            return
        return config.get("level-msg")

    @checks.thread_only()
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @commands.command()
    async def level(self, ctx):
        """
        Show recipient's MEE6 level.

        Stats are from the main server even if modmail threads are in a secondary server.

        You can add a message to include with the `set_level_msg` command, with support for
        the same variables as `freply`.
        """
        level = await self.api.levels.get_user_level(ctx.thread.id, dont_use_cache=True)
        if level is not None:
            msg = await self.get_level_msg()
            if msg:
                msg = ctx.bot.formatter.format(
                    msg, channel=ctx.channel, recipient=ctx.thread.recipient, author=ctx.message.author
                )
            else:
                msg = Embed.Empty

            embed = Embed(
                colour=ctx.bot.main_color,
                title=f"MEE6 Level: {level}",
                description=msg,
            )
        else:
            embed = Embed(
                colour=ctx.bot.error_color,
                title="MEE6 level not found."
            )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Mee6Level(bot))
