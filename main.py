import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
import uvicorn

app = FastAPI()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class UrunGiris(BaseModel):
    isim: str
    fiyat: float
    adet: int
    agirlik: float

@app.post("/hesapla")
async def analiz_et(urun: UrunGiris):
    # AI burada hem kategoriyi tahmin edecek hem gümrüğü hesaplayacak
    prompt = f"""
    Müşteri şu ürünü getirmek istiyor: "{urun.isim}"
    Birim Fiyat: {urun.fiyat} USD, Adet: {urun.adet}, Toplam Ağırlık: {urun.agirlik} KG.

    Senden şunları bekliyorum:
    1. Ürünün hangi ana kategoriye (Elektronik, Tekstil, Oyuncak, Makine vb.) girdiğini belirle.
    2. Olası GTİP kodunu yaz.
    3. Gümrük Vergisi, KDV, ÖTV (varsa), Gümrük Müşavirlik ve Ardiye masraflarını içeren detaylı bir tablo oluştur.
    4. Navlun (Nakliye) maliyetini tahmin et.
    5. TOPLAM MALİYETİ ve ÜRÜN BAŞI MALİYETİ hesapla.
    6. 'Karlılık Analizi': Bu ürün Türkiye pazarında satılır mı? Esnaf tavsiyesi ver.
    
    Yanıtı çok şık bir markdown formatında, tablolar kullanarak ver.
    """

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Sen dünyanın en iyi lojistik ve gümrük danışmanısın. Kullanıcıya para kazandıracak bilgiler verirsin."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
        )
        return {"analiz": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
