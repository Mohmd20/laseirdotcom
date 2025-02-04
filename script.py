import sqlite3
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup , BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# جایگزین با توکن واقعی
TOKEN = "7980217172:AAFuQy4Gv9wYqtm42zxbRyh9zh89oWfHqMM"

# تعریف دیکشنری‌های مربوط به عناوین فارسی
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

def get_db_connection():
    return sqlite3.connect("bot_database.db")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("بعدی ", callback_data="start_business")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("برای شروع کافیه کلیک کنید تا در خرید محصول کمکتون کنم", reply_markup=reply_markup)

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
async def support (update:Update , context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("برای ارتباط با ما روی   id زیر کلیک کنید :(https://t.me/misterwebdeveloper)" , parse_mode="Markdown")
async def set_bot_commands(application: Application):
    commands = [
        BotCommand("start" , "خانه"),
        BotCommand("support" , "ارتباط با پشتیبانی")
    ]
    await application.bot.set_my_commands(commands)
async def column_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = 235828041
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
        await query.message.reply_document(document=bio)
        user_id = update.effective_user.id

# متن پیام برای ادمین (می‌توانید همچنان آی‌دی را به صورت متن بگنجانید)
        admin_message = (
        f"کاربری از ربات فایل '{COLUMN_LABELS.get(column_key, column_key)}' "
        f"را از حوزه '{TABLE_LABELS.get(table_key, table_key)}' دریافت کرد."
        )

# ایجاد یک دکمه اینلاین با URL مناسب
        keyboard = [
        [InlineKeyboardButton("چت با کاربر", url=f"tg://user?id={user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        keyboard = [[InlineKeyboardButton("بازگشت", callback_data="back_to_tables")]]
        keyboard.append([InlineKeyboardButton("ارتباط با پشتیبانی", url=f"tg://user?id={ADMIN_ID}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"کاتالوگ {COLUMN_LABELS.get(column_key)} ارسال شد. اون رو مطالعه کنید و در صورت نیاز با پشتیبانی در ارتباط باشید", reply_markup=reply_markup)

    else:
        keyboard = [[InlineKeyboardButton("بازگشت", callback_data="back_to_tables")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("متاسفانه داده‌ای یافت نشد.", reply_markup=reply_markup)

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def back_to_tables(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_business_callback(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start_business_callback, pattern="^start_business$"))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    app.add_handler(CallbackQueryHandler(back_to_tables, pattern="^back_to_tables$"))
    app.add_handler(CallbackQueryHandler(table_callback, pattern="^table_"))
    app.add_handler(CallbackQueryHandler(column_callback, pattern="^column_"))
    app.add_handler(CommandHandler("support" , support))
    print("The Robot Is Running!!")
    app.post_init = set_bot_commands
    app.run_polling()

if __name__ == '__main__':
    main()
