import sqlite3
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

# =====================
# تنظیمات اولیه و ثابت‌ها
# =====================
TOKEN = "7980217172:AAFuQy4Gv9wYqtm42zxbRyh9zh89oWfHqMM"

# رمزها (برای مثال)
PASSWORD_ADD = "123"       # رمز افزودن ادمین
MAIN_ADMIN_PASS = "321"     # رمز عملیات ادمین اصلی

# حالت مکالمه برای دریافت فایل در ویرایش کاتالوگ
STATE_WAIT_FOR_CATALOG_FILE = 1

# دیکشنری‌های مربوط به کاتالوگ (ساختار قبلی)
TABLE_LABELS = {
    "gold": "حکاکی رنگی طلا",
    "industrial": "حکاکی قطعات صنعتی",
    "ads": "تبلیغات و بسته بندی",
    "wood": "چرم و چوب و پارچه",
    "mirror": "شیشه و آیینه",
    "stone": "سنگ و سرامیک"
}

TABLE_COLUMNS = {
    "gold": ["mopa"],
    "industrial": ["fiber"],
    "ads": ["fiber", "diod"],
    "wood": ["fiber", "diod"],
    "mirror": ["fiber", "diod", "uv"],
    "stone": ["fiber", "diod"]
}

COLUMN_LABELS = {
    "mopa": "موپا",
    "fiber": "فایبر هوشمند",
    "diod": "دیود هوشمند",
    "uv": "UV"
}

# =====================
# توابع اتصال به پایگاه داده
# =====================
def get_db_connection():
    # از یک پایگاه داده یکسان (مثلاً "bot_database.db") در تمام قسمت‌ها استفاده کنید
    return sqlite3.connect("bot_database.db")

def create_admins_table():
    conn = sqlite3.connect("bot_database.db")
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            name TEXT
        )
    ''')
    conn.commit()
    conn.close()






async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("بزن بریم", callback_data="start_business")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("خوش آمدید!", reply_markup=reply_markup)

async def start_business_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(table_label, callback_data=f"table_{table_key}")] for table_key, table_label in TABLE_LABELS.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("لطفاً حوزه کسب کارتون رو انتخاب کنید:", reply_markup=reply_markup)

async def table_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    table_key = query.data.split("_", 1)[1]
    context.user_data["selected_table"] = table_key
    columns = TABLE_COLUMNS.get(table_key, [])
    keyboard = [[InlineKeyboardButton(COLUMN_LABELS.get(col, col), callback_data=f"column_{col}")] for col in columns]
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data="back_to_tables")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"شما {TABLE_LABELS.get(table_key, table_key)} را انتخاب کردید.\nهر کدام را خواستید انتخاب کنید تا کاتالوگش را براتون ارسال کنم", reply_markup=reply_markup)



async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, name FROM admins")
    admins = cur.fetchall()
    conn.close()
    keyboard = []
    if admins:
        for admin in admins:
            admin_id, admin_name = admin
            keyboard.append([InlineKeyboardButton(f"ارتباط با {admin_name}", url=f"tg://user?id={admin_id}")]) 
        reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("برای ارتباط با ما با یکی از پشتیبان ها در ارتباط باشید", reply_markup=reply_markup)

async def set_bot_commands(application: Application):
    commands = [
        BotCommand("start" , "خانه"),
        BotCommand("support" , "ارتباط با پشتیبانی")
    ]
    await application.bot.set_my_commands(commands)
async def column_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    column_key = query.data.split("_", 1)[1]
    table_key = context.user_data.get("selected_table")
    
    if not table_key:
        await query.edit_message_text("خطا: حوزه کسب کار انتخاب نشده است.")
        return
    
    conn = get_db_connection()
    cur = conn.cursor()
    sql = f"SELECT {column_key} FROM {table_key} ORDER BY id DESC LIMIT 1"
    cur.execute(sql)
    result = cur.fetchone()
    conn.close()

    if result and result[0]:
        file_data = result[0]
        bio = BytesIO(file_data)
        bio.name = f"{column_key}.pdf"
        # ارسال فایل به کاربر
        await query.message.reply_document(document=bio)
        
        # ارسال پیام به تمامی ادمین‌ها
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, name FROM admins")
        admins = cur.fetchall()
        conn.close()

        if admins:
            for admin in admins:
                admin_user_id, admin_name = admin
                # ایجاد لینک برای دسترسی به پیوی کاربر
                user_id = update.effective_user.id
                user_link = f"<a href=\"tg://user?id={user_id}\">id کاربر</a>"
                # اطلاعات خرید برای ادمین
                admin_message = (
                    f"کاربری از ربات فایل '{COLUMN_LABELS.get(column_key, column_key)}' "
                    f"را از حوزه '{TABLE_LABELS.get(table_key, table_key)}' دریافت کرد."
                )
                # ارسال پیام به ادمین
                # await context.bot.send_message(chat_id=admin_user_id, text=admin_message, parse_mode="HTML")
                # ارسال دکمه چت با کاربر
                keyboard = [
                    [InlineKeyboardButton("چت با کاربر", url=f"tg://user?id={user_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(
                    chat_id=admin_user_id,
                    text=f"{admin_message}",
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )

        # ارسال پیامی به کاربر
        keyboard = [[InlineKeyboardButton("بازگشت", callback_data="back_to_tables")]]
        if admins:
            for admin in admins:
                admin_id, admin_name = admin
                keyboard.append([InlineKeyboardButton(f"ارتباط با {admin_name}", url=f"tg://user?id={admin_id}")]) 
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("فایل برای شما ارسال شد.", reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("بازگشت", callback_data="back_to_tables")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("متاسفانه داده‌ای یافت نشد.", reply_markup=reply_markup)



async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def back_to_tables(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_business_callback(update, context)



# =====================
# بخش افزودن ادمین (با رمز PASSWORD_ADD)
# =====================
async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("لغو ❌", callback_data="cancel_admin_addition")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفاً نام خود را وارد کنید:" , reply_markup=reply_markup)
    return 1

async def add_admin_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ایجاد کیبورد اینلاین با دکمه لغو
    admin_name = update.message.text.strip()
    user_id = update.effective_user.id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO admins (user_id, name) VALUES (?, ?)", (user_id, admin_name))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"ادمین با نام {admin_name} اضافه شد.")
    return ConversationHandler.END

async def cancel_admin_addition_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("فرآیند افزودن ادمین لغو شد ❌")
    return ConversationHandler.END

# =====================
# بخش ادمین اصلی (با رمز MAIN_ADMIN_PASS)
# =====================
# وقتی کاربر رمز MAIN_ADMIN_PASS را ارسال کند، منوی ادمین اصلی نمایش داده می‌شود
async def main_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("حذف تکی ادمین ها", callback_data="admin_remove_single")],
        [InlineKeyboardButton("حذف همه ادمین ها", callback_data="admin_remove_all")],
        [InlineKeyboardButton("ویرایش کاتالوگ", callback_data="admin_edit_catalog")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("منوی ادمین اصلی:", reply_markup=reply_markup)

# ----- حذف تکی ادمین -----
async def admin_remove_single_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, name FROM admins")
    admins = cur.fetchall()
    conn.close()
    if not admins:
        await query.edit_message_text("ادمینی ثبت نشده است.")
        return
    keyboard = []
    for admin in admins:
        user_id, name = admin
        keyboard.append([InlineKeyboardButton(f"{name} ({user_id})", callback_data=f"remove_admin_{user_id}")])
    # اضافه کردن دکمه بازگشت
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data="main_admin_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("لطفاً یک ادمین را برای حذف انتخاب کنید:", reply_markup=reply_markup)

async def remove_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")  # قالب: remove_admin_<user_id>
    if len(parts) == 3:
        admin_user_id = parts[2]
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM admins WHERE user_id = ?", (admin_user_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text("ادمین مورد نظر حذف شد.")

# ----- حذف همه ادمین ها -----
async def admin_remove_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("تایید", callback_data="confirm_remove_all")],
        [InlineKeyboardButton("بازگشت", callback_data="main_admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("آیا مطمئن هستید که می‌خواهید تمامی ادمین‌ها حذف شوند؟", reply_markup=reply_markup)

async def confirm_remove_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM admins")
    conn.commit()
    conn.close()
    await query.edit_message_text("تمامی ادمین‌ها حذف شدند.")

async def cancel_remove_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("عملیات حذف تمامی ادمین‌ها لغو شد.")

# ----- ویرایش کاتالوگ -----
# وقتی کاربر روی دکمه "ویرایش کاتالوگ" کلیک می‌کند، دکمه‌های مربوط به ستون‌ها نمایش داده می‌شود
async def admin_edit_catalog_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("UV", callback_data="catalog_edit_uv")],
        [InlineKeyboardButton("FIBER", callback_data="catalog_edit_fiber")],
        [InlineKeyboardButton("DIOD", callback_data="catalog_edit_diod")],
        [InlineKeyboardButton("MOPA", callback_data="catalog_edit_mopa")],
        [InlineKeyboardButton("بازگشت", callback_data="main_admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("لطفاً کاتالوگ مورد نظر را برای ویرایش انتخاب کنید:", reply_markup=reply_markup)

# وقتی یکی از دکمه‌های کاتالوگ انتخاب شود
async def catalog_edit_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # استخراج ستون انتخاب‌شده؛ مثلاً از "catalog_edit_mopa" قسمت آخر (mopa) را می‌گیریم
    selected = query.data.split("_")[-1]  # uv, fiber, diod, یا mopa
    context.user_data["selected_catalog_column"] = selected
    keyboard = [[InlineKeyboardButton("بازگشت", callback_data="main_admin_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"شما {selected} را انتخاب کردید. لطفاً فایل جدید را ارسال کنید:",reply_markup=reply_markup)
    # وارد حالت دریافت فایل می‌شویم
    return STATE_WAIT_FOR_CATALOG_FILE

# پیام handler برای دریافت فایل کاتالوگ
async def catalog_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        file_id = update.message.document.file_id
        file = await context.bot.get_file(file_id)  # تغییر از update.message.bot به context.bot
        file_data = await file.download_as_bytearray()
        selected_column = context.user_data.get("selected_catalog_column")
        if not selected_column:
            await update.message.reply_text("خطایی رخ داد. لطفاً دوباره امتحان کنید.")
            return ConversationHandler.END
        tables_updated = []
        conn = get_db_connection()
        cur = conn.cursor()
        # به‌روزرسانی تمام جدول‌هایی که ستون انتخاب‌شده را دارند
        for table, columns in TABLE_COLUMNS.items():
            if selected_column in columns:
                sql = f"""
                    UPDATE {table} 
                    SET {selected_column} = ? 
                    WHERE id = (SELECT id FROM {table} ORDER BY id DESC LIMIT 1)
                """
                cur.execute(sql, (file_data,))
                conn.commit()
                tables_updated.append(table)
        conn.close()
        keyboard = [[InlineKeyboardButton("بازگشت", callback_data="main_admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"کاتالوگ {selected_column} در جداول {', '.join(tables_updated)} به‌روزرسانی شد.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("لطفاً یک فایل معتبر ارسال کنید.")
    return ConversationHandler.END

async def cancel_catalog_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ویرایش کاتالوگ لغو شد.")
    return ConversationHandler.END
async def main_admin_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("حذف تکی ادمین ها", callback_data="admin_remove_single")],
        [InlineKeyboardButton("حذف همه ادمین ها", callback_data="admin_remove_all")],
        [InlineKeyboardButton("ویرایش کاتالوگ", callback_data="admin_edit_catalog")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("منوی ادمین اصلی:", reply_markup=reply_markup)

# =====================
# main() و ثبت Handlerها
# =====================
def main():
    create_admins_table()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start_business_callback, pattern="^start_business$"))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    app.add_handler(CallbackQueryHandler(back_to_tables, pattern="^back_to_tables$"))
    app.add_handler(CallbackQueryHandler(table_callback, pattern="^table_"))
    app.add_handler(CallbackQueryHandler(column_callback, pattern="^column_"))
    app.add_handler(CommandHandler("support" , support))
    # ثبت Handler مربوط به افزودن ادمین
    add_admin_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(PASSWORD_ADD), add_admin_start)],
    states={
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_name),
            CallbackQueryHandler(cancel_admin_addition_callback, pattern="^cancel_admin_addition$")]
    },
    fallbacks=[CommandHandler("cancel", cancel_admin_addition_callback)]
    )
    app.add_handler(add_admin_conv_handler)

    # Handler برای دریافت رمز ادمین اصلی
    app.add_handler(MessageHandler(filters.Text(MAIN_ADMIN_PASS), main_admin_menu))

    # CallbackQueryHandlers برای منوی ادمین اصلی
    app.add_handler(CallbackQueryHandler(admin_remove_single_callback, pattern="^admin_remove_single$"))
    app.add_handler(CallbackQueryHandler(admin_remove_all_callback, pattern="^admin_remove_all$"))
    app.add_handler(CallbackQueryHandler(confirm_remove_all_callback, pattern="^confirm_remove_all$"))
    app.add_handler(CallbackQueryHandler(cancel_remove_all_callback, pattern="^cancel_remove_all$"))
    app.add_handler(CallbackQueryHandler(admin_edit_catalog_callback, pattern="^admin_edit_catalog$"))
    app.add_handler(CallbackQueryHandler(catalog_edit_choice_callback, pattern="^catalog_edit_"))
    app.add_handler(CallbackQueryHandler(remove_admin_callback, pattern=r"^remove_admin_\d+$"))
    app.add_handler(CallbackQueryHandler(main_admin_back_callback, pattern="^main_admin_back$"))
    app.add_handler(CallbackQueryHandler(cancel_admin_addition_callback, pattern="^cancel_admin_addition$"))

    # ConversationHandler برای دریافت فایل ویرایش کاتالوگ
    catalog_edit_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Document.ALL, catalog_file_handler)],
        states={
            STATE_WAIT_FOR_CATALOG_FILE: [MessageHandler(filters.Document.ALL, catalog_file_handler)]
        },
        fallbacks=[CommandHandler("cancel", cancel_catalog_edit)]
    )
    app.add_handler(catalog_edit_conv_handler)

    # (سایر handlerهای مربوط به کاتالوگ، انتخاب حوزه و ارسال فایل برای کاربران نیز همانند قبل اضافه شوند)

    # ثبت دستورات ربات (اختیاری)
    async def set_commands(app: Application):
        commands = [
            BotCommand("start", "خانه"),
            BotCommand("support", "ارتباط با پشتیبانی")
        ]
        await app.bot.set_my_commands(commands)
    app.post_init = set_commands

    print("ربات در حال اجرا است...")
    app.run_polling()

if __name__ == '__main__':
    main()