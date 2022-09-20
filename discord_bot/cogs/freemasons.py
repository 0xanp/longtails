import datetime
import django
import discord
import requests
from django.conf import settings
import csv
import io

from discord import app_commands
from discord.ext import commands, tasks

from asgiref.sync import sync_to_async

from freemasons.models import SECONDS_BETWEEN_SYNC, FreeMasonMember, FreeMasonProject, TwitterUser
from twitter.client import TwitterClient

URLS = {
    "TOKEN_OWNER": "https://deep-index.moralis.io/api/v2/nft/{0}/{1}/owners?chain=eth&format=decimal",
    "MEMBERS": "http://www.nftinspect.xyz/api/collections/members/{0}?limit=2000&onlyNewMembers=false",
    "DETAILS": "https://www.nftinspect.xyz/api/collections/details/{0}"
}

class FreeMasons(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = discord.utils.find(
            lambda g: g.name == settings.DISCORD_GUILD_NAME,
            self.bot.guilds
        )

        self.longtails_channel = discord.utils.get(
            self.guild.text_channels,
            name=settings.DISCORD_CHANNEL_NAME
        )

        self.longtails_log_channel = discord.utils.get(
            self.guild.text_channels,
            name=settings.DISCORD_LOG_CHANNEL_NAME
        )        

        self.twitter_client = TwitterClient()

        self.sync_projects.start()
        print('[FreeMasons] Online.')

    async def send_summary(self, title_key, project_obj, summary):
        # prepare an embeded summary message 
        embed = discord.Embed(
            title=f"{project_obj.name} owners have started following these accounts",
            description="\n".join(
                [f"[{member_inst['username']}](https://twitter.com/i/user/{member_inst['twitter_identifier']}): {member_inst['count']}" for member_inst in summary])
        )
        # also prepare a csv file for internal use
        header = ['Name', 'Twitter','Count']
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(header)
        for member_inst in summary:
            data = [member_inst['username'],f"https://twitter.com/i/user/{member_inst['twitter_identifier']}", member_inst['count']]
            writer.writerow(header)
            writer.writerows(data)
        buffer.seek(0) #Don't know why this is here, but it worked...
        csv.close()
        await self.longtails_log_channel.send(file=discord.File(buffer, f"{project_obj.name}-{django.utils.timezone.now()}.csv"))
        await self.longtails_channel.send(embed=embed)

    @tasks.loop(seconds=60)
    async def sync_projects(self):
        print("[FreeMasons] [Sync] Clock.")

        projects = FreeMasonProject.objects.filter(
            watching=True,
        )

        for project_obj in projects.all():
            if not project_obj.next_sync_at or project_obj.next_sync_at < django.utils.timezone.now():
                print(
                    f'[FreeMasons] [Sync] [Project] {project_obj.contract_address}')
                embed = discord.Embed(
                    title=f"[FreeMasons] [Sync] [{project_obj.name}]"
                )

                embed.add_field(
                    name="Contract address",
                    value=project_obj.contract_address
                )

                await self.longtails_log_channel.send(embed=embed)

                await project_obj.sync()

            for member in project_obj.members.filter(
                next_sync_at__lte=django.utils.timezone.now()
            ) | project_obj.members.filter(next_sync_at__isnull=True):
                print(
                    f'[FreeMasons] [Sync] [Member] {member.twitter.username}')  
                await member.sync(self.twitter_client)

            if not project_obj.last_summarized_at or project_obj.last_summarized_at < django.utils.timezone.now() - datetime.timedelta(seconds=SECONDS_BETWEEN_SYNC):
                await self.send_summary('Followed By', project_obj, project_obj.member_following_summary[:30])
                # await self.send_summary('Follower Of', project_obj, project_obj.member_follower_summary[:50])

                project_obj.last_summarized_at = django.utils.timezone.now()
                project_obj.save()

    @app_commands.command(name="watch")
    async def watch(self, interaction: discord.Interaction, contract_address: str) -> None:
        await interaction.response.send_message("Updating status.", ephemeral=True)
        response = requests.get(URLS["DETAILS"].format(contract_address.lower()))
        
        if response.status_code == 200:
            project_obj, created = FreeMasonProject.objects.get_or_create(
            contract_address=contract_address.lower()
            )

            project_obj.watching = not project_obj.watching

            if project_obj.watching:
                await project_obj.sync()

            project_obj.save()

            embed = discord.Embed(
                title=f"Watching {project_obj.name}"
            )

            embed.add_field(name="Contract address", value=contract_address)
            embed.add_field(
                name="Watching",
                value="✅" if project_obj.watching else "❌",
                inline=False
            )
            response.close()
        else:
            embed = discord.Embed(
                title="Can't find entered project, please double check the smart contract address and wait a minute before trying again"
            )
            response.close()
        await self.longtails_log_channel.send(embed=embed)

    @app_commands.command(name="watching")
    async def watching(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Logging statuses.", ephemeral=True)

        projects = FreeMasonProject.objects.filter(watching=True)

        embed = discord.Embed(
            title=f"ML Twitter Bot is currently watching:",
            description="\n".join(
                f"[{project_obj.name}]({project_obj.twitter})" for project_obj in projects.all())
        )

        await self.longtails_channel.send(embed=embed)

    @app_commands.command(name="watched")
    async def watched(self, interaction: discord.Interaction, twitter_username: str) -> None:
        await interaction.response.send_message("Grabbing the data that we have for that username.", ephemeral=True)

        # get twitter object of username we are searching
        twitter_user_obj = TwitterUser.objects.filter(
            username=twitter_username)

        # return no data message if we don't have this user in the database
        if not twitter_user_obj.exists():
            embed = discord.Embed(
                title=f"ML Twitter Bot never scraped {twitter_username}",
            )

            await self.longtails_channel.send(embed=embed)

            return

        # find members that are following that user
        members = FreeMasonMember.objects.filter(
            following__in=[twitter_user_obj.first(), ]).exclude(twitter__username__isnull=True).exclude(twitter__twitter_identifier__isnull=True)

        description = "\n".join(
            [f"[{member_inst.twitter.username}](https://twitter.com/i/user/{member_inst.twitter.twitter_identifier})" for member_inst in members.all()])

        if members.count() == 0 or description == "":
            # return no data message if we don't have this user in the database
            embed = discord.Embed(
                title=f"{twitter_username} is not a hot follow.",
            )

            await self.longtails_channel.send(embed=embed)

            return 

        # return output
        embed = discord.Embed(
            title=f"Followers Of {twitter_username}",
            description=description
        )

        await self.longtails_channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        FreeMasons(bot),
        guilds=[discord.Object(id=settings.DISCORD_GUILD_ID)]
    )

    print("[FreeMasons] Setup.")
