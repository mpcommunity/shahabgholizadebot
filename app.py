import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from groq import Groq

# تنظیمات اولیه فلاسک
# پوشه templates باید شامل فایل index.html باشد
app = Flask(__name__, template_folder='templates')
CORS(app)

# دریافت کلید API از Environment Variable سرور (بدون کوتیشن در پنل Render)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# بررسی متصل بودن کلید برای جلوگیری از کرش کردن سرور
if not GROQ_API_KEY:
    print("CRITICAL ERROR: GROQ_API_KEY is not set in Environment Variables!")

client = Groq(api_key=GROQ_API_KEY)

# حافظه موقت برای نگهداری تاریخچه چت کاربرها
chat_histories = {}

# دستورات سیستمی برای هدایت هوش مصنوعی
SYSTEM_PROMPT = (
    "تو چت‌بات رسمی موسسه حقوقی شهاب قلی‌زاده هستی. "
    "باید با استناد به مواد قانونی ایران جواب بدهی. پاسخ‌ها را به صورت حرفه‌ای و با فرمت Markdown (برای بولد کردن) ارسال کن. "
    "تاریخچه چت را به یاد داشته باش و به سوالات پیوسته پاسخ دقیق بده."
)

@app.route('/')
def home():
    # نمایش فایل یکپارچه‌ای که تمام CSS و JS در آن است
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_legal_bot():
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_session')
        user_question = data.get('message', '')

        if not user_question:
            return jsonify({"reply": "لطفاً سوال خود را بپرسید."}), 400

        # مدیریت حافظه: اگر کاربر جدید است، تاریخچه را ایجاد کن
        if user_id not in chat_histories:
            chat_histories[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

        # اضافه کردن سوال کاربر به تاریخچه
        chat_histories[user_id].append({"role": "user", "content": user_question})

        # ارسال کل تاریخچه به Groq برای درک بهتر متن (Context)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_histories[user_id],
            temperature=0.6,
            max_tokens=4000
        )

        bot_reply = completion.choices[0].message.content

        # اضافه کردن پاسخ هوش مصنوعی به تاریخچه
        chat_histories[user_id].append({"role": "assistant", "content": bot_reply})

        # محدود کردن حافظه به 10 پیام آخر برای جلوگیری از سنگین شدن درخواست‌ها
        if len(chat_histories[user_id]) > 12:
            chat_histories[user_id] = [chat_histories[user_id][0]] + chat_histories[user_id][-10:]

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"reply": "در حال حاضر مشکلی در ارتباط با هوش مصنوعی وجود دارد. لطفاً لحظاتی دیگر تلاش کنید."}), 500

# تنظیمات پورت برای اجرا روی Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
