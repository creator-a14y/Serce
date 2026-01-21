import sqlite3
import numpy as np
import string
import threading
from sentence_transformers import SentenceTransformer, util

class ChatBot:
    def __init__(self, db_path='chatbot.db'):
        self.db_path = db_path
        self.son_anlasilmayan_mesaj = ""
        # Çok dilli (Türkçe destekli) anlamsal zeka modeli
        self.similarity_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.init_db()

    def tr_lower(self, metin):
        """Türkçe karakter uyumlu küçük harf dönüşümü."""
        return metin.replace('İ', 'i').replace('I', 'ı').lower()

    def metin_temizle(self, metin):
        metin = self.tr_lower(metin)
        return "".join([c for c in metin if c not in string.punctuation])

    def init_db(self):
        """SQLite tablolarını hazırlar."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Intents (Id INTEGER PRIMARY KEY AUTOINCREMENT, Tag TEXT UNIQUE)')
        c.execute('CREATE TABLE IF NOT EXISTS Patterns (Id INTEGER PRIMARY KEY AUTOINCREMENT, IntentId INTEGER, PatternText TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS Responses (Id INTEGER PRIMARY KEY AUTOINCREMENT, IntentId INTEGER, ResponseText TEXT)')
        conn.commit()
        conn.close()

    def predict(self, user_sentence):
        temiz_user_s = self.metin_temizle(user_sentence)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tüm patternları ve bağlı cevapları çek
        cursor.execute("""
            SELECT P.PatternText, R.ResponseText 
            FROM Patterns P 
            JOIN Responses R ON P.IntentId = R.IntentId
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            self.son_anlasilmayan_mesaj = user_sentence
            return None

        # Anlamsal Karşılaştırma
        en_yuksek_skor = -1
        en_iyi_cevap = None

        user_vec = self.similarity_model.encode(temiz_user_s, convert_to_tensor=True)

        for pattern, response in rows:
            pattern_vec = self.similarity_model.encode(self.metin_temizle(pattern), convert_to_tensor=True)
            skor = util.cos_sim(user_vec, pattern_vec).item()

            if skor > en_yuksek_skor:
                en_yuksek_skor = skor
                en_iyi_cevap = response

        # %75 benzerlik eşiği
        if en_yuksek_skor > 0.75:
            return en_iyi_cevap
        
        self.son_anlasilmayan_mesaj = user_sentence
        return None

    def teach(self, etiket, cevap):
        soru = self.son_anlasilmayan_mesaj if self.son_anlasilmayan_mesaj else etiket
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT OR IGNORE INTO Intents (Tag) VALUES (?)", (etiket,))
            cursor.execute("SELECT Id FROM Intents WHERE Tag = ?", (etiket,))
            intent_id = cursor.fetchone()[0]
            
            cursor.execute("INSERT INTO Patterns (IntentId, PatternText) VALUES (?, ?)", (intent_id, soru))
            cursor.execute("INSERT INTO Responses (IntentId, ResponseText) VALUES (?, ?)", (intent_id, cevap))
            conn.commit()
        finally:
            conn.close()
            self.son_anlasilmayan_mesaj = ""
        return soru