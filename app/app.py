from flask import Flask, request, render_template, jsonify
import os
from chatbot_logic import ChatBot

app = Flask(__name__)
bot = ChatBot()

# Parola Yönetimi: Buraya istediğin kadar kullanıcı ekleyebilirsin
# 'admin' şifresini Render Environment Variables'dan (ADMIN_PASS) alır.
DEBUG_PASSWORDS = {
    "admin": os.environ.get("ADMIN_PASS", "serce123"),
    "misafir": "serce2026"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/debug')
def debug_page():
    return render_template('debug.html')

@app.route('/get')
def get_bot_response():
    user_text = request.args.get('msg')
    if not user_text:
        return jsonify({"response": "Bir şey yazmadınız..."})
    return jsonify({"response": bot.predict(user_text)})

@app.route('/teach_debug', methods=['POST'])
def teach_bot():
    data = request.json
    user = data.get('user')
    password = data.get('password')
    etiket = data.get('tag')
    cevap = data.get('response')

    # Yetki Kontrolü
    if user in DEBUG_PASSWORDS and DEBUG_PASSWORDS[user] == password:
        # chatbot_logic içindeki teach fonksiyonunu çağırır
        soru = bot.teach(etiket, cevap)
        return jsonify({"status": "success", "message": f"'{soru}' kavramı başarıyla öğretildi!"})
    else:
        return jsonify({"status": "error", "message": "Hatalı kullanıcı adı veya parola!"}), 403

if __name__ == "__main__":
    app.run()
