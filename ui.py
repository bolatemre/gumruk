import streamlit as st
import mysql.connector
import requests
import time

# --- VERİTABANI ---
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
st.set_page_config(page_title="Lojistik & Gümrük Borsası", page_icon="🚢", layout="wide")

# --- SESSION STATE (BAŞLANGIÇ) ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_type = None
    st.session_state.user_name = None
    st.session_state.temp_res = None
    st.session_state.last_calc = None

# --- GELİŞMİŞ CSS (BEYAZ KUTU VE ÇİZGİ DÜZELTMELERİ) ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    
    /* Form ve Kutuların Sabitlenmesi */
    .custom-box {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        border: 2px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* Flu Efekti */
    .blur-text { filter: blur(5px); opacity: 0.4; pointer-events: none; }
    
    /* Kurumsal Başlıklar */
    h1, h2, h3 { color: #1e3a8a !important; font-weight: 800; }
    
    /* Sekme (Tab) Yazılarını Belirginleştir */
    .stTabs [data-baseweb="tab"] { font-size: 18px; font-weight: 700; color: #475569; }
    .stTabs [aria-selected="true"] { color: #1e3a8a !important; border-bottom-color: #1e3a8a !important; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🚢 Lojistik & Gümrük Borsası")
st.divider()

# --- ANA MANTIK ---

if not st.session_state.user_id:
    # GİRİŞ YAPILMAMIŞSA
    tab_ana, tab_auth = st.tabs(["📊 Hızlı Analiz", "🔐 Giriş / Kayıt"])
    
    with tab_ana:
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.markdown("### İthalat Verilerini Girin")
            # Kutuyu HTML ile manuel çiziyoruz ki Streamlit bozmasın
            with st.container(border=True):
                u = st.text_input("Ürün İsmi", placeholder="Örn: Akıllı Saat", key="vit_u")
                yuk = st.selectbox("Yükleme Tipi", ["Parsiyel", "Konteyner", "Hava", "Kurye"], key="vit_yuk")
                c1, c2, c3 = st.columns(3)
                fv = c1.number_input("Birim $", key="vit_f")
                av = c2.number_input("Adet", step=1, key="vit_a")
                kv = c3.number_input("Toplam KG", key="vit_k")
                
                if st.button("Maliyeti Analiz Et 🚀", key="vit_btn"):
                    if u and fv > 0:
                        with st.spinner("AI Hesaplıyor..."):
                            res = requests.post("http://localhost:8000/hesapla", json={"isim": f"{u} ({yuk})", "fiyat": fv, "adet": av, "agirlik": kv})
                            if res.status_code == 200:
                                st.session_state.temp_res = res.json()["analiz"]
                                st.session_state.last_calc = {"isim": u, "fiyat": fv, "adet": av, "agirlik": kv, "yukleme_tipi": yuk}
                                st.rerun() # Sayfayı yenileyerek sonucu göster
        
        with col2:
            st.markdown("### 📊 Analiz Ön İzleme")
            if st.session_state.temp_res:
                with st.container(border=True):
                    st.success("✅ Tahmini Rapor Hazır!")
                    st.markdown(f"<div>{st.session_state.temp_res[:150]}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='blur-text'>{st.session_state.temp_res[150:600]}</div>", unsafe_allow_html=True)
                    st.info("🔒 Tam rapor ve navlun teklifleri için Giriş Yapın.")
            else:
                st.info("Formu doldurduğunuzda AI raporu burada belirecek.")

    with tab_auth:
        # GİRİŞ / KAYIT EKRANI
        col_login, col_reg = st.columns(2, gap="large")
        
        with col_login:
            st.markdown("### Giriş Yap")
            with st.container(border=True):
                le = st.text_input("E-posta", key="log_e")
                lp = st.text_input("Şifre", type="password", key="log_p")
                if st.button("Sisteme Giriş Yap", key="log_btn"):
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
                        else:
                            st.error("Hatalı e-posta veya şifre.")
                        conn.close()

        with col_reg:
            st.markdown("### Üye Ol")
            with st.container(border=True):
                ri = st.text_input("Ad Soyad / Firma", key="reg_i")
                re = st.text_input("E-posta", key="reg_e")
                rp = st.text_input("Şifre", type="password", key="reg_p")
                rt = st.selectbox("Rolünüz", ["musteri", "lojistik_firmasi", "gumruk_musaviri"], key="reg_t")
                if st.button("Kayıt Ol", key="reg_btn"):
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users (username, email, password, user_type) VALUES (%s,%s,%s,%s)", (ri, re, rp, rt))
                        conn.commit()
                        st.success("Kayıt Başarılı! Şimdi giriş yapabilirsiniz.")
                        conn.close()

# --- GİRİŞ YAPILMIŞSA ---
else:
    # Sidebar ve Paneller (Müşteri/Firma)
    st.sidebar.success(f"Hoş geldin, {st.session_state.user_name}")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.clear()
        st.rerun()
    
    if st.session_state.user_type == 'musteri':
        st.header("🏢 İthalatçı Paneli")
        # Müşteri paneli kodlarını buraya ekleyebilirsin
    else:
        st.header("🚛 Firma Paneli")
        # Firma paneli kodlarını buraya ekleyebilirsin
