import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
import uvicorn

app = FastAPI()

# API anahtarını Render'daki Environment Variables'dan çeker
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    # Eğer environment variable set edilmemişse hata vermemesi için boş bırakıyoruz
    # Ama Render panelinde mutlaka eklemelisin
    client = None
else:
    client = Groq(api_key=api_key)

class UrunGiris(BaseModel):
    isim: str
    fiyat: float
    adet: int
    agirlik: float
    kategori: str

@app.post("/hesapla")
async def analiz_et(urun: UrunGiris):
    if not client:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY bulunamadı.")

    toplam_fiyat = urun.fiyat * urun.adet
    
    # AI'ya gönderilecek talimat
    prompt = f"""
    Ürün: {urun.isim}
    Kategori: {urun.kategori}
    Birim Fiyat: {urun.fiyat} USD
    Adet: {urun.adet}
    Toplam Mal Bedeli: {toplam_fiyat} USD
    Toplam Ağırlık: {urun.agirlik} KG
    
    Analiz talebi:
    1. Bu ürün için en uygun GTİP kodunu tahmin et.
    2. Türkiye için yaklaşık Gümrük Vergisi, KDV ve varsa ek yükümlülükleri hesapla.
    3. Çin-Türkiye arası ortalama navlun maliyetini ekle.
    4. Toplam 'Kapı Teslim' maliyetini çıkar ve ürünün karlılığı hakkında kısa bir esnaf yorumu yap.
    """

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Sen kıdemli bir gümrük müşaviri ve lojistik uzmanısın. Net ve teknik bilgiler ver."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant2",
        )
        return {"analiz": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
