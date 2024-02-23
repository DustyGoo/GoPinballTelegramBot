import json

import telebot
from telebot import types

from configuration import TOKEN

with open("database.json", encoding="utf-8") as db:
    data = json.load(db)
# В файле database.json хранятся все данные по экспонатам в формате
# словарей со значениями
# "name": - название экспоната
# "audioguide": - ссылка на файл с аудиогидом (находится в папке audio)
# "textguide": - описание экспоната
# "videoguide": - ссылка на youtube видео про экспонат

bot = telebot.TeleBot(TOKEN)

guide_selection = {}
# В этом словаре будут отображаться предпочтения пользователя в формате:
# {user_id: {'guide_type': '', 'section_type': ''}}, где guide_type будет
# отображать выбор текст/аудио/видео, а section_type - выбор категории
# экспонатов вступление/пинболы/аркады/неигровые экспонаты. Вот пример:
# {6845820748: {'guide_type': 'Текстовый гид', 'section_type': 'Пинболы'}}

messages = {}


# В этом словаре будут отображаться значения последних нажатых кнопок юзеров.
# Это нужно для проверки на дублирование нажатий. См. функцию check_duplicate


def create_keyboard(buttons: list) -> types.ReplyKeyboardMarkup:
    """
    Универсальная функция создания кнопок в нашем телеграм-боте

    Принимает значение buttons - это список строк, представляющих собой текст
    на кнопках.

    ReplyKeyboardMarkup обозначает, что кнопки будут появляться на месте
    мобильной клавиатуры.
    resize_keyboard=True обозначает способность клавиатуры подстраиваться
    под размер экрана устройства.
    row_width=1 обозначает, что в каждой строке будет лишь по одной кнопке

    Args:
        buttons (list): список строк, представляющих собой текст на кнопках.

    Returns:
        types.ReplyKeyboardMarkup: созданная клавиатура
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(*buttons)
    return keyboard


def check_duplicate(message) -> bool:
    """
    Проверяет, была ли уже обработана кнопка с текстом, указанным в
    сообщении message.

    Тут и далее по коду параметр message отражает сообщения от пользователя,
    которые, в свою очередь, являются текстом с reply-кнопок.

    Возвращает True, если кнопка была уже обработана, иначе - False.

    Args:
        message (telebot.types.Message): сообщение от пользователя

    Returns:
        bool: True, если кнопка была уже обработана, иначе - False.

    """
    chat_id = message.chat.id
    text = message.text

    # Проверка на специальные кнопки, которые могут быть нажаты повторно
    if text in ("<<- Вернуться назад",
                "<<--- Вернуться назад",
                "Вернуться в начало"):
        return False

    # Если для юзера еще нет сохраненного текста, сохраняем текущий текст
    if chat_id not in messages:
        messages[chat_id] = text
        return False

    # Если текст текущей кнопки совпадает с предыдущим сохраненным текстом,
    # то считаем кнопку нажатой дважды
    if text == messages[chat_id]:
        return True

    # Сохраняем текущий текст кнопки для будущего сравнения
    messages[chat_id] = text
    return False


@bot.message_handler(commands=["start"])
def starter(message) -> None:
    """
    Функция запуска бота и вызова главного меню

    Обработчик команды '/start', который инициализирует начало взаимодействия
    пользователя с ботом.
    Если кнопка была нажата повторно, функция завершает свою работу.
    Иначе инициализирует новую сессию пользователя, отправляет приветственное
    сообщение и создает клавиатуру с вариантами выбора типа гида.

    Args:
        message (telebot.types.Message): сообщение от пользователя
    """

    # Тут и далее условие 'if check_duplicate' проверяет не дублируется ли
    # текст нажатой кнопки. Иначе начинается полный бардак.
    if check_duplicate(message):
        return
    chat_id = message.chat.id
    guide_selection[chat_id] = {"guide_type": "", "section_type": ""}

    # Отправка приветственного сообщения и клавиатуры выбора типа гида
    mainkeys = create_keyboard(["Аудиогид", "Текстовый гид", "Видеогид"])
    bot.send_message(chat_id, "Добро пожаловать в <b>Музей Пинбола Go "
                              "Pinball</b>! \n\nВыберите, каким гидом вам "
                              "будет удобнее воспользоваться.",
                     reply_markup=mainkeys, parse_mode='HTML')
    # Регистрация следующего шага взаимодействия пользователя
    bot.register_next_step_handler_by_chat_id(chat_id, section_selection)


@bot.message_handler(content_types=["text"])
def section_selection(message) -> None:
    """
    Обработчик текстовых сообщений, предназначенных для выбора типа гида.

    Обрабатывает выбор типа гида, устанавливает соответствующее значение в
    `guide_selection`, отправляет сообщение с вариантами разделов гида и
    регистрирует следующий шаг взаимодействия. Функция прекращает свою
    работу, когда пользователь нажимает одну из предложенных кнопок.
    """
    if check_duplicate(message):
        return

    chat_id = message.chat.id
    guide_type = message.text
    guide_selection[chat_id]["guide_type"] = guide_type

    # Отправка сообщения с вариантами разделов гида
    if message.text in {"Аудиогид", "Текстовый гид"}:
        sectionkeys = create_keyboard(["Вступление",
                                       "Аркады",
                                       "Неигровые экспонаты",
                                       "Пинболы",
                                       "<<- Вернуться назад"])
        bot.send_message(chat_id, f"Вы выбрали раздел "
                                  f"<b>{guide_type}</b>.\n\nОтлично!"
                                  f"\nТеперь выберите раздел гида.",
                         reply_markup=sectionkeys,
                         parse_mode="HTML")
        bot.register_next_step_handler_by_chat_id(chat_id, section_showpiece)
    elif message.text in {"Видеогид"}:
        videoguide(message)

    # Тут и далее функция text_intrude вызывается при вводе произвольного
    # текста с клавиатуры, а не с заготовленных кнопок
    else:
        text_intrude(message)


@bot.message_handler(content_types=["text"])
def section_showpiece(message) -> None:
    """
    Обработчик текста для выбора раздела гида и предоставления напутствия.

    Функция обрабатывает выбор раздела гида, устанавливает соответствующее
    значение в guide_selection, отправляет сообщение с информацией о разделе,
    регистрирует следующий шаг взаимодействия и завершает свою работу.
    """
    chat_id = message.chat.id
    section_type = message.text
    guide_selection[chat_id]["section_type"] = section_type

    # Отправка сообщения с напутственным сообщением
    if message.text in {"Аркады", "Неигровые экспонаты", "Пинболы"}:
        bot.send_message(chat_id, f'Хотите больше узнать про <b>'
                                  f'{section_type.lower()}</b>?'
                                  f'\n\nХороший выбор!'
                                  f'\nВот все {section_type.lower()} '
                                  f'Музея <b>GoPinball</b>'
                                  f'\nСписок можно (и нужно!) скроллить',
                         parse_mode='HTML')

        # Вызов соответствующей функции для обработки выбранного раздела
        if message.text == "Аркады":
            arcades(message)
        elif message.text == "Неигровые экспонаты":
            npm(message)
        elif message.text == "Пинболы":
            pinballs(message)
    elif message.text == "<<- Вернуться назад":
        guide_selection[chat_id] = {}  # Сброс выбора раздела
        starter(message)  # Возврат в начальное меню
    elif message.text in {"Вступление"}:
        intro(message)
    else:
        text_intrude(message)


@bot.message_handler(content_types=["text"])
def intro(message) -> None:
    """
    Функция-обработчик для предоставления вводных знаний по гиду.

    Отправляет введение к выбранному гиду (аудиогиду или текстовому гиду) и
    регистрирует следующий шаг взаимодействия.
    """
    if check_duplicate(message):
        return

    chat_id = message.chat.id
    backkey = create_keyboard(["<<- Вернуться назад"])
    print(guide_selection)
    # Отправка введения к выбранному виду гида
    for key, value in guide_selection.items():
        if key != chat_id:
            continue
        if value.get("guide_type") == "Аудиогид":
            bot.send_voice(chat_id, voice=open(data[0]["audioguide"], "rb"),
                           reply_markup=backkey)
        elif value.get("guide_type") == "Текстовый гид":
            bot.send_message(chat_id, data[0]["textguide"], parse_mode="HTML",
                             reply_markup=backkey)
    print(guide_selection)
    bot.register_next_step_handler(message, back_to_menu)


@bot.message_handler(content_types=["text"])
def arcades(message) -> None:
    """
    Функция-обработчик для предоставления информаций по разделу "Аркады".

    Когда получает команду "Аркады", выдаёт список Аркадных экспонатов,
    уточняет, о чем рассказать и направляет в функцию выдачи финальной
    информации "final_giver"
    """
    if check_duplicate(message):
        return
    chat_id = message.chat.id

    # Создаём список кнопок, используя генератор списка. Тут и
    # далее опираемся на ключ "type" из файла database.json.
    arcade_buttons = [item["name"] for item in data if
                      item["type"] == "Arcade"]

    # Добавляем кнопку для возвращения в главное меню
    arcade_buttons.append("<<- Вернуться назад")
    arcadekeys = create_keyboard(arcade_buttons)
    bot.send_message(chat_id, 'О какой из аркад вам рассказать?',
                     reply_markup=arcadekeys)
    bot.register_next_step_handler_by_chat_id(chat_id, final_giver)


@bot.message_handler(content_types=["text"])
def npm(message) -> None:
    """
    Функция для предоставления информаций по разделу "Неигровые экспонаты".

    Когда получает команду "Неигровые экспонаты", выдаёт список таких машин,
    выдаёт сообщение и направляет в функцию выдачи финальной информации
    "final_giver"
    """
    if check_duplicate(message):
        return
    chat_id = message.chat.id

    npa_buttons = [item["name"] for item in data if
                   item["type"] == "NPA"]
    npa_buttons.append("<<- Вернуться назад")
    npakeys = create_keyboard(npa_buttons)
    bot.send_message(chat_id, 'В <b>GoPinball</b> можно поиграть не на '
                              'всех автоматах.\nНекоторые из экспонатов '
                              'находятся в специальном музейном уголке.'
                              '\n\nО каком из них вам рассказать?',
                     parse_mode='HTML', reply_markup=npakeys)
    bot.register_next_step_handler_by_chat_id(chat_id, final_giver)


@bot.message_handler(content_types=["text"])
def pinballs(message) -> None:
    """
    Функция-обработчик для предоставления информаций по разделу "Пинболы".

    Когда получает команду "Пинболы", выдаёт список Пинболов, добавляет
    кнопку "Назад", сообщение и направляет в функцию выдачи финальной
    информации "final_giver"
    """
    if check_duplicate(message):
        return
    chat_id = message.chat.id

    pinball_buttons = [item["name"] for item in data if
                       item["type"] == "Pinball"]
    pinball_buttons.append("<<- Вернуться назад")
    pinballkeys = create_keyboard(pinball_buttons)
    bot.send_message(chat_id, 'Гордость музея <b>GoPinball</b> - это '
                              'крупнейшая в России коллекция пинболов, '
                              'доступных каждому гостю!'
                              '\n\nО каком из пинболов вам рассказать?',
                     parse_mode='HTML', reply_markup=pinballkeys)
    bot.register_next_step_handler_by_chat_id(chat_id, final_giver)


@bot.message_handler(content_types=["text"])
def videoguide(message) -> None:
    """
    Функция для предоставления информаций по Видеогиду.

    Когда получает команду "Видеогид", выдаёт список экспонатов,для которых
    сняты видеоролики, добавляет кнопку "Назад", сообщение и направляет в
    функцию выдачи финальной информации "final_giver"
    """
    chat_id = message.chat.id

    # Создаём список кнопок, вызывая только те поля 'videoguide', значение
    # которых не равно none. Во всех остальных - ссылки на видеоролики.
    video_buttons = [item['name'] for item in data if item['videoguide'] !=
                     'none']
    video_buttons.append("<<- Вернуться назад")
    videokeys = create_keyboard(video_buttons)
    bot.send_message(chat_id, 'Для youtube-канала Музея <b>GoPinball</b>'
                              ' мы снимаем ролики с разбором правил, '
                              'техник игры в пинбол и другим контентом.'
                              '\n\nПодписывайтесь: youtube.com/@pinballmuseum'
                              '\n\nА вот наши видеообзоры:',
                     parse_mode='HTML', reply_markup=videokeys)
    bot.register_next_step_handler_by_chat_id(chat_id, final_giver)


@bot.message_handler(content_types=["text"])
def final_giver(message) -> None:
    """
    Обработчик для завершающего этапа взаимодействия с пользователем
    после выбора аркады, пинбола или другого контента.


    Действия:
    - Обращение к check_duplicate проверяет, было ли сообщение принято ранее
    - Создает клавиатуру с кнопкой '<<--- Вернуться назад'.
    - Если пользователь выбрал '<<- Вернуться назад' в предыдущей выдаче
    кнопок, final_giver вызывает функцию back_to_menu и завершает выполнение.
    - Ищет в данных контент, для выбранного пользователем экспоната.
    - Отправляет пользователю соответствующий контент из database.json в
    зависимости от выбранного типа гида (текстовый, аудио, видео).
    - Регистрирует следующий шаг взаимодействия, указывая, что после
    завершения этапа и нажатия '<<--- Вернуться назад' нужно вызвать
    функцию back_to_menu.
    """
    if check_duplicate(message):
        return

    chat_id = message.chat.id
    returnkey = create_keyboard(["<<--- Вернуться назад"])

    if message.text == "<<- Вернуться назад":
        back_to_menu(message)
        return

    for item in data:
        if item["name"] == message.text:
            for key, value in guide_selection.items():
                if key == chat_id:
                    if value.get("guide_type") == "Текстовый гид":
                        bot.send_message(chat_id,
                                         f"<b>{item['name']}</b>"
                                         f"\n\n\n{item['textguide']}",
                                         reply_markup=returnkey,
                                         parse_mode='HTML')
                    elif value.get("guide_type") == "Аудиогид":
                        bot.send_voice(chat_id,
                                       voice=open(item['audioguide'], 'rb'),
                                       reply_markup=returnkey)
                    elif value.get("guide_type") == "Видеогид":
                        bot.send_message(chat_id,
                                         f"<b>{item['name']}</b>"
                                         f"\n\n{item['videoguide']}",
                                         reply_markup=returnkey,
                                         parse_mode='HTML')
    bot.register_next_step_handler_by_chat_id(chat_id, back_to_menu)


@bot.message_handler(content_types=["text"])
def text_intrude(message) -> None:
    """
    Обработчик для сообщений, не соответствующих логике бота.

    Получая такое сообщение эта функция выносит предупреждение и с помощью
    кнопки 'Вернуться в начало' предлагает вернуться в стартовое меню,
    попутно очищая словарь guide_selection для активного пользователя
    """
    chat_id = message.chat.id
    guide_selection[chat_id] = {}
    backkey = create_keyboard(["Вернуться в начало"])
    bot.send_message(chat_id, 'Для навигации по боту пользуйтесь '
                              'кнопками. Бот не запрограммирован на '
                              'другой текст.', reply_markup=backkey)
    starter(message)


@bot.message_handler(content_types=["text"])
def back_to_menu(message) -> None:
    """
    Обработчик для возврата пользователя в главное меню или предыдущий раздел.

    Действия:
    - check_duplicate проверяет, не было ли сообщение обработано ранее
    - Если сообщение содержит текст '<<- Вернуться назад', очищает данные о
    выборе пользователя и вызывает функцию starter, возвращая юзера в начало.
    - Если сообщение содержит текст '<<--- Вернуться назад', то функция
    определяет тип гида и предыдущий раздел и, в зависимости от ранее
    сделанного выбора, вызывает соответствующую функцию (arcades, npm,
    pinballs, videoguide), чтобы пользователь мог выбрать другой экспонат.
    - В случае неверного ввода вызывает функцию text_intrude.
    """
    if check_duplicate(message):
        return

    chat_id = message.chat.id

    if message.text == "<<- Вернуться назад":
        guide_selection[chat_id] = {}
        starter(message)
        return

    if message.text != "<<--- Вернуться назад":
        text_intrude(message)
        return

    for key, value in guide_selection.items():
        if key == chat_id:
            same = value.get("guide_type")
            if value.get("section_type") == "Аркады":
                guide_selection[chat_id] = {'guide_type': same,
                                            'section_type': 'Аркады'}
                arcades(message)
            elif value.get("section_type") == "Неигровые экспонаты":
                guide_selection[chat_id] = {'guide_type': same,
                                            'section_type':
                                                'Неигровые экспонаты'}
                npm(message)
            elif value.get("section_type") == "Пинболы":
                guide_selection[chat_id] = {'guide_type': same,
                                            'section_type': 'Пинболы'}
                pinballs(message)
            elif value.get("guide_type") == "Видеогид":
                guide_selection[chat_id] = {'guide_type': 'Видеогид',
                                            'section_type': ''}
                videoguide(message)


if __name__ == "__main__":
    print("Бот запущен!")
    while True:
        try:
            bot.polling(none_stop=True)
        except:
            pass
