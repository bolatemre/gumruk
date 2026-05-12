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
    # En güncel Llama 3.3 Modeli
    prompt = f"""
    TÜRKİYE 2026 GÜMRÜK MEVZUATINA GÖRE ANALİZ:
    Ürün: {istek.isim} | Fiyat: {istek.fiyat} USD | Adet: {istek.adet} | Ağırlık: {istek.agirlik} KG
    
    HESAPLAMA DETAYLARI:
    - Çin Menşei ürünler için %60 İlave Gümrük Vergisi (İGV) uygula.
    - %20 KDV ekle.
    - 120 USD Sabit Gümrük Masrafı (Damga, Sunma, Ardiye) ekle.
    - Navlun: KG başı 6-8 USD arası tahmini navlun ekle.
    
    ÇIKTI FORMATI:
    - Kategori ve GTİP Tahmini
    - Vergi Tablosu (USD)
    - Navlun Tahmini (USD)
    - Toplam Kapı Teslim Maliyeti (USD)
    - Kısa Esnaf Yorumu (Karlılık Analizi)
    """

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Sen kıdemli bir gümrük müşavirisin. Cevapların net, profesyonel ve sadece USD cinsinden olsun."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
        )
        return {"analiz": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
