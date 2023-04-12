from aiogram.utils.helper import Helper, HelperMode, ListItem


class States(Helper):
    mode = HelperMode.snake_case

    WELCOME_STATE = ListItem()
    MENU_STATE = ListItem()
    CHOOSING_HOROSCOPE = ListItem()
    CURRENCY = ListItem()
    READING_NEWS = ListItem()
    SETTINGS = ListItem()
    MAIL_SETTINGS = ListItem()
    PERS_CURR_SETTINGS = ListItem()
    STOCKS_CASE = ListItem()
    SEARCH_STOCKS = ListItem()



if __name__ == '__main__':
    print(States.all())