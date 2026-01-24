from flask import Flask, request, render_template, jsonify
import os, json
from chatbot_logic import ChatBot

app = Flask(__name__)
bot = ChatBot()

# Şifreleri Render Environment Variables'dan (DEBUG_USERS) JSON olarak çeker
# Örnek Değer: {"ismail": "serce2026", "admin": "12345"}
users_raw = os.environ.get("DEBUG_USERS", '{"admin": "serce123"}')
try:
    DEBUG_PASSWORDS = json.loads(users_raw)
except:
    DEBUG_PASSWORDS = {"admin": "serce123"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/debug')
def debug_page():
    return render_template('debug.html')

@app.route('/get')
def get_bot_response():
    user_text = request.args.get('msg')
    mode = request.args.get('mode', 'public') # İstek türünü belirler
    
    response = bot.predict(user_text)
    
    # Ana sayfada kullanıcıya 'Öğret' ipucunu gösterme
    if mode == 'public' and "Öğret:" in response:
        return jsonify({"response": "Üzgünüm, bunu henüz öğrenmedim. Bana ne sormak istersin? 🐦"})
    
    return jsonify({"response": response})

@app.route('/teach_debug', methods=['POST'])
def teach_bot():
    data = request.json
    user = data.get('user')
    password = data.get('password')
    
    if user in DEBUG_PASSWORDS and str(DEBUG_PASSWORDS[user]) == str(password):
        bot.teach(data.get('tag'), data.get('response'))
        return jsonify({"status": "success", "message": "Başarıyla kaydedildi!"})
    else:
        return jsonify({"status": "error", "message": "Yetkisiz erişim!"}), 403

if __name__ == "__main__":
    app.run()
