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

# --- GELİŞMİŞ CSS (ÇİZGİLERİ GERİ GETİREN KISIM) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    
    /* Form Kutusu ve Çizgileri */
    .custom-form {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 15px;
        border: 2px solid #e2e8f0; /* Çizgi rengi ve kalınlığı */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    /* Analiz Kartı */
    .report-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        border-left: 8px solid #1e3a8a;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    .blur-text { filter: blur(5px); opacity: 0.4; user-select: none; }
    
    h1, h2, h3 { color: #1e3a8a !important; }
    
    /* Buton Tasarımı */
    .stButton>button {
        background-color: #1e3a8a;
        color: white;
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #2563eb; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🚢 Lojistik & Gümrük Borsası")
st.divider()

# --- 1. DURUM: ZİYARETÇİ ---
if not st.session_state.user_id:
    tab_calc, tab_auth = st.tabs(["📊 Hızlı Analiz", "🔑 Giriş / Kayıt"])
    
    with tab_calc:
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.markdown("### İthalat Verilerini Girin")
            # HTML Div kullanarak kutu içine alıyoruz
            st.markdown('<div class="custom-form">', unsafe_allow_html=True)
            u = st.text_input("Ürün İsmi", placeholder="Örn: Akıllı Saat", key="v_u")
            yuk = st.selectbox("Yükleme Tipi", ["Parsiyel", "Konteyner", "Hava", "Kurye"], key="v_yuk")
            f_col, a_col, k_col = st.columns(3)
            fv = f_col.number_input("Birim $", key="v_f")
            av = a_col.number_input("Adet", step=1, key="v_a")
            kv = k_col.number_input("Toplam KG", key="v_k")
            
            if st.button("Maliyeti Analiz Et 🚀", key="v_btn"):
                if u and fv > 0:
                    with st.spinner("AI Hesaplıyor..."):
                        res = requests.post("http://localhost:8000/hesapla", json={"isim": f"{u} ({yuk})", "fiyat": fv, "adet": av, "agirlik": kv})
                        if res.status_code == 200:
                            st.session_state.temp_res = res.json()["analiz"]
                            st.session_state.last_calc = {"isim": u, "fiyat": fv, "adet": av, "agirlik": kv, "yukleme_tipi": yuk}
                else:
                    st.error("Lütfen ürün adını ve fiyatını girin.")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 📊 Analiz Ön İzleme")
            if st.session_state.temp_res:
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.success("✅ Tahmini Rapor Hazır!")
                st.markdown(f"<div>{st.session_state.temp_res[:150]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='blur-text'>{st.session_state.temp_res[150:600]}</div>", unsafe_allow_html=True)
                st.info("🔒 Tam rapor ve navlun teklifleri için Giriş Yapın.")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Formu doldurduğunuzda AI raporu burada belirecek.")

    with tab_auth:
        # Giriş ve Kayıt kodları (Önceki kararlı sürümden)
        # ...
        pass

# ... (Müşteri ve Firma panelleri önceki kararlı haliyle devam eder)
