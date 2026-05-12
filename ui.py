import streamlit as st
import mysql.connector
import requests

# SQL Bağlantısı
DB_CONFIG = {
    "host": "72.60.86.17", 
    "user": "u115468925_lojistik",
    "password": "l123456M.",
    "database": "u115468925_lojistik",
    "port": 3306
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        return None

# Sayfa Ayarları
st.set_page_config(page_title="GümrükAsistanı B2B", page_icon="🚢", layout="wide")

# CSS: Tasarımı toparla
st.markdown("""
    <style>
    .report-card { background: white; padding: 20px; border-radius: 12px; border-left: 6px solid #1e3a8a; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# OTURUM YÖNETİMİ
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_type = None
    st.session_state.user_name = None

# --- NAVİGASYON ---
if st.session_state.user_id:
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user_name}**")
        st.write(f"🏷️ Rol: {st.session_state.user_type.upper()}")
        if st.button("Güvenli Çıkış"):
            st.session_state.user_id = None
            st.rerun()
        st.divider()

# --- EKRAN MANTIĞI ---

# 1. DURUM: KİMSE GİRİŞ YAPMAMIŞ (VİTRİN)
if not st.session_state.user_id:
    tab1, tab2 = st.tabs(["📊 Hızlı Maliyet Hesapla", "🔑 Giriş / Kayıt"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Ürün Bilgilerini Girin")
            with st.container(border=True):
                u = st.text_input("Ürün Adı", key="u_vitrin")
                f = st.number_input("Birim Fiyat ($)", min_value=0.0, key="f_vitrin")
                a = st.number_input("Adet", min_value=1, key="a_vitrin")
                kg = st.number_input("Toplam KG", min_value=0.0, key="kg_vitrin")
                if st.button("Tahmini Analizi Gör 🚀", key="btn_vitrin"):
                    with st.spinner("AI Hesaplıyor..."):
                        res = requests.post("http://localhost:8000/hesapla", json={"isim": u, "fiyat": f, "adet": a, "agirlik": kg})
                        if res.status_code == 200:
                            st.session_state.temp_res = res.json()["analiz"]
        with col2:
            st.subheader("Analiz Ön İzleme")
            if 'temp_res' in st.session_state:
                st.warning("🔒 Detaylı vergi tablosu ve navlun teklifleri için giriş yapın.")
                st.markdown(f"<div class='report-card'>{st.session_state.temp_res[:250]}...</div>", unsafe_allow_html=True)
            else:
                st.info("Sol taraftan ürün bilgilerini girerek tahmini maliyeti görebilirsiniz.")

    with tab2:
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("Giriş Yap")
            le = st.text_input("Email", key="l_e")
            lp = st.text_input("Şifre", type="password", key="l_p")
            if st.button("Giriş"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (le, lp))
                    user = cursor.fetchone()
                    if user:
                        st.session_state.user_id = user['id']
                        st.session_state.user_type = user['user_type']
                        st.session_state.user_name = user['username']
                        st.rerun()
                    else: st.error("Hatalı bilgiler.")
        with col_r:
            st.subheader("Kayıt Ol")
            ri = st.text_input("İsim / Firma", key="r_i")
            re = st.text_input("Email", key="r_e")
            rp = st.text_input("Şifre", type="password", key="r_p")
            rt = st.selectbox("Rolünüz", ["musteri", "lojistik_firmasi", "gumruk_musaviri"], key="r_t")
            if st.button("Ücretsiz Üye Ol"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, email, password, user_type) VALUES (%s,%s,%s,%s)", (ri, re, rp, rt))
                    conn.commit()
                    st.success("Kayıt başarılı! Şimdi giriş yapabilirsiniz.")

# 2. DURUM: MÜŞTERİ GİRİŞ YAPMIŞ
elif st.session_state.user_type == 'musteri':
    st.header("🏢 Müşteri Yönetim Paneli")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Yeni İthalat Talebi Oluştur")
        with st.container(border=True):
            u_m = st.text_input("Ürün", key="u_m")
            f_m = st.number_input("Birim Fiyat ($)", key="f_m")
            a_m = st.number_input("Adet", key="a_m")
            kg_m = st.number_input("Toplam KG", key="kg_m")
            if st.button("Resmi Analizi Başlat 📈"):
                res = requests.post("http://localhost:8000/hesapla", json={"isim": u_m, "fiyat": f_m, "adet": a_m, "agirlik": kg_m})
                if res.status_code == 200:
                    st.session_state.m_res = res.json()["analiz"]
    with c2:
        st.subheader("Detaylı Gümrük Raporu")
        if 'm_res' in st.session_state:
            st.markdown(f"<div class='report-card'>{st.session_state.m_res}</div>", unsafe_allow_html=True)
            if st.button("🚀 Firmalardan Gerçek Teklifleri Topla"):
                st.success("Talebiniz Borsa Havuzuna iletildi! Firmalar sizinle panel üzerinden iletişime geçecek.")

# 3. DURUM: FİRMA GİRİŞ YAPMIŞ (Lojistik veya Gümrük)
else:
    st.header("🚛 Firma İş Havuzu (Borsa)")
    st.info("Aşağıda teklif bekleyen aktif ithalat talepleri listelenmiştir.")
    # Burada SQL'den çekilen ilanlar olacak
    with st.container(border=True):
        st.write("📦 **Talep #101: Akıllı Robot Süpürge (500 Adet)**")
        st.write("Güzergah: Shenzhen -> İstanbul | Ağırlık: 450 KG")
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("Teklif Ver"):
                st.write("Form açılıyor...")
