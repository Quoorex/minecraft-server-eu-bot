# Minecraft-Server.eu Voting Bot

A voting bot for All sorts of minecraft server listing sites. Supports proxies and multiple servers and usernames to vote for.

Forked from Quoorex who made this bot specifically for minecraft-server.eu

## Requirements

- Python 3.6 or higher
- Pip
- Mozilla Firefox

## Installation

- `pip install -r requirements.txt`
- `python3 bot.py` (`python bot.py` on Windows)

## Configuration

All settings can be edited in [config.yaml](config.yaml).

### Settings

- **username_file:** file to load the username to vote for from
- **vote_url_file:** file to load the vote urls from
  - [example url](https://minecraft-server.eu/vote/index/1A73C)
- **headless:** whether to run display the browser windows (True) or not (False)
- **fake_useragent:** should the browser useragent be faked for every vote attempt
  - Note: this option is not recommended, as this can lead to ReCaptchas not working anymore
- **proxy:**
  - **enabled:** use proxies or not
  - **type:** proxy type; supported options: HTTP, HTTPS, SOCKS4, SOCKS5
  - **file:** file to load the proxies from; proxy format: **host:port**
- **use_timer:** enabling this lets the program vote periodically (every 24h)
  - Note: Using this is not recommended, as the program stops when a error comes up. You should rather use something like `cron` to start the program on a regular basis.

## TODO

- Integrate Captcha Solving API from Antigate
- 2 Modes:
  - Botting only votes
  - Botting rewards (typing usernames in)
- Implement a proxy scraper
- Ip ban check
