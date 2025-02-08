import sqlite3
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)

# =======================
# تنظیمات اولیه و ثابت‌ها
# =======================

# توکن ربات خود را جایگزین کنید
TOKEN = "7980217172:AAFuQy4Gv9wYqtm42zxbRyh9zh89oWfHqMM"

# (در صورت نیاز) آی‌دی اصلی ادمینی که برای ارسال کاتالوگ استفاده می‌شود (مثلاً برای اطلاع‌رسانی)
MAIN_ADMIN_ID = 123456789

# تعریف سه رمز (secret passwords)
PASSWORD_ADD = "123"           # رمز اول برای افزودن ادمین
PASSWORD_REMOVE_SINGLE = "321"  # رمز دوم برای حذف یک ادمین
PASSWORD_REMOVE_ALL = "1234"       # رمز سوم برای حذف تمام ادمین‌ها

# حالت‌های مکالمه برای افزودن ادمین
ADD_ADMIN_NAME = 1

# (بخش‌های قبلی مربوط به کاتالوگ)
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

# =======================
# توابع اتصال به پایگاه داده
# =======================

def get_db_connection():
    # مطمئن شوید نام پایگاه داده با آنچه که در اسکریپت ایجاد جدول‌ها استفاده شده یکسان باشد
    return sqlite3.connect("bot_database.db")

def create_admins_table():
    # ایجاد جدول admins جهت ذخیره ادمین‌ها
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

# =======================
# توابع مربوط به ارسال کاتالوگ (بخش قبلی)
# =======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("بزن بریم", callback_data="start_business")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("خوش آمدید!", reply_markup=reply_markup)

async def start_business_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(table_label, callback_data=f"table_{table_key}")]
                for table_key, table_label in TABLE_LABELS.items()]
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data="back_to_start")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("لطفاً حوزه کسب کارتون رو انتخاب کنید:", reply_markup=reply_markup)

async def table_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    table_key = query.data.split("_", 1)[1]
    context.user_data["selected_table"] = table_key
    columns = TABLE_COLUMNS.get(table_key, [])
    keyboard = [[InlineKeyboardButton(COLUMN_LABELS.get(col, col), callback_data=f"column_{col}")]
                for col in columns]
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data="back_to_tables")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"شما {TABLE_LABELS.get(table_key, table_key)} را انتخاب کردید.\nحالا یکی از موارد زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )

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
    # await update.message.reply_text("برای ارتباط با ما روی id زیر کلیک کنید: (https://t.me/misterwebdeveloper)", parse_mode="Markdown")

async def set_bot_commands(application: Application):
    commands = [
        BotCommand("start", "خانه"),
        BotCommand("support", "ارتباط با پشتیبانی")
    ]
    await application.bot.set_my_commands(commands)

# =======================
# توابع مدیریت ادمین (قابلیت‌های جدید)
# =======================

# --- افزودن ادمین ---
async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # کاربر پس از ارسال رمز PASSWORD_ADD وارد این handler می‌شود
    await update.message.reply_text("لطفاً نام خود را وارد کنید:")
    return ADD_ADMIN_NAME

async def add_admin_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_name = update.message.text.strip()
    user_id = update.effective_user.id
    conn = get_db_connection()
    cur = conn.cursor()
    # استفاده از INSERT OR IGNORE تا اگر کاربر قبلاً ثبت شده باشد خطا ندهد
    cur.execute("INSERT OR IGNORE INTO admins (user_id, name) VALUES (?, ?)", (user_id, admin_name))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"ادمین با نام {admin_name} اضافه شد.")
    return ConversationHandler.END

async def cancel_admin_addition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات افزودن ادمین لغو شد.")
    return ConversationHandler.END

# --- حذف یک ادمین (رمز دوم) ---
async def remove_admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, name FROM admins")
    admins = cur.fetchall()
    conn.close()
    if not admins:
        await update.message.reply_text("ادمینی ثبت نشده است.")
        return
    keyboard = []
    for admin in admins:
        user_id, name = admin
        keyboard.append([InlineKeyboardButton(f"{name} ({user_id})", callback_data=f"remove_admin_{user_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفاً یک ادمین را برای حذف انتخاب کنید:", reply_markup=reply_markup)

async def remove_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # مانند "remove_admin_195605236"
    parts = data.split("_")
    if len(parts) == 3:
        admin_user_id = parts[2]
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM admins WHERE user_id = ?", (admin_user_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text("ادمین مورد نظر حذف شد.")

# --- حذف تمام ادمین‌ها (رمز سوم) ---
async def remove_all_admins_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("تایید", callback_data="confirm_remove_all"),
         InlineKeyboardButton("لغو", callback_data="cancel_remove_all")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("آیا مطمئن هستید که می‌خواهید تمامی ادمین‌ها حذف شوند؟", reply_markup=reply_markup)

async def confirm_remove_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM admins")
    conn.commit()
    conn.close()
    await query.edit_message_text("تمامی ادمین‌ها حذف شدند.")

async def cancel_remove_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("عملیات حذف تمامی ادمین‌ها لغو شد.")

# =======================
# main() و ثبت Handlerها
# =======================

def main():
    # ایجاد جدول ادمین‌ها (admins) در صورت عدم وجود
    create_admins_table()
    
    app = Application.builder().token(TOKEN).build()

    # ثبت handlerهای مربوط به کاتالوگ و بخش‌های قبلی
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("support", support))
    app.add_handler(CallbackQueryHandler(start_business_callback, pattern="^start_business$"))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    app.add_handler(CallbackQueryHandler(back_to_tables, pattern="^back_to_tables$"))
    app.add_handler(CallbackQueryHandler(table_callback, pattern="^table_"))
    app.add_handler(CallbackQueryHandler(column_callback, pattern="^column_"))
    
    # -----------------------------
    # ثبت handlerهای مدیریت ادمین
    # -----------------------------
    
    # 1. افزودن ادمین (رمز اول)
    admin_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(PASSWORD_ADD), add_admin_start)],
        states={
            ADD_ADMIN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_name)]
        },
        fallbacks=[CommandHandler("cancel", cancel_admin_addition)]
    )
    app.add_handler(admin_conv_handler)
    
    # 2. حذف یک ادمین (رمز دوم)
    app.add_handler(MessageHandler(filters.Text(PASSWORD_REMOVE_SINGLE), remove_admin_list))
    app.add_handler(CallbackQueryHandler(remove_admin_callback, pattern=r"^remove_admin_\d+$"))
    
    # 3. حذف تمامی ادمین‌ها (رمز سوم)
    app.add_handler(MessageHandler(filters.Text(PASSWORD_REMOVE_ALL), remove_all_admins_start))
    app.add_handler(CallbackQueryHandler(confirm_remove_all, pattern="^confirm_remove_all$"))
    app.add_handler(CallbackQueryHandler(cancel_remove_all, pattern="^cancel_remove_all$"))
    
    # ثبت دستورهای ربات
    app.post_init = set_bot_commands
    
    print("ربات در حال اجرا است...")
    app.run_polling()

if __name__ == '__main__':
    main()