from logic import DB_Manager
from config import *
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types

# Используем единое имя базы данных
DATABASE = "port.db" 

bot = TeleBot("YOUR_TOKEN")
hideBoard = types.ReplyKeyboardRemove() 

cancel_button = "Отмена 🚫"

def cansel(message):
    bot.send_message(message.chat.id, "Действие отменено! 📋 Чтобы посмотреть команды, используй — /info", reply_markup=hideBoard)
  
def no_projects(message):
    bot.send_message(message.chat.id, '📭 У тебя пока нет добавленных проектов!\nМожешь создать свой первый проект с помощью команды /new_project ✨')

def gen_inline_markup(rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(f"🔎 {row}", callback_data=row))
    return markup

def gen_markup(rows):
    # ЗАДАНИЕ 1: Настройка одноразовой и компактной reply-клавиатуры
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup

# ЗАДАНИЕ 3: Стилизация атрибутов для красивого вывода при обновлении
attributes_of_projects = {
    'Имя проекта 📝' : ["✏️ Введите новое имя проекта:", "project_name"],
    'Описание 📖' : ["✏️ Введите новое описание проекта:", "description"],
    'Ссылка 🔗' : ["✏️ Введите новую ссылку на проект:", "url"],
    'Статус ⚙️' : ["⚙️ Выберите новый статус задачи из списка:", "status_id"]
}

def info_project(message, user_id, project_name):
    # ЗАДАНИЕ 3: Красивый вывод карточки проекта
    info = manager.get_project_info(user_id, project_name)[0]
    skills = manager.get_project_skills(project_name)
    if not skills:
        skills = 'Навыки пока не добавлены 🔍'
        
    card = f"""
📁 *Проект:* {info[0]}
──────────────────
ℹ️ *Описание:* {info[1] if info[1] else 'Отсутствует 📋'}
🔗 *Ссылка:* {info[2]}
⚡ *Статус:* {info[3]}
🛠️ *Технологии:* {skills}
──────────────────
"""
    bot.send_message(message.chat.id, card, parse_mode="Markdown", reply_markup=hideBoard)

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, """👋 Привет! Я твой персональный **Менеджер проектов**.
🚀 Помогу тебе структурировать портфолио, сохранять ссылки, отмечать статусы разработки и привязывать стек технологий к каждому кейсу!
""")
    info(message)
    
@bot.message_handler(commands=['info'])
def info(message):
    # ЗАДАНИЕ 2 & 3: Подробное и красивое описание всех команд
    help_text = """
🛠️ *Доступные команды помощника:*

➕ /newproject — Добавить новый проект в портфолио.
🗂️ /projects — Посмотреть список всех твоих проектов.
🎒 /skills — Привязать ключевые навыки и технологии к проекту.
🔄 /updateprojects — Редактировать информацию (изменить имя, ссылку, описание или статус).
❌ /delete — Навсегда удалить проект из базы данных.
ℹ️ /info — Вызвать эту справку по командам.

💡 *Лайфхак:* Ты можешь просто написать мне в чат **название своего проекта**, и я тут же пришлю всю информацию о нем!
"""
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")
    

@bot.message_handler(commands=['newproject'])
def addtask_command(message):
    bot.send_message(message.chat.id, "📝 Введите название проекта:")
    bot.register_next_step_handler(message, name_project)

def name_project(message):
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "🔗 Введите ссылку на проект (или напишите 'Нет'):")
    bot.register_next_step_handler(message, link_project, data=data)

def link_project(message, data):
    data.append(message.text)
    statuses = [x[0] for x in manager.get_statuses()] 
    bot.send_message(message.chat.id, "⚙️ Выберите текущий статус проекта:", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)

def callback_project(message, data, statuses):
    status = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if status not in statuses:
        bot.send_message(message.chat.id, "⚠️ Вы выбрали статус не из списка! Пожалуйста, используйте кнопки:", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return
    status_id = manager.get_status_id(status)
    data.append(status_id)
    manager.insert_project([tuple(data)])
    bot.send_message(message.chat.id, "🎉 Проект успешно сохранен в портфолио!", reply_markup=hideBoard)


@bot.message_handler(commands=['skills'])
def skill_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, '📁 Выберите проект, для которого нужно указать навык:', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)


def skill_project(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
        
    if project_name not in projects:
        bot.send_message(message.chat.id, '⚠️ Такого проекта не найдено. Выберите из списка:', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        skills = [x[1] for x in manager.get_skills()]
        bot.send_message(message.chat.id, '🛠️ Выберите технологию/навык:', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)

def set_skill(message, project_name, skills):
    skill = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cansel(message)
        return
        
    if skill not in skills:
        bot.send_message(message.chat.id, '⚠️ Пожалуйста, выберите навык, используя клавиатуру:', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    manager.insert_skill(user_id, project_name, skill)
    bot.send_message(message.chat.id, f'✅ Навык *{skill}* успешно добавлен к проекту *{project_name}*!', parse_mode="Markdown", reply_markup=hideBoard)


@bot.message_handler(commands=['projects'])
def get_projects_command(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "📋 *Список твоих проектов:*\n_Нажми на кнопку ниже, чтобы узнать подробности_"
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=gen_inline_markup([x[2] for x in projects]))
    else:
        no_projects(message)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    project_name = call.data
    info_project(call.message, call.from_user.id, project_name)
    bot.answer_callback_query(call.id) # Убирает вечную загрузку на инлайн кнопке


@bot.message_handler(commands=['delete'])
def delete_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects_names = [x[2] for x in projects]
        bot.send_message(message.chat.id, "🗑️ Выберите проект, который вы хотите **навсегда удалить**:", parse_mode="Markdown", reply_markup=gen_markup(projects_names))
        bot.register_next_step_handler(message, delete_project_step, projects=projects_names)
    else:
        no_projects(message)

def delete_project_step(message, projects):
    project = message.text
    user_id = message.from_user.id

    if message.text == cancel_button:
        cansel(message)
        return
    if project not in projects:
        bot.send_message(message.chat.id, '⚠️ Проект не найден. Попробуйте выбрать еще раз:', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project_step, projects=projects)
        return
    project_id = manager.get_project_id(project, user_id)
    manager.delete_project(user_id, project_id)
    bot.send_message(message.chat.id, f'💥 Проект *{project}* был успешно удален!', parse_mode="Markdown", reply_markup=hideBoard)


@bot.message_handler(commands=['updateprojects'])
def update_project(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "🔄 Выберите проект, данные которого хотите изменить:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
    else:
        no_projects(message)

def update_project_step_2(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, "⚠️ Ошибка выбора. Пожалуйста, укажите проект кнопкой:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
        return
    bot.send_message(message.chat.id, "✏️ Что именно вы хотите изменить?", reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)

def update_project_step_3(message, project_name):
    attribute = message.text
    reply_markup = None 
    if message.text == cancel_button:
        cansel(message)
        return
    if attribute not in attributes_of_projects.keys():
        bot.send_message(message.chat.id, "⚠️ Выберите корректный пункт меню:", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return
        
    # Извлекаем чистое системное имя поля (например, "status_id") из словаря
    clean_attribute = attributes_of_projects[attribute][1]
    
    if "Статус" in attribute:
        rows = manager.get_statuses()
        reply_markup = gen_markup([x[0] for x in rows])
        
    bot.send_message(message.chat.id, attributes_of_projects[attribute][0], reply_markup=reply_markup)
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=clean_attribute)

def update_project_step_4(message, project_name, attribute): 
    update_info = message.text
    if attribute == "status_id":
        rows = manager.get_statuses()
        if update_info in [x[0] for x in rows]:
            update_info = manager.get_status_id(update_info)
        elif update_info == cancel_button:
            cansel(message)
            return
        else:
            bot.send_message(message.chat.id, "⚠️ Неверный статус. Выберите из предложенных вариантов:", reply_markup=gen_markup([x[0] for x in rows]))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return
            
    user_id = message.from_user.id
    data = (update_info, project_name, user_id)
    manager.update_projects(attribute, data)
    bot.send_message(message.chat.id, "✨ Готово! Изменения успешно внесены в базу данных.", reply_markup=hideBoard)


@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    projects = [x[2] for x in manager.get_projects(user_id)]
    project = message.text
    if project in projects:
        info_project(message, user_id, project)
        return
    bot.reply_to(message, "🤖 Хм, я не совсем понял эту команду...")
    info(message)

    
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    manager.create_tables()
    manager.default_insert()
    bot.infinity_polling()
