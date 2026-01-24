import psycopg2
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ChatBot:
    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL")
        self.vectorizer = TfidfVectorizer()
        self.init_db()

    def get_connection(self):
        return psycopg2.connect(self.db_url)

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Intents (Id SERIAL PRIMARY KEY, Tag TEXT UNIQUE)')
        c.execute('CREATE TABLE IF NOT EXISTS Patterns (Id SERIAL PRIMARY KEY, IntentId INTEGER, PatternText TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS Responses (Id SERIAL PRIMARY KEY, IntentId INTEGER, ResponseText TEXT)')
        conn.commit()
        c.close()
        conn.close()

    def predict(self, user_sentence):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT P.PatternText, R.ResponseText FROM Patterns P JOIN Responses R ON P.IntentId = R.IntentId")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows: return "Zihnim boş..."

        patterns = [row[0] for row in rows]
        responses = [row[1] for row in rows]
        
        tfidf = self.vectorizer.fit_transform(patterns + [user_sentence])
        similarities = cosine_similarity(tfidf[-1], tfidf[:-1])[0]
        
        # Eşik değeri: 0.50 yaparak daha net cevaplar vermesini sağlıyoruz
        if similarities.size > 0 and max(similarities) > 0.50:
            return responses[similarities.argmax()]
        
        return "Bunu bilmiyorum. Öğret: konu | cevap"

    def teach(self, etiket, cevap):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Intents (Tag) VALUES (%s) ON CONFLICT (Tag) DO NOTHING", (etiket,))
        cursor.execute("SELECT Id FROM Intents WHERE Tag = %s", (etiket,))
        intent_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO Patterns (IntentId, PatternText) VALUES (%s, %s)", (intent_id, etiket))
        cursor.execute("INSERT INTO Responses (IntentId, ResponseText) VALUES (%s, %s)", (intent_id, cevap))
        conn.commit()
        cursor.close()
        conn.close()
