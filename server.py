from aiogram import Bot, Dispatcher, executor, types
from googletrans import Translator
import langid
import sqlite3
import io
from random import choice, randint
from autocorrect import Speller
import os

translator = Translator()
lang = "en"
spell = Speller(lang=lang)

API_TOKEN = "6109867662:AAFWPic6p4BzRLWYoIZ8h9ELS_RlmYVFokE"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

con = sqlite3.connect("eng_bot_db.sqlite3")
cur = con.cursor()

create_users = "INSERT INTO users(username) VALUES(?);" 
writting_type = ""
words_c = 0
correct = 0
choose = "Обычный"
words_for_test = []
test_word = ""
language = "Английский"
help_message = """/tranlator_mode - режим переводчика\nвы вводите мне слово, а я его перевожу.
/add_words - добавляет введенные вами слова в ваш личный словарь.
/print_dict - печатает весь ваш словарь.
/delete - удалить ненужные вам слова из словаря
/choose_learn - выбор сложности диктанта
/start_learning - диктант (будьте готовы, диктант начнется сразу после того, как вы введете команду)
/stop - выходит из текущего режима
/choose_language - выбор языка диктанта"""


def get_from_db(col, table, param_1, param_2, need_1, need_2):
    return cur.execute(f"SELECT {col} FROM {table} WHERE {param_1} = ? AND {param_2} = ?", (need_1, need_2)).fetchone()[0]


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    user_in = str(message.from_user.id)
    users_data = [x[0] for x in cur.execute("SELECT username FROM users").fetchall()]
    if user_in in users_data:
        await message.answer(f"Здравствуйте {message.from_user.full_name}!\nРады видеть вас снова!\nНажмите /help, чтобы вспомнить, что я могу")
    else:
        await message.answer(f"Здравствуйте {message.from_user.full_name}!\nВидимо вы новенький!\nНажмите /help, чтобы вспомнить, что я могу")
        user_in = [user_in]
        cur.execute(create_users, user_in)
        con.commit()
    

@dp.message_handler(commands=["help"])
async def help_massage(message: types.Message):
    global help_message
    await message.answer(f"Вот, что я умею:\n{help_message}")


@dp.message_handler(commands=["tranlator_mode"])
async def tranlator_mode(message: types.Message):
    global writting_type
    if writting_type != "translate":
        writting_type = "translate"
        await message.answer(f"Ваш режим переключен на переводчик\nПишите мне слова, а я их переведу")
    else:
        await message.answer(f"Вы и так находитесь в режиме перводчика")


@dp.message_handler(commands=["add_words"])
async def add_words(message: types.Message):
    global writting_type
    if writting_type != "add":
        writting_type = "add"
        await message.answer(f"Пишите мне слова, а я добавлю их в ваш личный словарь")
    else:
        await message.answer(f"Вы и так находитесь в режиме добавления слов в словарь")


@dp.message_handler(content_types=[types.ContentType.DOCUMENT])
async def doc_handler(message: types.Message):
    #json_file = await bot.get_file (message.document.open())
    #f = open(message.document.text, "r")

    #print(f.read(30))

    #json_file = await bot.get_file (message.document.file_id.file_path)
    #print(json_file)

    
    await message.document.download()


    
    file_info = await bot.get_file (message.document.file_id)
    print(file_info["file_path"])
    file_path = file_info["file_path"]
    with open(file_path, "r") as file:
        words = [word.rstrip() for word in file]
    for word in words:
        print(word)
        try:
            scr = langid.classify(word)[0]
            if scr == "en" or scr == "de" or scr == "uk":
                ans = translator.translate(word, src="en", dest="ru").text
            else:
                ans = translator.translate(word, src="ru", dest="en").text
            user_in = message.from_user.id
            if scr == "en" or scr == "de" or scr == "uk":
                user_words = [x[0] for x in cur.execute(f"SELECT en_word FROM words WHERE userid = {message.from_user.id}").fetchall()]
                if word not in user_words:
                    cur.execute("INSERT INTO words(userid, en_word, ru_word) VALUES(?, ?, ?);", (user_in, word, ans,))
                    con.commit()
            else:
                user_words = [x[0] for x in cur.execute(f"SELECT en_word FROM words WHERE userid = {message.from_user.id}").fetchall()]
                if ans.text not in user_words:
                    cur.execute("INSERT INTO words(userid, en_word, ru_word) VALUES(?, ?, ?);", (user_in, ans.text, word,))
                    con.commit()
            os.remove(file_path)
        except Exception:
            pass



@dp.message_handler(commands=["print_dict"])
async def print_dict(message: types.Message):
    global writting_type
    if writting_type != 'learning':
        p_dictianory = "Ваш словарь:\n"
        user_words = [x[0] for x in cur.execute(f"SELECT en_word FROM words WHERE userid = {message.from_user.id}").fetchall()]
        for word in sorted(user_words):
            word_cor_count = cur.execute(f"SELECT correct FROM words WHERE userid = ? AND en_word = ?", (message.from_user.id, word)).fetchone()[0]
            word_count = cur.execute(f"SELECT count FROM words WHERE userid = ? AND en_word = ?", (message.from_user.id, word)).fetchone()[0]
            ru_w = translator.translate(str(word), src="en", dest="ru").text
            if word_count != 0:
                p_dictianory = p_dictianory + word + " - " + ru_w + " " + str(int((word_cor_count / word_count) * 100)) + "%" + "\n"
            else:
                p_dictianory = p_dictianory + word + " - " + ru_w + "\n"
        await message.answer(p_dictianory)
    else:
        await message.answer("Вы не можете посмотреть свой словарь, пока не завершите диктант")


@dp.message_handler(commands=["delete"])
async def delete(message: types.Message):
    global writting_type
    if writting_type != "delete":
        writting_type = "delete"
        await message.answer(f"Ваш режим переключен на удаление\nПишите мне слова, а я удалю их из вашего словаря")
    else:
        await message.answer(f"Вы и так находитесь в режиме удаления слов из словаря")


@dp.message_handler(commands=["choose_learn"])
async def choose_learn(message: types.Message):
    global writting_type, choose
    writting_type = "choose"
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Обычный", "Продвинутый"]
    keyboard.add(*buttons)
    await message.answer(f"Выберете режим диктанта\nСейчас выбран {choose}", reply_markup=keyboard)


@dp.message_handler(commands=["choose_language"])
async def choose_language(message: types.Message):
    global writting_type, language
    writting_type = "choose_language"
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Английский", "Русский"]
    keyboard.add(*buttons)
    await message.answer(f"Выберете зык диктанта\nСейчас выбран {language}", reply_markup=keyboard)


@dp.message_handler(commands=["start_learning"])
async def learning(message: types.Message):
    global writting_type, words_for_test, test_word, choose
    if writting_type != "learning":
        if language == "Английский":
            word_ru_en = "en_word"
            src = "en"
            dest = "ru"
        elif language == "Русский":
            word_ru_en = "ru_word"
            src = "ru"
            dest = "en"
        words_for_test = [x[0] for x in cur.execute(f"SELECT {word_ru_en} FROM words WHERE userid = {message.from_user.id}").fetchall()]
        if len(words_for_test) >= 10:
            if choose == "Обычный":
                writting_type = "learning"
                await message.answer("Готовы к диктанту?")
                test_word = choice(words_for_test)
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                correct = translator.translate(test_word, src=src, dest=dest).text
                buttons = ["", "", ""]
                corr_place = randint(0, 2)
                buttons[corr_place] = correct
                for i in range(3):
                    if buttons[i] == "":
                        incorr = choice(words_for_test)
                        if incorr not in buttons:
                            buttons[i] = translator.translate(incorr, src=src, dest=dest).text
                        else:
                            incorr = choice(words_for_test)
                            buttons[i] = translator.translate(incorr, src=src, dest=dest).text
                keyboard.add(*buttons)
                await message.answer(str(test_word), reply_markup=keyboard)
            else:
                writting_type = "learning"
                await message.answer("Готовы к диктанту?")
                test_word = choice(words_for_test)
                await message.answer(str(test_word))
        else:
            await message.answer("Добавьте еще слов в словарь, чтобы начать диктант")
    else:
        await message.answer("Диктант уже идет")


@dp.message_handler(commands=["stop"])
async def stop(message: types.Message):
    global writting_type, words_c, correct, help_message
    if writting_type == "learning":
        words_c = 0
        correct = 0
        writting_type = ""
        await message.answer(f"Диктант окончен")
    elif writting_type == "translate":
        writting_type = ""
        await message.answer(f"Вы вышли из режима перевода")
    elif writting_type == "add":
        writting_type = ""
        await message.answer(f"Вы больше не добавляете слова в словарь")
    elif writting_type == "delete":
        writting_type = ""
        await message.answer(f"Вы больше не удаляете слова из словаря")
    else:
        writting_type = ""
        await message.answer(f"Вы находитесь в режиме по-умочанию\nВыберите один из режимов работы\n{help_message}")


@dp.message_handler()
async def message_work(message: types.Message):
    global writting_type, words_c, correct, choose, words_for_test, test_word, help_message, language, lang
    if writting_type == "translate":
        try:
            scr = langid.classify(message.text)[0]
            print(scr)
            if scr == "en" or scr == "de" or scr == "uk" or scr == "it":
                lang = "en"
                if spell(message.text) == message.text:
                    ans = translator.translate(message.text, src="en", dest="ru").text
                else:
                    ans = f"Вы ошиблись в написании слова\nВозможно вы имели в виду: {spell(message.text)}"
            else:
                lang = "ru"
                if spell(message.text) == message.text:
                    ans = translator.translate(message.text, src="ru", dest="en").text
                else:
                    ans = f"Вы ошиблись в написании слова\nВозможно вы имели в виду: {spell(message.text)}"
            user_in = message.from_user.id
            await message.answer(ans)
        except Exception:
            await message.answer("Что то пошло не так")

    elif writting_type == "add":
        try:
            scr = langid.classify(message.text)[0]
            if scr == "en" or scr == "de" or scr == "uk" or scr == "it":
                if spell(message.text) == message.text:
                    lang = "en"
                    ans = translator.translate(message.text, src="en", dest="ru").text
                else:
                    ans = f"Вы ошиблись в написании слова\nВозможно вы имели в виду: {spell(message.text)}"
            else:
                lang = "ru"
                if spell(message.text) == message.text:
                    ans = translator.translate(message.text, src="ru", dest="en").text
                else:
                    ans = f"Вы ошиблись в написании слова\nВозможно вы имели в виду: {spell(message.text)}"
            user_in = message.from_user.id
            if scr == "en" or scr == "de" or scr == "uk" or scr == "it":
                user_words = [x[0] for x in cur.execute(f"SELECT en_word FROM words WHERE userid = {message.from_user.id}").fetchall()]
                if "Вы ошиблись в написании слова" in ans:
                    await message.answer(ans)
                elif message.text not in user_words:
                    cur.execute("INSERT INTO words(userid, en_word, ru_word) VALUES(?, ?, ?);", (user_in, message.text, ans,))
                    con.commit()
                    await message.answer(f"Слово {message.text} было успешно добавлено в ваш словарь!")
                else:
                    await message.answer("Извините, в вашем словаре уже есть это слово!")
            else:
                user_words = [x[0] for x in cur.execute(f"SELECT en_word FROM words WHERE userid = {message.from_user.id}").fetchall()]
                if "Вы ошиблись в написании слова" in ans:
                    await message.answer(ans)
                elif ans not in user_words:
                    cur.execute("INSERT INTO words(userid, en_word, ru_word) VALUES(?, ?, ?);", (user_in, ans, message.text,))
                    con.commit() 
                    await message.answer(f"Слово {message.text} было успешно добавлено в ваш словарь!")
                else:
                    await message.answer("Извините, в вашем словаре уже есть это слово!")
        except Exception:
             await message.answer("Что то пошло не так")

    elif writting_type == "delete":
        try:
            scr = langid.classify(message.text)[0]
            if scr == "en" or scr == "de" or scr == "uk" or scr == "it":
                cur.execute(f"""DELETE FROM words WHERE en_word = ? AND userid = ?""", (message.text, message.from_user.id))
                con.commit()
                await message.answer(f"Слово {message.text} было удалено из вашего словаря")
            else:
                cur.execute(f"""DELETE FROM words WHERE ru_word = ? AND userid = ?""", (message.text, message.from_user.id))
                con.commit()
                await message.answer(f"Слово {message.text} было удалено из вашего словаря")
        except Exception:
            await message.answer("Что то пошло не так, попробуйте еще раз")
    
    elif writting_type == "choose":
        try:
            if message.text == "Обычный":
                choose = "Обычный"
                await message.answer("Сложность диктанта изменена на Обычный")
                writting_type = ""
            elif message.text == "Продвинутый":
                choose = "Продвинутый"
                await message.answer("Сложность диктанта изменена на Продвинутый")
                writting_type = ""
            else:
                await message.answer("Вы где то ошиблись, пожалуйста, перепроверьте свое сообщение")
        except Exception:
            await message.answer("Извините, что то пошло не так")

    elif writting_type == "choose_language":
        try:
            if message.text == "Ангийский":
                language = "Английский"
                await message.answer("Язык диктанта изменен на Английский")
                writting_type = ""
            elif message.text == "Русский":
                language = "Русский"
                await message.answer("Язык диктанта изменен на Русский")
                writting_type = ""
            else:
                await message.answer("Вы где то ошиблись, пожалуйста, перепроверьте свое сообщение")
        except Exception:
            await message.answer("Извините, что то пошло не так")
            
    elif writting_type == "learning":
        try:
            if language == "Английский":
                word_ru_en = "en_word"
                src = "en"
                dest = "ru"
            elif language == "Русский":
                word_ru_en = "ru_word"
                src = "ru"
                dest = "en"
            if choose == 'Обычный':
                word_cor_count = get_from_db("correct", "words", "userid", word_ru_en, message.from_user.id, test_word)
                word_count = get_from_db("count", "words", "userid", word_ru_en, message.from_user.id, test_word)
                
                if message.text == translator.translate(test_word, src=src, dest=dest).text:
                    await message.answer("Верно!")
                    correct += 1
                    word_cor_count += 1
                    cur.execute(f"UPDATE words SET correct = ? WHERE userid = ? AND {word_ru_en} = ?;", (word_cor_count, message.from_user.id, test_word))
                    con.commit()
                else:
                    await message.answer("Неверно")
                words_c += 1
                word_count += 1
                cur.execute(f"UPDATE words SET count = ? WHERE userid = ? AND {word_ru_en} = ?;", (word_count, message.from_user.id, test_word))
                con.commit()
                if words_c >= 10:
                    writting_type = ""
                    await message.answer(f"Диктант завершен\nВы правильно перевели {correct}/10 слов")
                    words_c = 0
                    correct = 0
                else:
                    test_word = choice(words_for_test)
                    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    corr = translator.translate(test_word, src=src, dest=dest).text
                    buttons = ["", "", ""]
                    corr_place = randint(0, 2)
                    buttons[corr_place] = corr
                    for i in range(3):
                        if buttons[i] == "":
                            incorr = choice(words_for_test)
                            if incorr not in buttons:
                                buttons[i] = translator.translate(incorr, src=src, dest=dest).text
                            else:
                                incorr = choice(words_for_test)
                            buttons[i] = translator.translate(incorr, src=src, dest=dest).text
                    keyboard.add(*buttons)
                    await message.answer(str(test_word), reply_markup=keyboard)
            else:
                if message.text == translator.translate(test_word, src=src, dest=dest).text:
                    await message.answer("Верно!")
                    correct += 1
                else:
                    await message.answer("Неверно")
                words_count += 1
                if words_count >= 10:
                    writting_type = ""
                    await message.answer(f"Диктант завершен\nВы правильно перевели {correct}/10 слов")
                    words_count = 0
                    correct = 0
                else:
                    test_word = choice(words_for_test)
                    await message.answer(str(test_word))
        except Exception:
            await message.answer("Извините, что то пошло не так")
            
    else:
        await message.answer(f"Выберите режим работы\n{help_message}")


if __name__ == "__main__":
   executor.start_polling(dp, skip_updates=True)
