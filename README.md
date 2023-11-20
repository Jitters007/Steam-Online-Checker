# SteamOnlineChecker

**SteamOnlineChecker** is a Telegram bot that allows users to track the status of Steam accounts.

## Installation

1. Install the required libraries:

    ```bash
    pip install pyTelegramBotAPI requests schedule
    ```

2. Replace the value of the `bot_token` variable with your Telegram bot token.

3. Replace the value of the `steam_token` variable with your Steam API key.

   3.1. You can create your Steam API key [here](https://steamcommunity.com/dev/apikey)

4. Run the bot:

    ```bash
    python main.py
    ```

## Usage

1. Send the `/start` command to register with the bot.

2. Add a Steam ID for tracking using the `/add` command.

3. Check the status of Steam IDs with the `/list` command.

4. Remove Steam IDs using the `/remove` command.

5. Additional commands:
   - `/help`: Displays a help message.

## Project Structure

- `main.py`: The main bot script.
- `main.db`: SQLite database for storing user and tracking information.

## Dependencies

- `pyTelegramBotAPI`: Library for working with the Telegram Bot API.
- `requests`: Library for making HTTP requests.
- `schedule`: Library for managing scheduled tasks.

## License

This project is distributed under the [GNU GENERAL PUBLIC LICENSE](LICENSE).
