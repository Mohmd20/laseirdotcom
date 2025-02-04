import sqlite3
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# جایگزین با توکن واقعی
TOKEN = "..."

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
    return sqlite3.connect("mydatabase.db")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("بزن بریم", callback_data="start_business")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("خوش آمدید!", reply_markup=reply_markup)

async def start_business_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(table_label, callback_data=f"table_{table_key}")] for table_key, table_label in TABLE_LABELS.items()]
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data="back_to_start")])
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
    await query.edit_message_text(f"شما {TABLE_LABELS.get(table_key, table_key)} را انتخاب کردید.\nحالا یکی از موارد زیر را انتخاب کنید:", reply_markup=reply_markup)

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
        await query.message.reply_document(document=bio)
        keyboard = [[InlineKeyboardButton("بازگشت", callback_data="back_to_tables")]]
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

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start_business_callback, pattern="^start_business$"))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    app.add_handler(CallbackQueryHandler(back_to_tables, pattern="^back_to_tables$"))
    app.add_handler(CallbackQueryHandler(table_callback, pattern="^table_"))
    app.add_handler(CallbackQueryHandler(column_callback, pattern="^column_"))

    print("ربات در حال اجرا است...")
    app.run_polling()

if __name__ == '__main__':
    main()
