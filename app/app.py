from flask import Flask, render_template, request, jsonify
from chatbot_logic import ChatBot
import os

app = Flask(__name__)
bot = ChatBot()

@app.route("/")
def index():
    return render_template("index.html")

# app.py içindeki ilgili rota
@app.route("/get")
def get_bot_response():
    user_msg = request.args.get('msg', '').strip()
    
    if user_msg.startswith("Öğret:"):
        try:
            # Format: Öğret: konu_adı | verilecek_cevap
            content = user_msg.replace("Öğret:", "").split("|")
            konu = content[0].strip()
            cevap = content[1].strip()
            
            ogrenilen_soru = bot.teach(konu, cevap)
            return jsonify({
                "response": f"Harika! Artık biri '{ogrenilen_soru}' derse, ona '{cevap}' diyeceğim."
            })
        except:
            return jsonify({"response": "Hata! Lütfen şu formatta öğret: 'Öğret: konu | cevap'"})

    response = bot.predict(user_msg)
    if not response:
        return jsonify({"response": "Bunu henüz bilmiyorum. 'Öğret: konu | cevap' diyerek bana öğretebilirsin!"})
        
    return jsonify({"response": response})

if __name__ == "__main__":

    app.run(debug=True, port=5000)
