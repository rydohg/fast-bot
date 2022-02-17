# FAST Bot: Fast Agile Standup Tracker
# Sends a standup announcement every Tuesday, Thursday, and Saturday and
# reminds those who don't mark it complete by reacting to complete it

# fast.json structure:
# {
#   "token": "bot oauth token", "test": false, "test_server": <int id>, "channel": "channel-name",
#   "status": "bot's status",
#   "help": "discord markdown formatted message",
#   "leaderboardAnnounce": "message",
#   "nonconfigurable": ["token", "test", "test_server", "questions", "people", "announcements"],
#   "patchnotes": "discord formatted patch notes messages",
#   "announcements": ["list of potential announcement starting messages"],
#   "questions": ["list of questions to be asked in standup"],
#   "people": [{"id": <int discord id>, "name": "name for display"}, ...]
# }

# Invite link: https://discord.com/api/oauth2/authorize?client_id=932418168201281537&permissions=8590421056&scope=bot
import os.path
import time
import discord
import random
import json
from datetime import datetime
import aiocron
import re

# For creating the graphs
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


# Discord bots are defined as a subclass of discord.Client
class FASTClient(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)
        self.standups = {}

    async def on_ready(self):
        print("The problem with being faster than light is that you can only live in darkness...")
        # Change discord status
        await client.change_presence(activity=discord.Game(data['status']))
        # Initialize the standup tracking array to false in every server it's in
        for guild in self.guilds:
            self.standups[guild.id] = {name['id']: False for name in data['people']}

    async def on_message(self, message: discord.Message):
        if message.author != client.user:
            if message.content.startswith('!fastbot'):
                await message.channel.send(data['help'])
            elif message.content.startswith('!checkStandup'):
                await self.check_standup(last_chance=True)
            elif message.content.startswith('!announceStandup'):
                await self.announce_standup()
            elif message.content.startswith("!leaderboard"):
                await self.send_leaderboard(message.channel)
            elif message.content.startswith("!set"):
                await self.set_config(message)
            elif message.content.startswith("!config"):
                await self.show_configurables(message)
            elif message.content.startswith("!patchnotes"):
                await message.channel.send(data['patchnotes'])
            elif message.channel.name == data['channel']:
                # Mark standup complete on message to standup channel
                # and react to message to show it works
                if message.author != client.user:
                    current_standup = self.standups[message.guild.id]
                    if not current_standup[message.author.id]:
                        current_standup[message.author.id] = True
                        await message.add_reaction("<:takeASeat:892174188083822652>")
                        print(f'Completed Standup: {current_standup}')

    # async def on_reaction_add(self, reaction, user):
    #     print(user.id)
    #     if user != client.user and reaction.message.author == client.user:
    #         current_standup = self.standups[reaction.message.guild.id]
    #         current_standup[user.id] = True
    #         print(f'Completed Standup: {current_standup}')

    async def announce_standup(self):
        for guild in self.guilds:
            # Only send the messages in the test server if test is enabled and only in MOSafely Studios if not
            if data['test'] and guild.id != data['test_server']:
                continue
            if not data['test'] and guild.id == data['test_server']:
                continue
            # Reset Standup tracker to not mark people who complete the last standup
            # afterwards from being counted for the next
            self.standups[guild.id] = {name['id']: False for name in data['people']}

            # Get permission to mention everyone, get a random announcement, then write out each question in the
            # questions JSON array
            mention_everyone = discord.AllowedMentions(everyone=True)
            announcement = f"@everyone Happy {datetime.today().strftime('%A')}!\n" \
                           f"{random.choice(data['announcements'])}\n" \
                           f"__**Standup Questions:**__\n"
            for i, q in enumerate(data['questions']):
                announcement += f'{i + 1}. {q}\n'
            announcement += "Please send your responses here and I'll react to them when you're marked done!"

            # Send formatted message to the channel name in the config and add the first reaction to it
            channel = discord.utils.get(guild.channels, name=data['channel'])
            announcement_msg = await channel.send(content=announcement, allowed_mentions=mention_everyone)
            # await announcement_msg.add_reaction("<:takeASeat:892174188083822652>")

            # Send reminder to update Jira
            await channel.send(
                "Also don't forget to update the Jira! please? "
                "https://mosafely.atlassian.net/jira/software/projects/MD/boards/1"
            )

    async def check_standup(self, last_chance=False):
        for guild in self.guilds:
            # Only send the messages in the test server if test is enabled and only in MOSafely Studios if not
            if data['test'] and guild.id != data['test_server']:
                continue
            if not data['test'] and guild.id == data['test_server']:
                continue
            # Check if everyone is done and format report accordingly
            current_standup = self.standups[guild.id]
            all_done = True
            announcement = "__**Standup Report:**__\n"
            print(current_standup)
            for person in current_standup:
                if not current_standup[person]:
                    all_done = False
                    announcement += f"<@{person}> "
            if not all_done:
                announcement += " please complete your standup(s)!"
            else:
                announcement += "Everyone did their standups! Good job! <:takeASeat:892174188083822652>"
            # Send report
            channel = discord.utils.get(guild.channels, name=data['channel'])
            await channel.send(announcement)

            # Only add to the leaderboard after the last reminder of a standup
            if last_chance:
                if os.path.exists('leaderboard.csv'):
                    df = pd.read_csv('leaderboard.csv')
                else:
                    df = pd.DataFrame()
                    df['id'] = [person['id'] for person in data['people']]
                    df['name'] = [person['name'] for person in data['people']]
                    df['completions'] = 0

                # Increment the number of completions per person who completed this standup
                # Then write new leaderboard df to file
                for person in current_standup:
                    if current_standup[person]:
                        df.loc[df['id'] == person, 'completions'] += 1

                df.to_csv('leaderboard.csv', index=False)
                # Send leaderboard message
                await self.send_leaderboard(channel)
            return all_done

    @staticmethod
    async def send_leaderboard(channel: discord.TextChannel):
        # Create bar plot from data and send it along with the leaderboardAnnounce value
        df = pd.read_csv('leaderboard.csv')
        sns.barplot(x='name', y='completions', data=df)
        plt.savefig("figure.png")
        await channel.send(data['leaderboardAnnounce'], file=discord.File("figure.png"))

    @staticmethod
    async def set_config(message):
        # Splits the command on spaces except when they're in quotes using regex
        command = [p for p in re.split("( |\\\".*?\\\"|'.*?')", str(message.content)) if p.strip()]
        print(command)

        # Only write valid commands to config
        if len(command) != 3:
            await message.channel.send("Not enough arguments for set.\nEx: ``!set key value``")
        elif command[1] not in data.keys():
            await message.channel.send(f'{command[1]} is not a configurable value')
        else:
            write_to_config(command[1], command[2].strip("\""))

    @staticmethod
    async def show_configurables(message):
        # Get list of configurable values in the json file
        # Not all values can or should be changeable by commands
        # so this function only shows those that can be
        configurables = "Configurable values: ```"
        for key in data.keys():
            if key not in data['nonconfigurable']:
                configurables += key + "\n"

        await message.channel.send(configurables + '```')


# crontab uses UTC so this is 12 EST on Sunday, Tuesday, and Thursday
@aiocron.crontab('0 17 * * 0,2,4', start=False)
async def standup():
    await client.announce_standup()


@aiocron.crontab('0 19 * * 0,2,4', start=False)
async def check():
    all_done = await client.check_standup()
    if not all_done:
        time.sleep(3600)
        await client.check_standup(last_chance=True)


# Write to json config only valid keys
def write_to_config(key, value):
    if key not in data['nonconfigurable']:
        data[key] = value
        with open('fast.json', 'w') as file:
            file.write(json.dumps(data))


# Start aiocron timers
standup.start()
check.start()

# Load the configuration file and start the discord bot client
data = json.load(open("fast.json"))

# This allows for getting member names dynamically, requires change in discord dev portal
intents = discord.Intents.default()
intents.members = True

client = FASTClient(intents=intents)
client.run(data['token'])
