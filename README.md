# FAST (Fast Agile Standup Tracker) Bot
> The problem with being faster than light is that you can only live in darkness

Created for my Senior Design team who needed a bot with custom features to help with using the Agile development process.

Not properly programmed to work across different discords at the same time yet
### fast.json Config File Structure
```
{
   "token": "bot oauth token",
   "test": false,
   "test_server": <int id>,
   "channel": "channel-name",
   "status": "bot's status",
   "help": "discord markdown formatted message",
   "leaderboardAnnounce": "message",
   "nonconfigurable": ["token", "test", "test_server", "questions", "people", "announcements"],
   "patchnotes": "discord formatted patch notes messages",
   "announcements": ["list of potential announcement starting messages"],
   "questions": ["list of questions to be asked in standup"],
   "people": [{"id": <int discord id>, "name": "name for display"}, ...]
}
```
- ``test`` and ``test_server`` set when and where to debug new features and disables the bot elsewhere to allow for debugging without spamming the group or kicking the bot.
- ``channel`` is the default standup channel.
- ``status`` is the bot's disscord status
- ``leaderboardAnnounce`` is the message sent along with the leaderboard bar plot
- ``nonconfigurable`` are the keys in this file that can't be changed dynamically by bot commands
- ``announcements`` is the random list of standup announcements that can choose from
- ``questions`` are the questions asked in the standups
- ``people`` currently a predefined list of people who will participate in the standups along with the names to put in the graph. should be dynamically made later.
