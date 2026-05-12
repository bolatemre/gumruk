import streamlit as st
import mysql.connector
import requests
import datetime

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
    except Exception as e:
        return None

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="GümrükAsistanı B2B", page_icon="🚢", layout="wide")

# --- OTURUM HAFIZASI (SESSION STATE) ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_type = None
    st.session_state.user_name = None
    st.session_state.last_calculation = None # Vitrinde yapılan hesaplamayı tutar

# --- CSS ---
st.markdown("""
    <style>
    .report-card { background: white; padding: 20px; border-radius: 12px; border-left: 6px solid #1e3a8a; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .offer-card { background: #f0f7ff; padding: 15px; border-radius: 10px; border: 1px solid #007bff; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FONKSİYONLAR ---
def talebi_kaydet(uid, isim, fiyat, adet, agirlik):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "INSERT INTO requests (user_id, product_name, price, quantity, weight) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (uid, isim, fiyat, adet, agirlik))
        conn.commit()
        conn.close()

# --- HEADER & ÇIKIŞ ---
if st.session_state.user_id:
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user_name}**")
        if st.button("Güvenli Çıkış"):
            st.session_state.user_id = None
            st.rerun()

# --- MANTIK AKIŞI ---

# 1. DURUM: ZİYARETÇİ EKRANI (KİMSE GİRİŞ YAPMAMIŞ)
if not st.session_state.user_id:
    tab1, tab2 = st.tabs(["📊 Hızlı Hesapla", "🔑 Giriş / Kayıt"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("İthalat Verilerini Girin")
            with st.container(border=True):
                u = st.text_input("Ürün Adı", key="v_u")
                f = st.number_input("Birim Fiyat ($)", min_value=0.0, key="v_f")
                a = st.number_input("Adet", min_value=1, key="v_a")
                kg = st.number_input("Toplam KG", min_value=0.0, key="v_kg")
                if st.button("Maliyeti Analiz Et 🚀"):
                    # Verileri geçici hafızaya al
                    st.session_state.last_calculation = {"isim": u, "fiyat": f, "adet": a, "agirlik": kg}
                    res = requests.post("http://localhost:8000/hesapla", json=st.session_state.last_calculation)
                    if res.status_code == 200:
                        st.session_state.temp_res = res.json()["analiz"]
        with col2:
            if 'temp_res' in st.session_state:
                st.warning("🔒 Analizin tamamını görmek ve resmi teklif toplamak için GİRİŞ YAPIN.")
                st.markdown(f"<div class='report-card'>{st.session_state.temp_res[:200]}...</div>", unsafe_allow_html=True)
            else:
                st.info("Ürün bilgilerini girerek tahmini maliyeti görebilirsiniz.")

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
                        # EĞER HAFIZADA HESAPLAMA VARSA OTOMATİK KAYDET
                        if st.session_state.last_calculation:
                            talebi_kaydet(user['id'], **st.session_state.last_calculation)
                        st.rerun()
                    else: st.error("Hatalı bilgiler.")

        with col_r:
            st.subheader("Ücretsiz Kayıt Ol")
            ri = st.text_input("İsim / Firma", key="r_i")
            re = st.text_input("Email", key="r_e")
            rp = st.text_input("Şifre", type="password", key="r_p")
            rt = st.selectbox("Rolünüz", ["musteri", "lojistik_firmasi", "gumruk_musaviri"], key="r_t")
            if st.button("Kayıt Ol"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, email, password, user_type) VALUES (%s,%s,%s,%s)", (ri, re, rp, rt))
                    conn.commit()
                    st.success("Kayıt başarılı! Şimdi giriş yapın.")

# 2. DURUM: MÜŞTERİ (İTHALATÇI) PANELİ
elif st.session_state.user_type == 'musteri':
    st.header("🏢 Müşteri Paneli")
    m_tab1, m_tab2 = st.tabs(["📋 Teklif Taleplerim", "➕ Yeni Teklif Al"])
    
    with m_tab1:
        st.subheader("Eski Talepleriniz ve Gelen Teklifler")
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM requests WHERE user_id = %s ORDER BY created_at DESC", (st.session_state.user_id,))
            talepler = cursor.fetchall()
            for t in talepler:
                with st.expander(f"📦 {t['product_name']} - {t['created_at'].strftime('%d/%m/%Y')}"):
                    st.write(f"**Detay:** {t['quantity']} Adet | {t['price']}$ Birim Fiyat | {t['weight']} KG")
                    # Bu talebe gelen teklifleri çek
                    cursor.execute("SELECT * FROM offers WHERE request_id = %s", (t['id'],))
                    teklifler = cursor.fetchall()
                    if not teklifler:
                        st.info("Henüz teklif gelmedi. Firmaların incelemesi bekleniyor.")
                    else:
                        for o in teklifler:
                            st.markdown(f"""<div class='offer-card'>💰 Teklif: {o['offer_amount']}$ | 🕒 Süre: {o['delivery_days']} Gün<br>📝 Not: {o['firm_note']}</div>""", unsafe_allow_html=True)
            conn.close()

    with m_tab2:
        st.subheader("Yeni Bir İthalat Maliyeti Hesapla & Teklif Topla")
        with st.container(border=True):
            nu = st.text_input("Ürün", key="nu")
            nf = st.number_input("Birim Fiyat ($)", key="nf")
            na = st.number_input("Adet", key="na")
            nk = st.number_input("Toplam KG", key="nk")
            if st.button("Hesapla ve İlana Çık 🚀"):
                talebi_kaydet(st.session_state.user_id, nu, nf, na, nk)
                st.success("Talebiniz kaydedildi ve firmalara iletildi!")
                st.rerun()

# 3. DURUM: FİRMA PANELİ (LOJİSTİK/GÜMRÜK)
else:
    st.header("🚛 Firma Teklif Borsası")
    st.info("Aşağıdaki talepler için fiyat teklifi verebilirsiniz.")
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id ORDER BY r.created_at DESC")
        ilanlar = cursor.fetchall()
        for i in ilanlar:
            with st.expander(f"📦 {i['product_name']} - Müşteri: {i['username']}"):
                st.write(f"**Detay:** {i['quantity']} Adet | {i['price']}$ Birim Fiyat | {i['weight']} KG")
                with st.form(key=f"form_{i['id']}"):
                    t_fiyat = st.number_input("Teklifiniz ($)", min_value=0.0)
                    t_gun = st.number_input("Teslim Süresi (Gün)", min_value=1)
                    t_not = st.text_area("Notunuz")
                    if st.form_submit_button("Teklifi Gönder"):
                        cursor.execute("INSERT INTO offers (request_id, firm_id, offer_amount, delivery_days, firm_note) VALUES (%s, %s, %s, %s, %s)", 
                                     (i['id'], st.session_state.user_id, t_fiyat, t_gun, t_not))
                        conn.commit()
                        st.success("Teklifiniz başarıyla iletildi!")
        conn.close()
