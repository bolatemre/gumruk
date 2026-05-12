import streamlit as st
import mysql.connector
import requests
import time

# --- VERİTABANI BAĞLANTISI ---
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
    except Exception:
        return None

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Lojistik & Gümrük Borsası", page_icon="🏢", layout="wide")

# --- SESSION STATE ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_type = None
    st.session_state.user_name = None
    st.session_state.temp_res = None
    st.session_state.last_calc = None

# --- GELİŞMİŞ CSS (TASARIMI DÜZELTEN KISIM) ---
st.markdown("""
    <style>
    /* Arka Plan ve Genel Font */
    .stApp { background-color: #f0f2f6; }
    
    /* Kart Tasarımları */
    .premium-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        border-left: 8px solid #1e3a8a;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* Flu Efekti (Bozulmayan Kısım) */
    .blur-text { 
        filter: blur(5px); 
        opacity: 0.4; 
        user-select: none; 
        pointer-events: none;
    }

    /* Teklif Kutuları */
    .offer-item {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }

    /* Başlıklar ve Yazılar */
    h1, h2, h3 { color: #1e3a8a !important; font-family: 'Inter', sans-serif; }
    .info-label { color: #64748b; font-size: 11px; font-weight: 700; text-transform: uppercase; }
    .info-value { color: #1e293b; font-size: 15px; font-weight: 700; }
    
    /* Butonlar */
    .stButton>button {
        background-color: #1e3a8a;
        color: white;
        border-radius: 8px;
        height: 3em;
        width: 100%;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover { background-color: #2563eb; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. DURUM: ZİYARETÇİ VE GİRİŞ ---
if not st.session_state.user_id:
    tab_calc, tab_auth = st.tabs(["📊 Hızlı Analiz", "🔑 Giriş / Kayıt"])
    
    with tab_calc:
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.subheader("İthalat Verilerini Girin")
            with st.container(border=True):
                u = st.text_input("Ürün İsmi", placeholder="Örn: Akıllı Saat")
                yuk = st.selectbox("Yükleme Tipi", ["Parsiyel", "Konteyner", "Hava", "Kurye"])
                f_col, a_col, k_col = st.columns(3)
                fv = f_col.number_input("Birim $")
                av = a_col.number_input("Adet", step=1)
                kv = k_col.number_input("Toplam KG")
                if st.button("Maliyeti Analiz Et 🚀"):
                    with st.spinner("AI Hesaplıyor..."):
                        res = requests.post("http://localhost:8000/hesapla", json={"isim": f"{u} ({yuk})", "fiyat": fv, "adet": av, "agirlik": kv})
                        if res.status_code == 200:
                            st.session_state.temp_res = res.json()["analiz"]
                            st.session_state.last_calc = {"isim": u, "fiyat": fv, "adet": av, "agirlik": kv, "yukleme_tipi": yuk}
        
        with col2:
            st.subheader("📊 Analiz Ön İzleme")
            if st.session_state.temp_res:
                st.success("✅ Tahmini Rapor Hazır!")
                st.markdown(f"<div>{st.session_state.temp_res[:150]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='blur-text'>{st.session_state.temp_res[150:600]}</div>", unsafe_allow_html=True)
                st.info("🔒 Tam rapor ve navlun teklifleri için Giriş Yapın.")
            else:
                st.info("Formu doldurduğunuzda AI raporu burada belirecek.")

    with tab_auth:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### Giriş Yap")
            le = st.text_input("E-posta", key="login_email")
            lp = st.text_input("Şifre", type="password", key="login_pass")
            if st.button("Sisteme Giriş Yap"):
                with st.status("Doğrulanıyor...", expanded=False) as s:
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
            st.markdown("### Üye Ol")
            ri = st.text_input("Ad Soyad / Firma")
            re = st.text_input("E-posta", key="reg_email")
            rp = st.text_input("Şifre", type="password", key="reg_pass")
            rtel = st.text_input("Telefon")
            rt = st.selectbox("Rolünüz", ["musteri", "lojistik_firmasi", "gumruk_musaviri"])
            if st.button("Kayıt Ol"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, email, password, user_type, phone) VALUES (%s,%s,%s,%s,%s)", (ri, re, rp, rt, rtel))
                    conn.commit()
                    st.success("Kayıt başarılı! Şimdi giriş yapabilirsiniz.")

# --- 2. DURUM: MÜŞTERİ PANELİ ---
elif st.session_state.user_type == 'musteri':
    st.header("🏢 İthalatçı Kontrol Paneli")
    # Müşteri ekranı kodları (Ayrılmış teklifler ve analizler)
    # ... (Önceki kararlı sürümdeki müşteri paneli buraya gelecek)

# --- 3. DURUM: FİRMA PANELİ ---
else:
    st.header(f"🏢 {st.session_state.user_type.upper()} DASHBOARD")
    # Firma ekranı kodları (Filtreli ilanlar ve teklif verme)
    # ... (Önceki kararlı sürümdeki firma paneli buraya gelecek)

# SIDEBAR ÇIKIŞ
if st.session_state.user_id:
    st.sidebar.write(f"Hoş geldin, **{st.session_state.user_name}**")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.clear()
        st.rerun()
