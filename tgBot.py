import requests
import telebot
import os
import re

BASE_URL = 'https://fragment.com/'
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'

class Telegram:
    def __init__(self, bot_token):
        self.bot = telebot.TeleBot(bot_token)

    def get_user(self, username: str):
        if len(username) < 5 or len(username) > 32:
            return None

        response = requests.get(BASE_URL + 'username/' + username, headers={
            'User-Agent': DEFAULT_USER_AGENT,
            'X-Aj-Referer': f'{BASE_URL}?query={username}',
            'Accept': 'application/json, text/javascript, /; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'trailers'
        })

        if response.status_code != 200:
            return 'Error fetching data'

        try:
            response_json = response.json()
        except ValueError:
            return None

        if 'h' not in response_json:
            return 'свободен'

        h_data = response_json['h']

        status = h_data.split('tm-section-header-status')[1].split('">')[0].strip()
        status_mapping = {
            'tm-status-taken': 'taken',
            'tm-status-avail': 'on auc',
            'tm-status-unavail': 'sold'
        }

        return status_mapping.get(status, 'Unknown')

    def check_usernames(self, usernames):
        results = []
        for username in usernames:
            status = self.get_user(username)
            if status:
                results.append(f'{username} {status}')

        if len(results) > 10:
            self.save_results_to_file(results)

        return results

    def save_results_to_file(self, results):
        filename = 'username_check_results.txt'
        with open(filename, 'w') as file:
            for result in results:
                file.write(result + '\n')

        return filename

    def contains_russian(self, text):
        return bool(re.search('[а-яА-Я]', text))


# Initialize the bot with your token
bot_token = 'spokdpaokapodka:dsaokdsapoaskapok'
tg = Telegram(bot_token)

@tg.bot.message_handler(commands=['check'])
def handle_check_command(message):
    # Ask the user to provide usernames
    tg.bot.send_message(message.chat.id, 'Drop your username to check, the separation is separated by commas')

@tg.bot.message_handler(commands=['start'])
def handle_start_command(message):
    pass

@tg.bot.message_handler(func=lambda message: True)
def handle_usernames(message):
    if message.text.startswith('/') and message.text not in ['/check']:
        return

    if tg.contains_russian(message.text):
        tg.bot.send_message(message.chat.id, 'Please use only Latin characters (no Russian letters).')
        return

    # Split the input by commas and strip any extra spaces
    usernames = [username.strip() for username in message.text.split(',')]
    results = tg.check_usernames(usernames)

    # Send results to the user or compile them in a file if too many
    if len(results) > 10:
        filename = tg.save_results_to_file(results)
        tg.bot.send_message(message.chat.id, 'Lots of results, answer in .txt below')
        with open(filename, 'rb') as file:
            tg.bot.send_document(message.chat.id, file, caption='Results')
    else:
        # Send results to the user directly
        for result in results:
            tg.bot.send_message(message.chat.id, result)

@tg.bot.message_handler(content_types=['document'])
def handle_document(message):
    # Handle the document containing usernames
    if message.document.mime_type == 'text/plain':
        file_info = tg.bot.get_file(message.document.file_id)
        file = tg.bot.download_file(file_info.file_path)

        # Save the file locally and read usernames
        with open(message.document.file_name, 'wb') as new_file:
            new_file.write(file)

        # Read usernames from the file
        with open(message.document.file_name, 'r') as user_file:
            usernames = [line.strip() for line in user_file if line.strip()]

        # Проверка на русские символы в именах пользователей из файла
        usernames = [username for username in usernames if not tg.contains_russian(username)]

        results = tg.check_usernames(usernames)

        # Send results to the user or compile them in a file if too many
        if len(results) > 10:
            filename = tg.save_results_to_file(results)
            tg.bot.send_message(message.chat.id, 'There are too many results, here is the result file:')
            with open(filename, 'rb') as file:
                tg.bot.send_document(message.chat.id, file, caption='Results')
        else:
            # Send results to the user directly
            for result in results:
                tg.bot.send_message(message.chat.id, result)

# Start the bot
tg.bot.polling()
