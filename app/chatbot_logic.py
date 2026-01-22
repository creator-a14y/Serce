import sqlite3
import os
import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ChatBot:
    def __init__(self, db_path='chatbot.db'):
        self.db_path = db_path
        self.son_anlasilmayan_mesaj = ""
        self.vectorizer = TfidfVectorizer()
        
        # Gemini API Ayarı
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Intents (Id INTEGER PRIMARY KEY AUTOINCREMENT, Tag TEXT UNIQUE)')
        c.execute('CREATE TABLE IF NOT EXISTS Patterns (Id INTEGER PRIMARY KEY AUTOINCREMENT, IntentId INTEGER, PatternText TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS Responses (Id INTEGER PRIMARY KEY AUTOINCREMENT, IntentId INTEGER, ResponseText TEXT)')
        conn.commit()
        conn.close()

    def predict(self, user_sentence):
        # Önce Yerel Hafızaya Bak (Kosinüs Benzerliği)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT P.PatternText, R.ResponseText FROM Patterns P JOIN Responses R ON P.IntentId = R.IntentId")
        rows = cursor.fetchall()
        conn.close()

        if rows:
            patterns = [row[0] for row in rows]
            responses = [row[1] for row in rows]
            tfidf = self.vectorizer.fit_transform(patterns + [user_sentence])
            similarities = cosine_similarity(tfidf[-1], tfidf[:-1])[0]
            
            # Eğer benzerlik %30'dan fazlaysa yerel cevabı ver
            if max(similarities) > 0.30:
                return responses[similarities.argmax()]

        # Eğer yerel hafızada yoksa Gemini'ye sor
        if self.model:
            try:
                response = self.model.generate_content(user_sentence)
                return response.text
            except Exception as e:
                return f"Gemini'ye bağlanırken bir hata oluştu: {str(e)}"
        
        self.son_anlasilmayan_mesaj = user_sentence
        return "Bunu henüz bilmiyorum, öğretmek ister misin?"

    def teach(self, etiket, cevap):
        # Öğretme mantığı aynı kalıyor...
        soru = self.son_anlasilmayan_mesaj if self.son_anlasilmayan_mesaj else etiket
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO Intents (Tag) VALUES (?)", (etiket,))
        cursor.execute("SELECT Id FROM Intents WHERE Tag = ?", (etiket,))
        intent_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO Patterns (IntentId, PatternText) VALUES (?, ?)", (intent_id, soru))
        cursor.execute("INSERT INTO Responses (IntentId, ResponseText) VALUES (?, ?)", (intent_id, cevap))
        conn.commit()
        conn.close()
        self.son_anlasilmayan_mesaj = ""
        return soru
