# Hi guys, this DDoS bot source is the second version of <br>[https://github.com/vominht/BOT-DDoS-TELEGRAM]
### Any questions pm Telegram <br> https://t.me/daviinci_b
## Install
```
git clone https://github.com/vominht/BOT-DDoS-TELEGRAM-V2
```
## To setup this bot, following these commands
```
pip install python-telegram-bot --upgrade
pip install aiohttp
```
## Then, setting bot in BotFather: Bot Settings >> Inline Mode >> Turn On >> Edit Inline Placeholder and type placeholder for your bot
## Tag bot to start attack, for example:<br> @botusername http://target.com time port 

# Commands

Below are the available commands for system interaction and administration:

### User Commands
- `plan` - View your plan details.
- `running` - View your current running status.

### Administrative Commands
- `bl` - Blacklist a user. [Admin Only]
- `ban` - Ban or unban a user. [Admin Only]
- `add` - Add a new user to the system. [Admin Only]
- `method` - Manage methods. [Admin Only]
- `listban` - View all banned users. [Admin Only]

### Note: if you want to use script instead of api to perform attack, use file main (more attack options).py
And please configure as follows
- `Line 82:` configure command to run script
- `Line 318,319:` attack option with script or api

## Credit: Telegram @daviinci_b
