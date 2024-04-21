import requests
import telebot
from decouple import config

BOT_TOKEN = config('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)

ABOUT_TEXT = """This bot is example bot to convert currencies to each other.
What do you want to do?"""


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    text = """
    Hello!, Wellcome
    to start the currency converting process please enter /currency
    """
    bot.reply_to(message, text)


def get_valid_currency_codes():
    try:
        response = requests.get("https://openexchangerates.org/api/currencies.json")
        if response.status_code == 200:
            return response.json().keys()
        else:
            return []
    except requests.exceptions.RequestException:
        return []


def is_valid_currency(currency_code):
    valid_currency_codes = get_valid_currency_codes()
    return currency_code in valid_currency_codes


def get_currency_rate(from_currency: str, to_currency: str, amount: float):
    url = "https://api.frankfurter.app/latest"
    params = {"from": from_currency, "to": to_currency, "amount": amount}
    response = requests.get(url, params)

    return response


@bot.message_handler(commands=['currency'])
def from_currency_handler(message):
    text = "which currency you want to convert from ?"
    sent_msg = bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(sent_msg, to_currency_handler)


def to_currency_handler(message):
    from_currency = message.text.upper()

    if not is_valid_currency(from_currency):
        text = "Invalid currency code. Please enter a valid currency code."
        sent_msg = bot.send_message(message.chat.id, text)
        bot.register_next_step_handler(sent_msg, to_currency_handler)
        return

    text = "which currency you want to convert to ?"
    sent_msg = bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(sent_msg, amount_handler, from_currency)


def amount_handler(message, from_currency):
    to_currency = message.text.upper()

    if not is_valid_currency(to_currency):
        text = "Invalid currency code. Please enter a valid currency code."
        sent_msg = bot.send_message(message.chat.id, text)
        bot.register_next_step_handler(sent_msg, amount_handler, from_currency)
        return

    if from_currency == to_currency:
        text = "The 'from' currency cannot be the same as the 'to' currency. Please choose a different currency."
        sent_msg = bot.send_message(message.chat.id, text)
        bot.register_next_step_handler(sent_msg, amount_handler, from_currency)
        return

    text = "Enter the amount you want to convert:"
    sent_msg = bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(sent_msg, perform_conversion, from_currency, to_currency)


def perform_conversion(message, from_currency, to_currency):
    try:
        amount = float(message.text)
        conversion_result = get_currency_rate(from_currency, to_currency, amount)
        rate = conversion_result.json()['rates'][to_currency]
        response_message = f"{amount} {from_currency} = {rate} {to_currency}"
        bot.send_message(message.chat.id, response_message)
    except ValueError:
        bot.send_message(message.chat.id, "Invalid amount. Please enter a valid number.")


@bot.message_handler(commands=['about'])
def about_handler(message):
    bot.send_message(message.chat.id, ABOUT_TEXT)


@bot.message_handler(func=lambda message: True)
def default_handler(message):
    text = "Sorry, I didn't understand that. Please use /currency or /about."
    bot.send_message(message.chat.id, text)


bot.infinity_polling()
