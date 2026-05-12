import streamlit as st
import requests

st.set_page_config(page_title="GümrükAsistanı AI", page_icon="📈", layout="wide")

# Tasarım CSS (Daha profesyonel görünüm)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_stdio=True)

st.title("🤖 GümrükAsistanı: Yapay Zeka Destekli İthalat Analizi")
st.subheader("Ürün bilgilerini girin, gümrükten kapınıza kadar maliyeti hesaplayalım.")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2854/2854611.png", width=100)
    st.info("Bu bot, güncel gümrük mevzuatı ve lojistik verilerini kullanarak simülasyon yapar.")
    st.warning("Resmi işlemler için mutlaka bir gümrük müşavirine danışın.")

col1, col2 = st.columns([1, 1])

with col1:
    with st.expander("📦 Ürün Detayları", expanded=True):
        urun_adi = st.text_input("Ürün Adı", placeholder="Örn: Elektrikli Kaykay")
        fiyat = st.number_input("Birim Alış Fiyatı (USD)", min_value=0.0)
        adet = st.number_input("Adet", min_value=1, step=1)
        agirlik = st.number_input("Toplam Ağırlık (KG)", min_value=0.0)
    
    analiz_butonu = st.button("Maliyet Analizini Başlat")

with col2:
    if analiz_butonu:
        if not urun_adi:
            st.error("Lütfen bir ürün adı girin.")
        else:
            with st.spinner("AI Gümrük Mevzuatını ve Navlunları Tarıyor..."):
                try:
                    res = requests.post("http://localhost:8000/hesapla", 
                                     json={"isim": urun_adi, "fiyat": fiyat, "adet": adet, "agirlik": agirlik})
                    if res.status_code == 200:
                        st.success("Analiz Hazır!")
                        st.markdown(res.json()["analiz"])
                    else:
                        st.error("Bir hata oluştu, lütfen tekrar deneyin.")
                except:
                    st.error("Sunucuya bağlanılamadı.")
    else:
        st.write("👈 Analiz sonuçları burada görünecek.")
