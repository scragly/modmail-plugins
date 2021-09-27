import asyncio
import os
import typing

import aiohttp
from discord import Embed
from discord.ext import commands

import pendulum


ENDPOINT = "https://api.gaiusbot.me/warnings"


class GaiusWarnException(Exception):
    pass


class GaiusWarning:
    def __init__(self, warnid, userid, reason, warndate, pardonerid, pardondate, modid, **_kwargs):
        self.id: int = int(warnid)
        self.user_id: int = int(userid)
        self.mod_id: int = int(modid)
        self.reason: str = reason
        self.created = pendulum.from_timestamp(int(warndate[:-3]))
        self.pardoner_id = int(pardonerid) if pardonerid else None
        self.pardon_date = pendulum.from_timestamp(int(pardondate[:-3])) if pardondate else None

    @property
    def active(self):
        return not self.pardon_date

    def timestamp(self, relative=False):
        if relative:
            return f"<t:{self.created.int_timestamp}:r>"
        return f"<t:{self.created.int_timestamp}>"

    def pardoned_timestamp(self, relative=False):
        if not self.pardon_date:
            return
        if relative:
            return f"<t:{self.pardon_date.int_timestamp}:r>"
        return f"<t:{self.pardon_date.int_timestamp}>"


class GaiusWarns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.api.get_plugin_partition(self)
        self._session: typing.Optional[aiohttp.ClientSession] = None
        self._apikey: str = os.environ["gaius_api_key"]

    async def get_warns(self, user_id: int):
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(headers={"API-KEY": self._apikey})

        async with self._session.get(f"{ENDPOINT}/{user_id}") as req:
            if req.status != 200:
                raise GaiusWarnException(f"Request failed: STATUS {req.status}")
            payload = await req.json()

        return [GaiusWarning(**d) for d in sorted(payload, key=lambda i: i["warnid"], reverse=True)]

    @commands.Cog.listener()
    async def on_thread_ready(self, thread, _creator, _category, _initial_message):
        warnings: typing.List[GaiusWarning] = await self.get_warns(thread.id)
        await asyncio.sleep(2)
        msg = await thread.channel.fetch_message(thread.genesis_message.id)
        embed: Embed = msg.embeds[0]
        if not warnings:
            embed.add_field(name=f"Gaius Warnings", value="No warnings found.")
        else:
            last = warnings[0]
            output = [
                "**Last Warning Received**",
                f"**ID:** {last.id}",
                f"**Date:** {last.timestamp()} ({last.timestamp(relative=True)})",
                f"**Mod:** <@{last.mod_id}>"
            ]
            if last.pardon_date:
                output.append(f"**Pardoned:** {last.pardoned_timestamp()} ({last.pardoned_timestamp(relative=True)})")
            output.append(f"**Reason:** {last.reason}")
            embed.add_field(
                name=f"{len(warnings)} Gaius Warnings",
                value="\n".join(output),
                inline=False
            )
        await msg.edit(embed=embed)


def setup(bot):
    bot.add_cog(GaiusWarns(bot))
