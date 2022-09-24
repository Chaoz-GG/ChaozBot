# Chaoz.GG CSGO Bot

## Table of Contents

- [About](#about)
- [Installation](#installation)
  * [Requirements](#requirements)
  * [Setup](#setup)
- [Running](#running)
- [Data Files](#data-files)

## About

> This is a multipurpose bot for the Chaoz.GG Discord server. It is written in Python 3.8 and uses the [discord.py](https://github.com/Rapptz/discord.py) module as the primary gateway for communication with the Discord API.
> The project utilizes the [StatsAPI](https://github.com/Chaoz-GG/StatsAPI) for the majority of its data functions, such as the statistics and inventory value calculation. Both the `StatsAPI` and `ChaozBot` are licensed to the Chaoz.GG organization.
> All the development of `StatsAPI` and `ChaozBot` is done by [`Sn1F3rt#0001`](https://github.com/Sn1F3rt) who is compensated by the Chaoz.GG organization for his work.
> Developmental support for both the repositories will be provided as long as it is in the scope of the already discussed plans and something isn't working as intended. 
> Issues due to library updates or changes in the Discord API will be looked into, however, no guarantee is provided for their fix without a change in the working system of the bot's architecture.

> :warning: **The project utilizes `discord.py` 2.0 and any version <2.0 is NOT supported.**

## Installation

### Requirements

Install the latest version of `google-chrome` and MySQL/MariaDB on your server.

### Setup

**Do not run either the StatsAPI or ChaozBot as root!** Use a user without SSH access to prevent any security vulnerabilities.

```
sudo adduser chaozbot
sudo passwd -l chaozbot
sudo su - chaozbot
```

1. Clone both the repositories to your server.
2. Create a virtual environment inside both the `StatsAPI` and `ChaozBot` directories using `python -m venv venv`.
3. Activate the virtual environment using `source venv/bin/activate`.
4. Install the required Python modules inside each directory using `pip install -r requirements.txt`.
5. Create a new database in MySQL/MariaDB and import the `chaozgg.sql` file.
6. Copy the `config.example.json` file from both the repositories to `config.json` and fill in the required information. 

### Running 

> :warning: Remember to activate the virtual environment using `source venv/bin/activate` before running either of them.

StatsAPI uses `gunicorn` for production and so you can run a production server using the `bin/prod` shell file which has been pre-written and optimized for production.

`ChaozBot` can simply be run using `python bot.py`.

## Data Files

1. `config.example.json`/`config.json` - Contains the configuration for `StatsAPI` and `ChaozBot`.
2. `chaozgg.sql` - Contains the database structure for the system.
3. `requirements.txt` - Contains the required Python modules for both the repositories.
4. `bin/prod` - Contains the shell script for running the `StatsAPI` in production.
5. `data/games.json` - Contains the available games in real time for Chaoz.GG.
6. `data/games_backup.json` - Contains a backup copy of all the pre-initialized games just in case something goes wrong with the `games.json` file.
7. `data/leaderboard.json` - Stores the message IDs for the region-wise leaderboards for statistics. To regenerate the leaderboards, simple empty this file. 
8. `data/messages.json` - Contains all the messages that the bot uses to interact with the users. Edit as per the subkey. Every cog has its own key in the file.
9. `data/teams.json` - Stores the message ID for the team creation message. To regenerate the message, simple empty this file.
10. `data/timezones.json` - Contains a list of all the timezones supported by Chaoz.GG.