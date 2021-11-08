# Minecraft-Server.eu Voting Bot

A voting bot for Minecraft-Server.eu. Supports proxies and multiple servers and usernames to vote for.

## Requirements

- Python 3.6 or higher
- Pip
- Poetry (`pip install poetry`)
- Mozilla Firefox

## Important

- Minecraft-Server.eu does IP ban after around 4-5 votes (not exactly sure) so it's advised to use proxies (that are not banned by Google or else the captchas won't work)

## Installation

- `poetry install`  
  - this will setup a virtual environment for the project
- `poetry shell`
  - activates the environment
- `python main.py`
  - runs the program

## Configuration

All settings can be edited in [config.yaml](config.yaml).

### Settings

- __username_file:__ file to load the username to vote for from  
- __vote_url_file:__ file to load the vote urls from  
  - [example url](https://minecraft-server.eu/vote/index/1A73C)  
- __headless:__ whether to run display the browser windows (True) or not (False)
- __fake_useragent:__ should the browser useragent be faked for every vote attempt
  - Note: this option is not recommended, as this can lead to ReCaptchas not working anymore
- __proxy:__
  - __enabled:__ use proxies or not
  - __type:__ proxy type; supported options: HTTP, HTTPS, SOCKS4, SOCKS5
  - __file:__ file to load the proxies from; proxy format: __host:port__
- __use_timer:__ enabling this lets the program vote periodically (every 24h)
  - Note: Using this is not recommended, as the program stops when a error comes up. You should rather use something like `cron` to start the program on a regular basis.
