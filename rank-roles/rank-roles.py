import typing as t

from discord import Embed
from discord.ext import commands
from mee6_py_api import API

from core import checks
from core.models import PermissionLevel

if t.TYPE_CHECKING:
    from discord import Message


class RankRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = API(self.bot.config['guild_id'])
        self.db = bot.api.get_plugin_partition(self)
        self._id = "rankroles"

    async def get_level(self, user_id: int):
        return await self.api.levels.get_user_level(user_id, dont_use_cache=True)

    async def config(self, key: t.Optional[str] = None, **set_values):
        if not key and not set_values:
            return await self.db.find_one({"_id": self._id})

        if key:
            config = await self.db.find_one({"_id": self._id})
            return config.get(key)

        await self.db.find_one_and_update({"_id": self._id}, {"$set": set_values}, upsert=True)

    @commands.Cog.listener()
    async def on_thread_ready(self, thread, _creator, _category, _initial_message):
        level = await self.get_level(thread.id)
        msg = await thread.channel.fetch_message(thread.genesis_message.id)
        embed: Embed = msg.embeds[0]
        embed.add_field(name="Level", value=str(level) if level else "0")
        await msg.edit(embed=embed)

    @checks.thread_only()
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @commands.command()
    async def level(self, ctx):
        """
        Show recipient's level.

        Stats are from the main server even if modmail threads are in a secondary server.

        You can add a message to include with the `set_level_msg` command, with support for
        the same variables as `freply`.
        """
        level = await self.get_level(ctx.thread.id)
        if level is None:
            level = 0
        embed = Embed(
            colour=ctx.bot.main_color,
            title=f"Level: {level}",
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(RankRoles(bot))
