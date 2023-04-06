import logging
import os
from aiogram import Bot, types
import json
import pyshorteners
import time
import datetime
from aiogram.types import InlineKeyboardMarkup
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils import exceptions
from threading import Thread
from schedule import every, run_pending
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters import FiltersFactory
from scripts import config
from scripts.utils import States
from scripts.db import BotDB
import asyncio
import functools
from collectors import horoscope, currency
from collectors import news

bot = Bot(token=config.BETA_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
BotDB = BotDB()
filters = FiltersFactory(dp)
ALL_NEWS = {}
zodiac_signs = list(config.zodiac_signs_links.keys())


def shorten_url(url):
	return pyshorteners.Shortener().clckru.short(url)


def event_starter(func):
	if not func.is_running():
		func.start()


async def send_curr(user_id, btn=True):
	curr = currency.get()
	btns = [[
		types.InlineKeyboardButton(
			text="Другая валюта",
			callback_data="other_currency")
	]]
	builder = InlineKeyboardMarkup(inline_keyboard=btns if btn else None)
	await bot.send_message(
		user_id,
		f"{curr['USD']['name']} (USD): {curr['USD']['val']}₽\n"
		f"{curr['EUR']['name']} (EUR): {curr['EUR']['val']}₽",
		reply_markup=builder)


async def birthday(user_id):
	day = str(int(datetime.date.today().strftime('%d')))
	month = str(int(datetime.date.today().strftime('%m')))
	data = '.'.join([day, month])
	if BotDB.get_birth(user_id) == data:
		await bot.send_message(
			user_id,
			"Дорогой пользователь, поздравляю Вас с днем рождения, спасибо, что Вы с нами!🥳")


async def menu(message, text='Вы в меню'):
	state = dp.current_state(user=message.from_user.id)
	BotDB.update_status(message.from_user.id, "menu")
	btn1 = types.KeyboardButton(text="Гороскопы🪐")
	btn2 = types.KeyboardButton(text="Курсы валют💰")
	btn3 = types.KeyboardButton(text="Новости📰")
	btn5 = types.KeyboardButton(text="Инвестиции📈")
	btn4 = types.KeyboardButton(text="Настройки⚙")
	kb = [[btn1, btn2, btn3], [btn5, btn4]]
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb)
	await message.answer(text, reply_markup=markup)
	await state.set_state(States.MENU_STATE[0])


async def send_mail(user_id):
	try:
		await birthday(user_id)
		true_modes = BotDB.get_modes(user_id)
		modes = true_modes.split(';')
		if modes:
			await bot.send_message(user_id, "Утренние новости☕️📰:")
			if '2' in modes:
				znak = BotDB.get_znak(user_id)
				if znak in config.zodiac_signs_links:
					await bot.send_message(user_id, horoscope.get(config.zodiac_signs_links[znak])[0])
					for j in horoscope.get(config.zodiac_signs_links[znak])[1]:
						await bot.send_message(user_id, j.text)
				else:
					await bot.send_message(
						user_id,
						"Вы не указали вашу дату рождения для гороскопа.")
			if '3' in modes:
				await send_curr(user_id, btn=False)

			if '1' in modes:
				for num in range(len(ALL_NEWS['https://dzen.ru/news'][:6])):
					await send_news(user_id, 'https://dzen.ru/news', num, skip_btn=False)

	except exceptions.BotBlocked:
		logging.warning("Bot blocked by user")
	except exceptions.ChatNotFound:
		logging.warning("Chat not found")
	except exceptions.UserDeactivated:
		logging.warning("User is deactivated")
	except exceptions.TelegramAPIError:
		logging.warning("Telegram API error occurred")
	except Exception as e:
		logging.warning(f"Error occurred: {e}")


async def start_mailing():
	now = datetime.datetime.now().time().replace(microsecond=0, second=0)

	if now == config.SEND_TIME:
		logging.info('start mailing')
		tasks = []
		for user_id, in BotDB.get_id():
			tasks.append(asyncio.create_task(send_mail(user_id)))
		await asyncio.gather(*tasks)



async def send_news(user_id, topic, article, skip_btn=True):
	if topic in ALL_NEWS and article < len(ALL_NEWS[topic]) - 1 and len(ALL_NEWS[topic]) > 0:
		skip = types.InlineKeyboardButton(text="Дальше", callback_data="skip")
		det = types.InlineKeyboardButton(text='Подробнее', url=shorten_url(ALL_NEWS[topic][article]['url']))
		key_b = [[skip, det]] if skip_btn else [[det]]

		emoj = dict([tuple(reversed(i)) for i in config.NEWS_URLS.items()])[topic][-1]
		markup = types.InlineKeyboardMarkup(inline_keyboard=key_b)
		if ALL_NEWS[topic][article]["img"]:
			await bot.send_photo(
				user_id, photo=ALL_NEWS[topic][article]["img"],
				caption=emoj + ' ' + ALL_NEWS[topic][article]['title'],
				reply_markup=markup)
		else:
			await bot.send_message(user_id, emoj + ' ' + ALL_NEWS[topic][article]['title'], reply_markup=markup)
		BotDB.update_article(user_id, article + 1)
	else:
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
			[
				types.KeyboardButton(text="⬅Назад"),
				types.KeyboardButton(text="Меню↩")]
		])
		await bot.send_message(user_id, "Новости на эту тему закончились", reply_markup=markup)


async def settings_btns(modes):
	if "1" in modes:
		btn_1 = types.InlineKeyboardButton(text='Новости📰   ✅', callback_data="not_mode 1")
	else:
		btn_1 = types.InlineKeyboardButton(text='Новости📰   ❌', callback_data="mode 1")
	if "2" in modes:
		btn_2 = types.InlineKeyboardButton(text='Гороскоп💫  ✅', callback_data="not_mode 2")
	else:
		btn_2 = types.InlineKeyboardButton(text='Гороскоп💫  ❌', callback_data="mode 2")
	if "3" in modes:
		btn_3 = types.InlineKeyboardButton(text='Курсы валют💰   ✅', callback_data="not_mode 3")
	else:
		btn_3 = types.InlineKeyboardButton(text='Курсы валют💰   ❌', callback_data="mode 3")

	markup = types.InlineKeyboardMarkup(inline_keyboard=[
		[btn_1],
		[btn_2],
		[btn_3]
	])

	return markup


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message, state: FSMContext):
	if (message.chat.id,) not in BotDB.get_id():
		await message.answer(
			f'{message.from_user.first_name}, здравствуйте, я новостной бот. Напишите мне день и месяц вашего рождения (через точку), чтобы получать гороскоп')
		if not BotDB.user_exists(message.chat.id):
			BotDB.add_user(
				message.chat.id, "welcome", f'{message.from_user.first_name}',
				message.from_user.username, "pass", '1;2;3')
		else:
			BotDB.update_status(message.chat.id, "welcome")

		await state.set_state(States.WELCOME_STATE[0])

	else:
		await message.answer("Я тебя помню")
		await menu(message, 'Вы в меню')


@dp.message_handler(state=States.WELCOME_STATE)
async def welcome(message: types.Message, state: FSMContext):
	try:
		data = list(map(int, message.text.split(".")))
	except ValueError as e:
		await message.answer("Введены невенрные данные, попробуйте еще раз")
		return
	BotDB.add_birth(message.chat.id, message.text)
	if len(data) == 2 and 0 < data[0] < 32 and 0 < data[1] < 13:
		znak = "Овен"
		if (21 <= data[0] <= 31 and data[1] == 3) or (data[1] == 4 and 1 <= data[0] <= 19):
			znak = zodiac_signs[0]
		elif (20 <= data[0] <= 30 and data[1] == 4) or (data[1] == 5 and 1 <= data[0] <= 20):
			znak = zodiac_signs[1]
		elif (21 <= data[0] <= 31 and data[1] == 5) or (
				data[1] == 6 and 1 <= data[0] <= 21):
			znak = zodiac_signs[2]
		elif (22 <= data[0] <= 30 and data[1] == 6) or (
				data[1] == 7 and 1 <= data[0] <= 22):
			znak = zodiac_signs[3]
		elif (23 <= data[0] <= 31 and data[1] == 7) or (
				data[1] == 8 and 1 <= data[0] <= 22):
			znak = zodiac_signs[4]
		elif (23 <= data[0] <= 31 and data[1] == 8) or (
				data[1] == 9 and 1 <= data[0] <= 22):
			znak = zodiac_signs[5]
		elif (23 <= data[0] <= 30 and data[1] == 9) or (
				data[1] == 10 and 1 <= data[0] <= 23):
			znak = zodiac_signs[6]
		elif (24 <= data[0] <= 31 and data[1] == 10) or (
				data[1] == 11 and 1 <= data[0] <= 22):
			znak = zodiac_signs[7]
		elif (23 <= data[0] <= 30 and data[1] == 11) or (
				data[1] == 12 and 1 <= data[0] <= 21):
			znak = zodiac_signs[8]
		elif (22 <= data[0] <= 31 and data[1] == 12) or (
				data[1] == 1 and 1 <= data[0] <= 20):
			znak = zodiac_signs[9]
		elif (21 <= data[0] <= 31 and data[1] == 1) or (
				data[1] == 2 and 1 <= data[0] <= 18):
			znak = zodiac_signs[10]
		elif (19 <= data[0] <= 29 and data[1] == 2) or (
				data[1] == 3 and 1 <= data[0] <= 20):
			znak = zodiac_signs[11]

		await message.answer(f"А вы знали, что Вы {znak}?")
		BotDB.update_status(message.chat.id, "pass")
		BotDB.update_znak(message.chat.id, znak)
		await menu(
			message,
			"Теперь каждое утро в 8 часов вы будете получать актуальный гороскоп, новости и курс валют.")
		await state.set_state(States.MENU_STATE[0])
	else:
		await message.answer("Введены невенрные данные, попробуйте еще раз")


@dp.message_handler(state=States.MENU_STATE)
async def choosing_in_menu(message: types.Message, state: FSMContext):
	if message.text == 'Инвестиции📈':
		BotDB.update_status(message.chat.id, "invest")

	if message.text == "Гороскопы🪐":
		BotDB.update_status(message.chat.id, "horoscope")
		btn1 = types.KeyboardButton(text=zodiac_signs[0])
		btn2 = types.KeyboardButton(text=zodiac_signs[1])
		btn3 = types.KeyboardButton(text=zodiac_signs[2])
		btn4 = types.KeyboardButton(text=zodiac_signs[3])
		btn5 = types.KeyboardButton(text=zodiac_signs[4])
		btn6 = types.KeyboardButton(text=zodiac_signs[5])
		btn7 = types.KeyboardButton(text=zodiac_signs[6])
		btn8 = types.KeyboardButton(text=zodiac_signs[7])
		btn9 = types.KeyboardButton(text=zodiac_signs[8])
		btn10 = types.KeyboardButton(text=zodiac_signs[9])
		btn11 = types.KeyboardButton(text=zodiac_signs[10])
		btn12 = types.KeyboardButton(text=zodiac_signs[11])
		back = types.KeyboardButton(text="Меню↩")
		kb = [
			[btn1, btn2, btn3, btn4],
			[btn5, btn6, btn7, btn8],
			[btn9, btn10, btn11, btn12],
			[back]
		]
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb)
		await message.answer(
			"Выберите знак зодиака для которого хотите узнать гороскоп",
			reply_markup=markup)
		await state.set_state(States.CHOOSING_HOROSCOPE[0])

	if message.text == "Новости📰":
		BotDB.update_status(message.chat.id, "news")

		home = types.KeyboardButton(text="Меню↩")
		markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[home]])
		await message.answer("Чтобы вернуться, нажмите кнопку меню", reply_markup=markup1)
		kb = [[types.InlineKeyboardButton(text=text, callback_data=url)] for text, url in config.NEWS_URLS.items()]
		markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
		await message.answer("Выберите тему", reply_markup=markup)
		await state.set_state(States.READING_NEWS[0])

	if message.text == "Курсы валют💰":
		home = types.KeyboardButton(text="Меню↩")
		markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[home]])
		await message.answer("Чтобы вернуться, нажмите кнопку меню", reply_markup=markup1)

		BotDB.update_status(message.chat.id, "curr")

		await send_curr(message.chat.id)

		await state.set_state(States.CURRENCY[0])

	if message.text == "Настройки⚙":
		BotDB.update_status(message.chat.id, "settings")
		back = types.KeyboardButton(text="Меню↩")
		markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[back]])
		await message.answer("Чтобы вернуться, нажмите кнопку меню", reply_markup=markup1)
		modes = BotDB.get_modes(message.chat.id)
		if ';' not in modes:
			BotDB.update_modes(message.chat.id, '1;2;3')
			modes = '1;2;3'
		modes = modes.split(';')
		await message.answer("Выберите категории рассылки", reply_markup=await settings_btns(modes))
		await state.set_state(States.SETTINGS[0])


@dp.message_handler(state=States.CHOOSING_HOROSCOPE)
async def choosing_horoscope(message: types.Message, state: FSMContext):
	if message.text == 'Меню↩':
		await menu(message)
	elif message.text in zodiac_signs:
		await message.answer(horoscope.get(config.zodiac_signs_links[message.text])[0])
		for i in horoscope.get(config.zodiac_signs_links[message.text])[1]:
			await message.answer(i.text)
	else:
		await message.answer("Я не понимаю")


@dp.message_handler(state=States.CURRENCY)
async def choosing_curr(message: types.Message, state: FSMContext):
	if message.text == 'Меню↩':
		await menu(message)


@dp.message_handler(state=States.SETTINGS)
async def settings(message: types.Message, state: FSMContext):
	if message.text == 'Меню↩':
		await menu(message)


@dp.callback_query_handler(state=States.SETTINGS)
async def set_mode(callback: types.CallbackQuery, state: FSMContext):
	true_modes = BotDB.get_modes(callback.message.chat.id)
	modes = true_modes.split(';')
	if 'not_mode' in callback.data:
		modes.remove(callback.data.split(' ')[1])
	elif 'mode' in callback.data:
		modes.append(callback.data.split(' ')[1])
	markup = await settings_btns(modes)
	modes = ';'.join(list(set(modes)))
	BotDB.update_modes(callback.message.chat.id, modes)
	await bot.edit_message_reply_markup(
		chat_id=callback.message.chat.id,
		message_id=callback.message.message_id,
		reply_markup=markup
	)


@dp.callback_query_handler(state=States.CURRENCY)
async def curr_(callback: types.CallbackQuery, state: FSMContext):
	if 'curr_' in callback.data:
		builder = InlineKeyboardMarkup()
		curr = currency.get()
		key = callback.data.split('_')[1]
		builder.add(types.InlineKeyboardButton(
			text="Другая валюта",
			callback_data="other_currency")
		)
		await callback.message.answer(
			f"{curr[key]['name']} ({key}): {curr[key]['val']}₽\n",
			reply_markup=builder)
		await bot.delete_message(callback.message.chat.id, callback.message.message_id)
	elif 'other_currency' in callback.data:
		slice_ = (0, 5)
		step = 5
		curr = currency.get()
		keys = sorted(list(curr.keys()), key=lambda x: curr[x]['name'])
		btns = []
		for i in keys[slice_[0]:slice_[1]]:
			btns.append([
				types.InlineKeyboardButton(
					text=f"{curr[i]['name']} ({i})",
					callback_data=f"curr_{i}"),
			])
		btns.append([
			types.InlineKeyboardButton(
				text=f">>",
				callback_data=f"slice_{slice_[0] + step}_{slice_[1] + step}"),
		])
		builder = InlineKeyboardMarkup(inline_keyboard=btns)
		await callback.message.answer(
			"Выберите валюу:",
			reply_markup=builder)
	elif 'slice_' in callback.data:
		slice_ = [
			int(callback.data.split('_')[1]),
			int(callback.data.split('_')[2])
		]
		step = 5
		curr = currency.get()
		keys = sorted(list(curr.keys()), key=lambda x: curr[x]['name'])
		btns = []
		print(slice_)
		for i in keys[slice_[0]:slice_[1]]:
			btns.append([
				types.InlineKeyboardButton(
					text=f"{curr[i]['name']} ({i})",
					callback_data=f"curr_{i}"),
			])
		if slice_[0] <= 0:
			row = [
				types.InlineKeyboardButton(
					text=f">>",
					callback_data=f"slice_{slice_[0] + step}_{slice_[1] + step}"),
			]
		elif len(keys) < slice_[1]:
			row = [
				types.InlineKeyboardButton(
					text="<<",
					callback_data=f"slice_{slice_[0] - step}_{slice_[1] - step}")
			]
		else:
			row = [
				types.InlineKeyboardButton(
					text="<<",
					callback_data=f"slice_{slice_[0] - step}_{slice_[1] - step}"),
				types.InlineKeyboardButton(
					text=f">>",
					callback_data=f"slice_{slice_[0] + step}_{slice_[1] + step}"),
			]

		btns.append(row)
		builder = InlineKeyboardMarkup(inline_keyboard=btns)
		await bot.edit_message_reply_markup(
			callback.message.chat.id,
			callback.message.message_id,
			reply_markup=builder)


@dp.callback_query_handler(state=States.READING_NEWS)
async def choosing_categories_news(callback: types.CallbackQuery, state: FSMContext):
	if callback.data == 'skip':
		await send_news(
			callback.message.chat.id,
			BotDB.get_topic(callback.message.chat.id),
			BotDB.get_article(callback.message.chat.id))
	else:
		BotDB.update_topic(callback.message.from_user.id, callback.data)
		markup = types.ReplyKeyboardMarkup(
			resize_keyboard=True, keyboard=[
				[
					types.KeyboardButton(text="⬅Назад"),
					types.KeyboardButton(text="Меню↩")]
			]
		)
		await callback.message.answer("Нажмите 'назад', чтобы сменить тему", reply_markup=markup)
		BotDB.update_article(callback.message.chat.id, 0)
		BotDB.update_topic(callback.message.chat.id, callback.data)
		await send_news(callback.message.chat.id, callback.data, 0)
		await bot.delete_message(callback.message.chat.id, callback.message.message_id)


@dp.message_handler(state=States.READING_NEWS)
async def reading_news(message: types.Message, state: FSMContext):
	if message.text == "⬅Назад":
		message1 = message
		message1.text = 'Новости📰'
		await choosing_in_menu(message1, state)
	elif message.text == "Меню↩":
		await menu(message)


@dp.message_handler()
async def all_cmd(message: types.Message, state: FSMContext):
	states = {
		'welcome': (States.WELCOME_STATE[0], welcome),
		'menu': (States.MENU_STATE[0], choosing_in_menu),
		'horoscope': (States.CHOOSING_HOROSCOPE[0], choosing_horoscope),
		'curr': (States.CURRENCY[0], choosing_curr),
		'news': (States.READING_NEWS[0], reading_news),
		'settings': (States.SETTINGS[0], settings)
	}
	st = states[BotDB.get_status(message.chat.id)]
	await state.set_state(st[0])
	await st[1](message, state)


def save_all():
	t1 = Thread(target=save_news)
	t1.start()


def save_news():
	global ALL_NEWS
	data = news.save_all_news()
	if data:
		ALL_NEWS = data
	else:
		with open('data/news_data.json', encoding='utf-8') as json_file:
			ALL_NEWS = json.load(json_file)


async def work():
	while True:
		await start_mailing()
		run_pending()
		await asyncio.sleep(30)


def thread_func(func):
	t = Thread(target=func)
	t.start()


# Запуск процесса поллинга новых апдейтов
async def main():
	save_all()
	every(10).minutes.do(save_all)


	tasks = [
		asyncio.create_task(dp.start_polling(bot)),
		asyncio.create_task(work())
	]
	await asyncio.gather(*tasks)

if __name__ == "__main__":
	if os.name == 'nt':
		asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
	asyncio.run(main())
