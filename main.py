import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
import uvicorn

app = FastAPI()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class AnalizIstegi(BaseModel):
    isim: str
    fiyat: float
    adet: int
    agirlik: float

@app.post("/hesapla")
async def analiz_et(istek: AnalizIstegi):
    # 2026 GÜNCEL MEVZUAT TALİMATI
    prompt = f"""
    TÜRKİYE 2026 GÜMRÜK VE DIŞ TİCARET REJİMİNE GÖRE HESAPLA:
    Ürün: {istek.isim} | Alış Fiyatı: {istek.fiyat} USD | Adet: {istek.adet} | Ağırlık: {istek.agirlik} KG
    
    ZORUNLU HESAPLAMA PARAMETRELERİ:
    1. Gümrük Vergisi: Çin menşei için %60 İGV (İlave Gümrük Vergisi) ekle.
    2. KDV: %20 olarak hesapla.
    3. Ek Masraflar: Damga vergisi, Gümrüğe sunma ve Ardiye masrafları için toplam maktu 120 USD ekle.
    4. Navlun (USD): KG başı 6 USD üzerinden tahmini kargo bedeli çıkar.
    5. ÇIKTI: Sadece USD ($) cinsinden, net bir tablo ve kısa esnaf yorumu olsun.
    """

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Sen çok tecrübeli bir gümrük müşavirisin. 2026 yılı güncel vergi oranlarını ve dolar bazlı maliyetleri kullanırsın."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
        )
        return {"analiz": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
