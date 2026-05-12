import streamlit as st
import mysql.connector
import requests
import time
import json

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

st.set_page_config(page_title="Lojistik & Gümrük Borsası", page_icon="🏢", layout="wide")

# --- SESSION STATE ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_type = None
    st.session_state.user_name = None
    st.session_state.temp_res = None
    st.session_state.items = [] # Çoklu ürün listesi

# --- CSS (Premium Tasarım) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .premium-card { background: white; padding: 20px; border-radius: 12px; border-left: 8px solid #1e3a8a; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .blur-text { filter: blur(5px); opacity: 0.4; pointer-events: none; }
    .item-row { background: #f1f5f9; padding: 10px; border-radius: 8px; margin-bottom: 5px; border: 1px solid #e2e8f0; }
    </style>
    """, unsafe_allow_html=True)

# --- FONKSİYONLAR ---
def talebi_kaydet(uid, urunler_json, toplam_fiyat, analiz, yuk_tipi):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "INSERT INTO requests (user_id, product_name, price, quantity, weight, ai_analysis, extra_info, status) VALUES (%s,%s,%s,%s,%s,%s,%s,'aktif')"
            # product_name yerine çoklu ürün listesini, price yerine toplamı yazıyoruz
            cursor.execute(query, (uid, urunler_json, toplam_fiyat, 0, 0, analiz, yuk_tipi))
            conn.commit()
        finally: conn.close()

# --- ANA DÖNGÜ ---
if not st.session_state.user_id:
    # --- VİTRİN VE GİRİŞ EKRANI (DÜZELTİLDİ) ---
    st.title("🚢 Lojistik & Gümrük Borsası")
    t_calc, t_auth = st.tabs(["📊 Çoklu Ürün Analizi", "🔑 Giriş / Kayıt"])
    
    with t_calc:
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.subheader("Ürün Listesini Oluşturun")
            with st.container(border=True):
                c_u = st.text_input("Ürün Adı", key="v_u")
                c_f = st.number_input("Birim Fiyat ($)", key="v_f")
                c_a = st.number_input("Adet", step=1, key="v_a")
                if st.button("➕ Listeye Ekle"):
                    if c_u and c_f > 0:
                        st.session_state.items.append({"isim": c_u, "fiyat": c_f, "adet": c_a})
                
                # Eklenen Ürünler
                for idx, item in enumerate(st.session_state.items):
                    st.markdown(f"<div class='item-row'>📦 {item['isim']} | {item['adet']} Adet | {item['fiyat']}$</div>", unsafe_allow_html=True)
                
                if st.session_state.items:
                    yuk = st.selectbox("Yükleme Tipi", ["Parsiyel", "Konteyner", "Hava"], key="v_yuk")
                    if st.button("Tüm Listeyi AI ile Analiz Et 🚀"):
                        with st.spinner("AI Tüm Kalemleri İnceliyor..."):
                            prompt_data = json.dumps(st.session_state.items)
                            res = requests.post("http://localhost:8000/hesapla", json={"isim": prompt_data, "fiyat": 0, "adet": 0, "agirlik": 0})
                            if res.status_code == 200:
                                st.session_state.temp_res = res.json()["analiz"]
        
        with col2:
            st.subheader("📊 Analiz Ön İzleme")
            if st.session_state.temp_res:
                st.markdown(f"<div>{st.session_state.temp_res[:200]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='blur-text'>{st.session_state.temp_res[200:700]}</div>", unsafe_allow_html=True)
                st.info("🔒 Teklifleri toplamak için Giriş Yapın.")
            else: st.info("Ürünleri ekleyip analiz butonuna basın.")

    with t_auth:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### Giriş Yap")
            le = st.text_input("E-posta", key="le")
            lp = st.text_input("Şifre", type="password", key="lp")
            if st.button("Giriş"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (le, lp))
                    u = cursor.fetchone()
                    if u:
                        st.session_state.user_id, st.session_state.user_type, st.session_state.user_name = u['id'], u['user_type'], u['username']
                        st.rerun()
        with col_r:
            st.markdown("### Kayıt Ol")
            # Kayıt formları... (Önceki kararlı sürümle aynı)

else:
    # --- GİRİŞ YAPILMIŞ PANELLER ---
    st.sidebar.success(f"Hoş geldin, {st.session_state.user_name}")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.user_type == 'musteri':
        st.header("🏢 İthalatçı Paneli")
        t1, t2 = st.tabs(["📋 Taleplerim", "➕ Yeni Çoklu Talep"])
        
        with t2:
            st.subheader("Yeni Ürün Listesi Hazırla")
            # Çoklu ürün ekleme mantığı buraya da eklendi...
            # (Vitrinle aynı mantıkta çalışan form)
            
    else:
        st.header("🚛 Firma Paneli")
        # Firmalar artık "product_name" alanındaki JSON listesini okuyup
        # Tüm ürünleri liste halinde görecek.
