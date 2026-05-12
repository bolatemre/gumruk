import streamlit as st
import requests

# Sayfa ayarları
st.set_page_config(page_title="GümrükAsistanı AI", page_icon="📈", layout="wide")

# Tasarım CSS (Hata burada düzeltildi: unsafe_allow_html=True yapıldı)
st.markdown("""
    <style>
    /* Arka plan ve genel font */
    .main { background-color: #f0f2f6; }
    
    /* Buton tasarımı */
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        background-color: #007bff; 
        color: white; 
        height: 3em;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        color: white;
    }
    
    /* Başlık stili */
    h1 { color: #1e3a8a; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Sonuç kutusu stili */
    .report-box {
        padding: 20px;
        background-color: white;
        border-radius: 15px;
        border-left: 5px solid #007bff;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Üst Başlık Alanı
st.title("🤖 GümrükAsistanı: Akıllı İthalat Analizi")
st.subheader("Ürün detaylarını girin, gümrük ve lojistik maliyetlerini saniyeler içinde hesaplayalım.")

# Yan Menü (Sidebar)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2854/2854611.png", width=100)
    st.markdown("### Sistem Notları")
    st.info("💡 **İpucu:** Ürün adını ne kadar detaylı yazarsanız (örn: 'Lityum iyon pilli robot süpürge') AI o kadar doğru GTİP tahmini yapar.")
    st.warning("⚠️ Bu hesaplamalar simülasyon amaçlıdır. 2026 güncel mevzuatı temel alınır.")
    st.divider()
    st.markdown("🌐 **Lira Markt** iştirakidir.")

# Ana Ekran Kolonları
col1, col2 = st.columns([2, 3], gap="large")

with col1:
    st.markdown("### 📋 Veri Girişi")
    with st.container(border=True):
        urun_adi = st.text_input("Ürün Adı", placeholder="Örn: 4K Ultra HD Projeksiyon Cihazı")
        
        # Sayısal girişler için yan yana kolonlar
        c1, c2 = st.columns(2)
        with c1:
            fiyat = st.number_input("Birim Alış (USD)", min_value=0.0, step=0.1, format="%.2f")
            adet = st.number_input("Adet", min_value=1, step=1)
        with c2:
            agirlik = st.number_input("Toplam Ağırlık (KG)", min_value=0.0, step=0.1)
            # Para birimi sabit USD olarak kurgulandı
    
    analiz_butonu = st.button("Maliyet Analizini Başlat 🚀")

with col2:
    st.markdown("### 📊 Analiz Raporu")
    if analiz_butonu:
        if not urun_adi or fiyat == 0:
            st.error("Lütfen ürün adını ve fiyatını geçerli şekilde girin.")
        else:
            with st.spinner("AI Gümrük Mevzuatını (İGV, KDV, ÖTV) ve Navlun Fiyatlarını Hesaplanıyor..."):
                try:
                    # Backend API bağlantısı (main.py'ye gider)
                    res = requests.post("http://localhost:8000/hesapla", 
                                     json={
                                         "isim": urun_adi, 
                                         "fiyat": fiyat, 
                                         "adet": int(adet), 
                                         "agirlik": agirlik
                                     })
                    
                    if res.status_code == 200:
                        st.success("Hesaplama Başarılı!")
                        # AI'dan gelen markdown içeriğini şık bir kutu içinde gösteriyoruz
                        st.markdown(f'<div class="report-box">{res.json()["analiz"]}</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"API Hatası: {res.status_code}. Lütfen backend'i kontrol edin.")
                except Exception as e:
                    st.error(f"Bağlantı Hatası: Sunucuya ulaşılamadı. (Detay: {e})")
    else:
        st.info("Analiz sonuçlarını görmek için sol taraftaki formu doldurup butona basın.")

# Alt Bilgi
st.divider()
st.caption("© 2026 GümrükAsistanı AI | Tüm maliyetler USD bazlı tahmini rakamlardır.")
