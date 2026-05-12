import streamlit as st
import requests
import time

st.set_page_config(page_title="Lojistik & Gümrük Botu", page_icon="🚢")

st.title("🚢 Lojistik & Gümrük Danışman Botu")
st.markdown("Çin'den getirmek istediğiniz ürünlerin maliyetini anında hesaplayın.")

# Yan menü veya açıklama
with st.sidebar:
    st.header("Nasıl Çalışır?")
    st.write("Verileri manuel girin, AI gümrük mevzuatına göre size bir maliyet simülasyonu çıkarsın.")
    st.info("Not: Bu veriler tahmindir, yatırım tavsiyesi değildir.")

# Form yapısı
with st.form("ithalat_formu"):
    urun_adi = st.text_input("Ürün Adı (Örn: Bluetooth Kulaklık)")
    kategori = st.selectbox("Ürün Kategorisi", ["Elektronik", "Tekstil", "Plastik Ürünler", "Mutfak Gereçleri", "Makine Parçaları", "Diğer"])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        birim_fiyat = st.number_input("Birim Fiyat (USD)", min_value=0.01, format="%.2f")
    with col2:
        adet = st.number_input("Adet", min_value=1, step=1)
    with col3:
        agirlik = st.number_input("Toplam KG", min_value=0.1)

    submit = st.form_submit_button("Maliyeti Analiz Et")

if submit:
    if not urun_adi:
        st.error("Lütfen ürün adını girin.")
    else:
        with st.spinner("Gümrük verileri ve lojistik maliyetleri hesaplanıyor..."):
            payload = {
                "isim": urun_adi,
                "fiyat": birim_fiyat,
                "adet": adet,
                "agirlik": agirlik,
                "kategori": kategori
            }
            
            try:
                # Render içinde backend 8000 portunda çalışacak
                response = requests.post("http://localhost:8000/hesapla", json=payload)
                
                if response.status_code == 200:
                    sonuc = response.json().get("analiz")
                    st.success("Analiz Başarıyla Tamamlandı!")
                    st.markdown("### 📊 Maliyet ve Gümrük Raporu")
                    st.markdown(sonuc)
                else:
                    st.error(f"Bir hata oluştu: {response.text}")
            except Exception as e:
                st.error(f"Sunucu bağlantı hatası: {e}")