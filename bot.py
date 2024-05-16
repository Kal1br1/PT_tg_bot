import logging
import paramiko
import os
import re
import dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import psycopg2
from psycopg2 import Error

logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

dotenv.load_dotenv()

TOKEN = os.getenv("TOKEN")

host = os.getenv('RM_HOST')
port = int(os.getenv('RM_PORT'))
username = os.getenv('RM_USER')
password = os.getenv('RM_PASSWORD')

user_db = os.getenv('DB_USER')
password_db = os.getenv('DB_PASSWORD')
host_db = os.getenv('DB_HOST')
port_db = os.getenv('DB_PORT')
database = os.getenv('DB_DATABASE')


client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
connected_ssh = False


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def idkThisCommand(update: Update, context):
    update.message.reply_text("Я не знаю такой команды.\nНаберите /help для просмотра доступных комманд")


def helpCommand(update: Update, context):
    update.message.reply_text(
        "Доступные команды:\n/start\n/find_email\n/find_phone_number\n/verify_passwordвщслук ")


def findEmailsCommand(update: Update, context):
    update.message.reply_text("Введите текст для поиска email-адресов:")
    return "find_emails"


def findEmails(update: Update, context):
    user_input = update.message.text
    emailRegex = re.compile(r"[a-z0-9._-]+@[a-z]+.[a-z]{2,3}")

    lstemails = emailRegex.findall(user_input)

    if not lstemails:
        update.message.reply_text("Почты не найдены")
        return ConversationHandler.END

    emails = ""
    for i in range(len(lstemails)):
        emails += f"{i + 1}. {lstemails[i]}\n"

    context.user_data['emails'] = lstemails
    update.message.reply_text(emails)
    update.message.reply_text("Хотите ли Вы записать данные в базу данных? Ответьте: да или нет")
    return "insert_emails"

def insertEmails(update: Update, context):
    user_input = update.message.text.lower()
    connection = None
    if user_input == "да":
        emails = context.user_data.get('emails', [])
        try:
            connection = psycopg2.connect(user=user_db,
                                          password=password_db,
                                          host=host_db,
                                          port=port_db,
                                          database=database)
            cursor = connection.cursor()
            for email in emails:
                cursor.execute(f"INSERT INTO emails (email) VALUES ('{email}');")
            connection.commit()
            update.message.reply_text("Данные успешно записаны в базу данных")
        except (Exception, Error) as error:
            update.message.reply_text("Произошла ошибка при записи данных в базу данных")
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто")
    elif user_input == "нет":
        update.message.reply_text("Данные не были записаны в базу данных.")
    else:
        update.message.reply_text("Ответьте да или нет")
        return "insert_emails"
    return ConversationHandler.END


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return 'find_phone_numbers'


def findPhoneNumbers(update: Update, context):
    user_input = update.message.text

    patterns = [r"\b8\d{10}\b", r"\b8\(\d{3}\)\d{7}\b", r"\b8 \d{3} \d{3} \d{2} \d{2}\b",
                r"\b8 \(\d{3}\) \d{3} \d{2} \d{2}\b", r"\b8-\d{3}-\d{3}-\d{2}-\d{2}\b",
                r"\+7\d{10}\b", r"\+7\(\d{3}\)\d{7}\b", r"\+7 \d{3} \d{3} \d{2} \d{2}\b",
                r"\+7 \(\d{3}\) \d{3} \d{2} \d{2}\b", r"\+7-\d{3}-\d{3}-\d{2}-\d{2}\b"]

    lstnumbers = []
    for i in patterns:
        lstnumbers += re.findall(i, user_input)

    if not lstnumbers:
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END

    str_numbers = ""
    for i in range(len(lstnumbers)):
        str_numbers += f"{i + 1}. {lstnumbers[i]}\n"
    context.user_data['phones'] = lstnumbers
    update.message.reply_text(str_numbers)
    update.message.reply_text("Хотите ли Вы записать данные в базу данных? Ответьте: да или нет")
    return "insert_phones"

def insertPhones(update: Update, context):
    user_input = update.message.text.lower()
    connection = None
    if user_input == "да":
        phones = context.user_data.get('phones', [])
        try:
            connection = psycopg2.connect(user=user_db,
                                          password=password_db,
                                          host=host_db,
                                          port=port_db,
                                          database=database)
            cursor = connection.cursor()
            for phone in phones:
                cursor.execute(f"INSERT INTO phones (phone_number) VALUES ('{phone}');")
            connection.commit()
            update.message.reply_text("Данные успешно записаны в базу данных")
        except (Exception, Error) as error:
            update.message.reply_text("Произошла ошибка при записи данных в базу данных")
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто")
    elif user_input == "нет":
        update.message.reply_text("Данные не были записаны в базу данных.")
    else:
        update.message.reply_text("Ответьте да или нет")
        return "insert_phones"
    return ConversationHandler.END


def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки сложности:')
    return 'verifyPassword'


def verifyPassword(update: Update, context):
    password = update.message.text

    count_AZ = 0
    count_az = 0
    count_nums = 0
    count_specials = 0

    for i in password:
        if "A" <= i <= "Z":
            count_AZ += 1
        elif "a" <= i <= "z":
            count_az += 1
        elif i.isdigit():
            count_nums += 1
        elif i in "!@#$%^&*()":
            count_specials += 1

    if len(password) >= 8 and count_AZ >= 1 and count_az >= 1 and count_nums >= 1 and count_specials >= 1:
        update.message.reply_text("Пароль сложный")
    else:
        update.message.reply_text("Пароль простой")
    return ConversationHandler.END


def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def isConnected(update: Update, context):
    global connected_ssh
    if not connected_ssh:
        update.message.reply_text("Для начала подключитесь к SSH.\nЧтобы подключиться наберите: /connect_ssh")
        return False
    return True


def getData(command, update: Update, context):
    if not isConnected(update, context):
        return None
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read()
    normal_data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    return f"```\n{normal_data}```"


def connectViaSSH(update: Update, context):
    global connected_ssh
    if connected_ssh:
        update.message.reply_text("Вы уже подключены по SSH")
    else:
        client.connect(hostname=host, username=username, password=password, port=port)
        update.message.reply_text("Вы успешно подключились по SSH")
        connected_ssh = True


def disconnectFromSSH(update: Update, context):
    global connected_ssh
    if not connected_ssh:
        update.message.reply_text("Вы уже отключены от SSH")
    else:
        client.close()
        update.message.reply_text("Вы успешно отключились от SSH")
        connected_ssh = False


def getRelease(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("lsb_release -a", update, context), parse_mode="MarkdownV2")


def getUname(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("uname -a", update, context), parse_mode="MarkdownV2")


def getUptime(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("uptime", update, context), parse_mode="MarkdownV2")


def getDf(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("df -h", update, context), parse_mode="MarkdownV2")


def getFree(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("free -h", update, context), parse_mode="MarkdownV2")


def getMpstat(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("mpstat", update, context), parse_mode="MarkdownV2")


def getW(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("w", update, context), parse_mode="MarkdownV2")


def getAuths(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("last -n 10", update, context), parse_mode="MarkdownV2")


def getCritical(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("journalctl -p err -n 5", update, context), parse_mode="MarkdownV2")


def getPS(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("ps au", update, context), parse_mode="MarkdownV2")


def getSS(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("ss -tunp", update, context), parse_mode="MarkdownV2")


def getServices(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("service --status-all", update, context), parse_mode="MarkdownV2")


def getAptList(update: Update, context):
    update.message.reply_text(
        "Выберите действие:\n1. Вывести список всех установленных пакетов\n2. Найти информацию о конкретном пакете")
    return "apt_list_action"


def aptListAction(update: Update, context):
    if not isConnected(update, context): return
    user_input = update.message.text
    if user_input == "1":
        update.message.reply_text(getData("apt list --installed | head -n 50", update, context),
                                  parse_mode="MarkdownV2")
        return ConversationHandler.END
    elif user_input == "2":
        update.message.reply_text("Введите название пакета для поиска:")
        return "find_package"
    else:
        update.message.reply_text("Неверный выбор. Попробуйте еще раз.")
        return "apt_list_action"


def findPackage(update: Update, context):
    package_name = update.message.text
    update.message.reply_text(getData(f"apt-cache show {package_name}", update, context), parse_mode="MarkdownV2")
    return ConversationHandler.END


def getReplInfo(update: Update, context):
    if not isConnected(update, context): return
    update.message.reply_text(getData("zgrep 'replication' /var/log/postgresql/postgresql-16-main.log* | head -15", update, context),
                              parse_mode="MarkdownV2")
def getInfoBD(table):
    connection = None
    data = []
    try:
        connection = psycopg2.connect(user=user_db,
                                      password=password_db,
                                      host=host_db,
                                      port=port_db,
                                      database=database)
        cursor = connection.cursor()
        cursor.execute(f"SELECT * from {table};")
        data += cursor.fetchall()
        logging.info(f"Команда SELECT успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
    return data


def getEmails(update: Update, context):
    data = getInfoBD("emails")
    data_text = ""
    for i in data:
        data_text += f"{i}"[1:-1] + "\n"

    update.message.reply_text(data_text)

def getPhones(update: Update, context):
    data = getInfoBD("phones")
    data_text = ""
    for i in data:
        data_text += f"{i}"[1:-1] + "\n"

    update.message.reply_text(data_text)
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler("find_email", findEmailsCommand)],
        states={
            "find_emails": [MessageHandler(Filters.text & ~Filters.command, findEmails)],
            "insert_emails": [MessageHandler(Filters.text & ~Filters.command, insertEmails)],
        },
        fallbacks=[]
    )

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler("find_phone_number", findPhoneNumbersCommand)],
        states={
            'find_phone_numbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'insert_phones': [MessageHandler(Filters.text & ~Filters.command, insertPhones)],
        },
        fallbacks=[],
    )

    convHandlerVerifyPass = ConversationHandler(
        entry_points=[CommandHandler("verify_password", verifyPasswordCommand)], states={
            'verifyPassword': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)]}, fallbacks=[])

    convHandlerAptList = ConversationHandler(
        entry_points=[CommandHandler("get_apt_list", getAptList)],
        states={
            "apt_list_action": [MessageHandler(Filters.text & ~Filters.command, aptListAction)],
            "find_package": [MessageHandler(Filters.text & ~Filters.command, findPackage)],
        },
        fallbacks=[],
    )

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))

    dp.add_handler(CommandHandler("connect_ssh", connectViaSSH))
    dp.add_handler(CommandHandler("disconnect_ssh", disconnectFromSSH))

    dp.add_handler(CommandHandler("get_release", getRelease))
    dp.add_handler(CommandHandler("get_uname", getUname))
    dp.add_handler(CommandHandler("get_uptime", getUptime))
    dp.add_handler(CommandHandler("get_df", getDf))
    dp.add_handler(CommandHandler("get_free", getFree))
    dp.add_handler(CommandHandler("get_mpstat", getMpstat))
    dp.add_handler(CommandHandler("get_w", getW))
    dp.add_handler(CommandHandler("get_auths", getAuths))
    dp.add_handler(CommandHandler("get_critical", getCritical))
    dp.add_handler(CommandHandler("get_ps", getPS))
    dp.add_handler(CommandHandler("get_ss", getSS))
    dp.add_handler(CommandHandler("get_services", getServices))

    dp.add_handler(CommandHandler("get_repl_logs", getReplInfo))
    dp.add_handler(CommandHandler("get_emails", getEmails))
    dp.add_handler(CommandHandler("get_phone_numbers", getPhones))

    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerVerifyPass)
    dp.add_handler(convHandlerAptList)
    dp.add_handler(MessageHandler(Filters.command, idkThisCommand))

    # Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()

