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
import aiogram.utils.markdown as fmt
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

bot = Bot(token=config.REALISE_TOKEN, parse_mode=types.ParseMode.HTML)
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
	curr_list = await BotDB.get_curr(user_id)
	curr_list = [i for i in curr_list.split(';') if i]
	msg_text = ''
	if curr_list:
		for i in curr_list:
			msg_text += f"<b>{curr[i]['name']} ({i})</b>:\t{curr[i]['val']}₽\n\n"
	else:
		msg_text = 'У вас нет избранных валют. Вы можете выбрать их в настройках'
	await bot.send_message(
		user_id,
		msg_text,
		reply_markup=builder)


async def birthday(user_id):
	day = str(int(datetime.date.today().strftime('%d')))
	month = str(int(datetime.date.today().strftime('%m')))
	data = '.'.join([day, month])
	if await BotDB.get_birth(user_id) == data:
		await bot.send_message(
			user_id,
			"Дорогой пользователь, поздравляю Вас с днем рождения, спасибо, что Вы с нами!🥳")


async def menu(message, text='Вы в меню'):
	state = dp.current_state(user=message.from_user.id)
	await BotDB.update_status(message.from_user.id, "menu")
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
		true_modes = await BotDB.get_modes(user_id)
		modes = true_modes.split(';')
		if modes:
			await bot.send_message(user_id, "Утренние новости☕️📰:")
			if '2' in modes:
				try:
					znak = await BotDB.get_znak(user_id)
					if znak in config.zodiac_signs_links:
						await bot.send_message(user_id, horoscope.get(config.zodiac_signs_links[znak])[0])
						for j in horoscope.get(config.zodiac_signs_links[znak])[1]:
							await bot.send_message(user_id, j.text)
					else:
						await bot.send_message(
							user_id,
							"Вы не указали вашу дату рождения для гороскопа, чтобы указать ее введите /age")
				except Exception as e:
					logging.warning(f"не удалось отправить гороскоп пользователю {user_id} | {e}")
			if '3' in modes:
				try:
					await send_curr(user_id, btn=False)
				except Exception as e:
					logging.warning(f"не удалось отправить валюты пользователю {user_id} | {e}")

			if '1' in modes:
				try:
					for num in range(len(ALL_NEWS['https://dzen.ru/news'][:6])):
						await send_news(user_id, 'https://dzen.ru/news', num, skip_btn=False)
				except Exception as e:
					logging.warning(f"не удалось отправить новости пользователю {user_id} | {e}")
	except exceptions.BotBlocked:
		logging.warning(f"Bot blocked by user {user_id}")
	except exceptions.ChatNotFound:
		logging.warning(f"Chat not found {user_id}")
	except exceptions.UserDeactivated:
		logging.warning(f"User {user_id} is deactivated")
	except exceptions.TelegramAPIError:
		logging.warning("Telegram API error occurred")
	except Exception as e:
		logging.warning(f"Error occurred: {e}")


async def start_mailing(start=False):
	now = datetime.datetime.now().time().replace(microsecond=0, second=0)

	if now == config.SEND_TIME or start:
		logging.info('start mailing')
		tasks = []
		for user_id, in await BotDB.get_id():
			tasks.append(asyncio.create_task(send_mail(user_id)))
		await asyncio.gather(*tasks)


async def send_news(user_id, topic, article, skip_btn=True):
	if topic in ALL_NEWS and article < len(ALL_NEWS[topic]) - 1 and len(ALL_NEWS[topic]) > 0:
		skip = types.InlineKeyboardButton(text="Дальше", callback_data="skip")
		det = types.InlineKeyboardButton(text='Подробнее', url=shorten_url(ALL_NEWS[topic][article]['url']))
		key_b = [[skip, det]] if skip_btn else [[det]]

		emoj = config.REV_NEWS_URLS[topic][-1]
		markup = types.InlineKeyboardMarkup(inline_keyboard=key_b)
		await bot.send_message(
			user_id,
			f"{fmt.hide_link(shorten_url(ALL_NEWS[topic][article]['url']))}",
			parse_mode=types.ParseMode.HTML,
			reply_markup=markup
		)
		# Другой формат отправки новостей!!!!
		# if ALL_NEWS[topic][article]["img"]:
		# 	await bot.send_photo(
		# 		user_id, photo=ALL_NEWS[topic][article]["img"],
		# 		caption=emoj + ' ' + ALL_NEWS[topic][article]['title'],
		# 		reply_markup=markup, parse_mode=types.ParseMode.HTML)
		# else:
		# 	await bot.send_message(user_id, emoj + ' ' + ALL_NEWS[topic][article]['title'], reply_markup=markup)
		await BotDB.update_article(user_id, article + 1)
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


@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):

	if (message.chat.id,) not in await BotDB.get_id():
		await message.answer(
			f'{message.from_user.first_name}, здравствуйте, я новостной бот. Напишите мне день и месяц вашего рождения (через точку), чтобы получать гороскоп')
		if not await BotDB.user_exists(message.chat.id):
			await BotDB.add_user(
				message.chat.id,
				"welcome",
				f'{message.from_user.first_name}',
				message.from_user.username,
				"pass",
				'1;2;3',
				'USD;EUR'
			)
		else:
			await BotDB.update_status(message.chat.id, "welcome")

		await state.set_state(States.WELCOME_STATE[0])

	else:
		await message.answer("Я тебя помню, если хочешь изменить дату рождения, введи команду /age")
		await menu(message, 'Вы в меню')


@dp.message_handler(commands=['age'], state='*')
async def age(message: types.Message, state: FSMContext):
	await message.answer(
		f'{message.from_user.first_name}, Напишите мне день и месяц вашего рождения (через точку), чтобы получать гороскоп')
	if not await BotDB.user_exists(message.chat.id):
		await BotDB.add_user(
			message.chat.id, "welcome", f'{message.from_user.first_name}',
			message.from_user.username, "pass", '1;2;3')
	else:
		await BotDB.update_status(message.chat.id, "welcome")
		await state.set_state(States.WELCOME_STATE[0])


@dp.message_handler(state=States.WELCOME_STATE)
async def welcome(message: types.Message, state: FSMContext):
	try:
		data = list(map(int, message.text.split(".")))
	except ValueError as e:
		await message.answer("Введены невенрные данные, попробуйте еще раз")
		return
	await BotDB.add_birth(message.chat.id, message.text)
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
		await BotDB.update_status(message.chat.id, "pass")
		await BotDB.update_znak(message.chat.id, znak)
		await menu(
			message,
			"Теперь каждое утро в 8 часов вы будете получать актуальный гороскоп, новости и курс валют.")
		await state.set_state(States.MENU_STATE[0])
	else:
		await message.answer("Введены невенрные данные, попробуйте еще раз")


@dp.message_handler(state=States.MENU_STATE)
async def choosing_in_menu(message: types.Message, state: FSMContext):
	if message.text == 'Инвестиции📈':
		await BotDB.update_status(message.chat.id, "invest")

	if message.text == "Гороскопы🪐":
		await BotDB.update_status(message.chat.id, "horoscope")
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
			[btn1, btn2, btn3],
			[btn4, btn5, btn6],
			[btn7, btn8, btn9],
			[btn10, btn11, btn12],
			[back]
		]
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb)
		await message.answer(
			"Выберите знак зодиака для которого хотите узнать гороскоп",
			reply_markup=markup)
		await state.set_state(States.CHOOSING_HOROSCOPE[0])

	if message.text == "Новости📰":
		await BotDB.update_status(message.chat.id, "news")

		home = types.KeyboardButton(text="Меню↩")
		markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[home]])
		await message.answer("Чтобы вернуться, нажмите кнопку меню", reply_markup=markup1)
		slice_ = (0, 8)
		step = 8

		kb = []
		btns = list(config.NEWS_URLS.items())[slice_[0]:slice_[1]]
		for i in range(0, len(btns) - 1, 2):
			kb.append([
				types.InlineKeyboardButton(
					text=btns[i][0],
					callback_data=btns[i][1]),
				types.InlineKeyboardButton(
					text=btns[i + 1][0],
					callback_data=btns[i + 1][1]),
			])
		kb.append([
			types.InlineKeyboardButton(
				text=f">>",
				callback_data=f"slice_{slice_[0] + step}_{slice_[1] + step}"),
		])
		markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
		await message.answer("Выберите тему", reply_markup=markup)
		await state.set_state(States.READING_NEWS[0])

	if message.text == "Курсы валют💰":
		home = types.KeyboardButton(text="Меню↩")
		markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[home]])
		await message.answer("Чтобы вернуться, нажмите кнопку меню", reply_markup=markup1)

		await BotDB.update_status(message.chat.id, "curr")

		await send_curr(message.chat.id)

		await state.set_state(States.CURRENCY[0])

	if message.text == "Настройки⚙":
		sett_btns = [
			[
				types.KeyboardButton(text="Параметры рассылки⏰"),
				types.KeyboardButton(text="Избранные валюты💰"),
			],
			[types.KeyboardButton(text="Меню↩")]
		]
		await BotDB.update_status(message.chat.id, "settings")
		markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=sett_btns)
		await message.answer("Выберите категорию настроек", reply_markup=markup1)
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


@dp.message_handler(state=States.MAIL_SETTINGS + States.PERS_CURR_SETTINGS)
async def back_to_settings(message: types.Message, state: FSMContext):
	if message.text == 'Назад↩':
		message.text = 'Настройки⚙'
		await state.set_state(States.SETTINGS[0])
		await choosing_in_menu(message, state)


@dp.message_handler(state=States.SETTINGS + States.MAIL_SETTINGS)
async def settings(message: types.Message, state: FSMContext):
	if message.text == 'Меню↩':
		await menu(message)
	elif message.text == 'Параметры рассылки⏰':
		markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[types.KeyboardButton(text="Назад↩")]])
		await message.answer(
			"Нажмите 'Назад↩', чтобы вернуться в настройки",
			reply_markup=markup1)
		modes = await BotDB.get_modes(message.chat.id)
		modes = modes.split(';')
		await BotDB.update_status(message.chat.id, "mail_settings")
		await message.answer("Выберите категории рассылки", reply_markup=await settings_btns(modes))
		await state.set_state(States.MAIL_SETTINGS[0])
	elif message.text == 'Избранные валюты💰':
		markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[types.KeyboardButton(text="Назад↩")]])
		await message.answer(
			"Нажмите 'Назад↩', чтобы вернуться в настройки",
			reply_markup=markup1)
		await state.set_state(States.PERS_CURR_SETTINGS[0])
		await BotDB.update_status(message.chat.id, 'pers_curr_settings')
		await other_curr_btns(message.chat.id, from_sett=True)


@dp.callback_query_handler(state=States.PERS_CURR_SETTINGS)
async def set_pers_curr(callback: types.CallbackQuery, state: FSMContext):
	if 'slice_' in callback.data:
		await callback_on_click_slice_curr(callback, from_sett=True)
	elif callback.data.startswith('curr_'):
		new_mark = callback.message.reply_markup
		curr = callback.data.split('_')[1]
		for i in new_mark.inline_keyboard:
			if curr in i[0].callback_data:
				i[0].text = i[0].text + '✅'
				i[0].callback_data = '✅' + i[0].callback_data
		await BotDB.update_curr(
			callback.message.chat.id,
			await BotDB.get_curr(callback.message.chat.id) + ';' + curr
		)
		await bot.edit_message_reply_markup(
			callback.message.chat.id,
			callback.message.message_id,
			reply_markup=new_mark
		)
	elif callback.data.startswith('✅curr_'):
		pers_curr = (await BotDB.get_curr(callback.message.chat.id)).split(';')
		pers_curr.remove(callback.data.split('_')[1])
		new_mark = callback.message.reply_markup
		curr = callback.data.split('_')[1]
		for i in new_mark.inline_keyboard:
			if curr in i[0].callback_data:
				i[0].text = i[0].text[:-1]
				i[0].callback_data = i[0].callback_data[1:]
		await bot.edit_message_reply_markup(
			callback.message.chat.id,
			callback.message.message_id,
			reply_markup=new_mark
		)
		await BotDB.update_curr(
			callback.message.chat.id,
			';'.join(pers_curr)
		)


@dp.callback_query_handler(state=States.MAIL_SETTINGS)
async def set_mode(callback: types.CallbackQuery, state: FSMContext):
	true_modes = await BotDB.get_modes(callback.message.chat.id)
	modes = true_modes.split(';')
	if 'not_mode' in callback.data:
		modes.remove(callback.data.split(' ')[1])
	elif 'mode' in callback.data:
		modes.append(callback.data.split(' ')[1])
	markup = await settings_btns(modes)
	modes = ';'.join(list(set(modes)))
	await BotDB.update_modes(callback.message.chat.id, modes)
	await bot.edit_message_reply_markup(
		chat_id=callback.message.chat.id,
		message_id=callback.message.message_id,
		reply_markup=markup
	)


async def other_curr_btns(user_id, from_sett=False):
	slice_ = (0, 5)
	step = 5
	curr = currency.get()
	keys = sorted(list(curr.keys()), key=lambda x: curr[x]['name'])
	btns = []
	if from_sett:
		pers_curr = (await BotDB.get_curr(user_id)).split(';')
	for i in keys[slice_[0]:slice_[1]]:
		add_s = ''
		if from_sett and i in pers_curr:
			add_s = '✅'
		btns.append([
			types.InlineKeyboardButton(
				text=f"{curr[i]['name']} ({i}){add_s}",
				callback_data=f"{add_s}curr_{i}"),
		])
	btns.append([
		types.InlineKeyboardButton(
			text=f">>",
			callback_data=f"slice_{slice_[0] + step}_{slice_[1] + step}"),
	])
	builder = InlineKeyboardMarkup(inline_keyboard=btns)
	await bot.send_message(
		user_id,
		"Выберите валюу:",
		reply_markup=builder)


async def callback_on_click_slice_curr(callback, from_sett=False):
	slice_ = [
		int(callback.data.split('_')[1]),
		int(callback.data.split('_')[2])
	]
	step = 5
	curr = currency.get()
	keys = sorted(list(curr.keys()), key=lambda x: curr[x]['name'])
	btns = []
	if from_sett:
		pers_curr = (await BotDB.get_curr(callback.message.chat.id)).split(';')
	for i in keys[slice_[0]:slice_[1]]:
		add_s = ''
		if from_sett and i in pers_curr:
			add_s = '✅'
		btns.append([
			types.InlineKeyboardButton(
				text=f"{curr[i]['name']} ({i}){add_s}",
				callback_data=f"{add_s}curr_{i}"),
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


@dp.callback_query_handler(state=States.CURRENCY)
async def curr_(callback: types.CallbackQuery, state: FSMContext, from_sett=False):
	if 'curr_' in callback.data:
		builder = InlineKeyboardMarkup()
		curr = currency.get()
		key = callback.data.split('_')[1]
		builder.add(types.InlineKeyboardButton(
			text="Другая валюта",
			callback_data="other_currency")
		)
		await callback.message.answer(
			f"<b>{curr[key]['name']} ({key})</b>:\t{curr[key]['val']}₽\n\n",
			reply_markup=builder)
		await bot.delete_message(callback.message.chat.id, callback.message.message_id)
	elif 'other_currency' in callback.data or from_sett:
		await other_curr_btns(callback.message.chat.id)
	elif 'slice_' in callback.data:
		await callback_on_click_slice_curr(callback)


@dp.callback_query_handler(state=States.READING_NEWS)
async def choosing_categories_news(callback: types.CallbackQuery, state: FSMContext):
	if callback.data == 'skip':
		await send_news(
			callback.message.chat.id,
			await BotDB.get_topic(callback.message.chat.id),
			await BotDB.get_article(callback.message.chat.id))
	elif callback.data in config.REV_NEWS_URLS:
		await BotDB.update_topic(callback.message.from_user.id, callback.data)
		markup = types.ReplyKeyboardMarkup(
			resize_keyboard=True, keyboard=[
				[
					types.KeyboardButton(text="⬅Назад"),
					types.KeyboardButton(text="Меню↩")]
			]
		)
		await callback.message.answer("Нажмите 'назад', чтобы сменить тему", reply_markup=markup)
		await BotDB.update_article(callback.message.chat.id, 0)
		await BotDB.update_topic(callback.message.chat.id, callback.data)
		await send_news(callback.message.chat.id, callback.data, 0)
		await bot.delete_message(callback.message.chat.id, callback.message.message_id)

	elif 'slice_' in callback.data:
		slice_ = [
			int(callback.data.split('_')[1]),
			int(callback.data.split('_')[2])
		]
		step = 8
		kb = []
		btns = list(config.NEWS_URLS.items())[slice_[0]:slice_[1]]
		for i in range(0, len(btns) - 1, 2):
			kb.append([
				types.InlineKeyboardButton(
					text=btns[i][0],
					callback_data=btns[i][1]),
				types.InlineKeyboardButton(
					text=btns[i + 1][0],
					callback_data=btns[i + 1][1]),
			])
		if slice_[0] <= 0:
			row = [
				types.InlineKeyboardButton(
					text=f">>",
					callback_data=f"slice_{slice_[0] + step}_{slice_[1] + step}"),
			]
		elif len(btns) < slice_[1]:
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

		kb.append(row)
		builder = InlineKeyboardMarkup(inline_keyboard=kb)
		await bot.edit_message_reply_markup(
			callback.message.chat.id,
			callback.message.message_id,
			reply_markup=builder)


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
		'settings': (States.SETTINGS[0], settings),
		'mail_settings': (States.MAIL_SETTINGS[0], back_to_settings),
		'pers_curr_settings': (States.PERS_CURR_SETTINGS[0], back_to_settings)
	}
	st = states[await BotDB.get_status(message.chat.id)]
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
	await start_mailing(start=True)
	await asyncio.gather(*tasks)


if __name__ == "__main__":
	if os.name == 'nt':
		asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
	asyncio.run(main())
