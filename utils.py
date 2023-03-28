from aiogram.utils.helper import Helper, HelperMode, ListItem


class States(Helper):
    mode = HelperMode.snake_case

    WELCOME_STATE = ListItem()
    MENU_STATE = ListItem()
    CHOOSING_HOROSCOPE = ListItem()
    TEST_STATE_3 = ListItem()
    TEST_STATE_4 = ListItem()
    TEST_STATE_5 = ListItem()


if __name__ == '__main__':
    print(States.all()[0] == States.MENU_STATE[0])