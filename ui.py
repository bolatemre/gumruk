import streamlit as st
import requests

# Sayfa Yapısı
st.set_page_config(page_title="İthalat Borsası | Gümrük & Lojistik", layout="wide")

# Kurumsal Tema
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .auth-card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); text-align: center; border-top: 5px solid #1e3a8a; }
    .price-box { background: #e0f2fe; padding: 15px; border-radius: 10px; border-left: 5px solid #0284c7; }
    </style>
    """, unsafe_allow_html=True)

# Session State (Oturum Yönetimi)
if 'user_type' not in st.session_state:
    st.session_state.user_type = None # 'musteri', 'firma' veya None

# --- HEADER / NAV ---
t1, t2 = st.columns([4, 1])
with t1:
    st.title("🚢 GümrükAsistanı: Dijital Lojistik Borsası")
with t2:
    if st.session_state.user_type:
        if st.button("Çıkış Yap"):
            st.session_state.user_type = None
            st.rerun()

# --- ANA SAYFA / HESAPLAMA ---
if st.session_state.user_type != 'firma':
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("📦 Maliyet Hesapla")
        with st.container(border=True):
            urun = st.text_input("Getirmek istediğiniz ürün?", placeholder="Örn: CNC Lazer Kesim Makinesi")
            fiyat = st.number_input("Birim Alış Fiyatı (USD)", min_value=0.0)
            adet = st.number_input("Adet", min_value=1, step=1)
            agirlik = st.number_input("Toplam KG", min_value=0.0)
            hesapla = st.button("Analizi Göster 🚀")

    with col2:
        st.subheader("📊 Gümrük & Navlun Raporu")
        if hesapla:
            with st.spinner("Güncel mevzuat taranıyor..."):
                res = requests.post("http://localhost:8000/hesapla", json={"isim": urun, "fiyat": fiyat, "adet": adet, "agirlik": agirlik})
                if res.status_code == 200:
                    analiz = res.json()["analiz"]
                    
                    if not st.session_state.user_type:
                        # GİRİŞ YAPILMAMIŞSA BARİYER
                        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
                        st.warning("🔒 Analiz sonuçlarını ve firma tekliflerini görmek için giriş yapmalısınız.")
                        st.markdown("### Giriş Yap veya Kayıt Ol")
                        c1, c2 = st.columns(2)
                        if c1.button("Müşteri Olarak Giriş"):
                            st.session_state.user_type = 'musteri'
                            st.rerun()
                        if c2.button("Lojistik Firması Kaydı"):
                            st.session_state.user_type = 'firma'
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        # MÜŞTERİ GİRİŞİ YAPILMIŞSA
                        st.success("Analiz Tamamlandı!")
                        st.markdown(f"<div class='price-box'>{analiz}</div>", unsafe_allow_html=True)
                        st.divider()
                        st.markdown("### 📢 Teklif İste")
                        st.write("Bu ürün için gümrük ve lojistik firmalarından teklif toplansın mı?")
                        if st.button("Teklif Talebi Oluştur (Ücretsiz)"):
                            st.balloons()
                            st.info("Talebiniz sistemdeki 50+ firmaya iletildi. Teklifler panelinize düşecek.")

# --- FİRMA PANELİ ---
if st.session_state.user_type == 'firma':
    st.header("🏢 Firma Teklif Paneli")
    st.info("Aşağıdaki talepler için fiyat teklifi verebilirsiniz. Müşteri iletişim bilgileri teklif kabulünden sonra açılır.")
    
    # Örnek Talep Listesi (Burayı ileride MySQL'den çekeceğiz)
    with st.container(border=True):
        st.write("**Talep #204: 100 Adet Elektrikli Kaykay (Çin - İstanbul)**")
        st.write("Müşteri: Emre C.")
        
        # TEKLİF VERME FORMU
        with st.expander("Teklif Ver"):
            t_fiyat = st.number_input("Hizmet Bedeliniz (USD)", min_value=0.0, key="fiyat_204")
            t_sure = st.number_input("Varış Süresi (Gün)", min_value=1, key="sure_204")
            t_not = st.text_area("Notunuz", placeholder="Ardiye masrafları hariçtir...", key="not_204")
            if st.button("Teklifi Gönder"):
                st.success("Teklifiniz başarıyla iletildi!")
