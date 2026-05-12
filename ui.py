import streamlit as st
import mysql.connector
import requests

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
st.set_page_config(page_title="GümrükAsistanı B2B", page_icon="🚢", layout="wide")

# --- SESSION STATE ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_type = None
    st.session_state.user_name = None
    st.session_state.temp_res = None
    st.session_state.last_calc = None

# --- CSS TASARIM ---
st.markdown("""
    <style>
    .report-card { background: white; padding: 20px; border-radius: 15px; border-left: 8px solid #1e3a8a; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-top:10px; }
    .blur-text { filter: blur(5px); opacity: 0.4; user-select: none; }
    .offer-box { background: #f0f7ff; padding: 15px; border-radius: 10px; border: 1px solid #0ea5e9; margin-bottom: 10px; position: relative; }
    .stButton>button { border-radius: 10px; font-weight: bold; }
    .status-badge { padding: 5px 10px; border-radius: 50px; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FONKSİYONLAR ---
def talebi_kaydet(uid, isim, fiyat, adet, agirlik, analiz, yukleme_tipi):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "INSERT INTO requests (user_id, product_name, price, quantity, weight, ai_analysis, extra_info) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (uid, isim, fiyat, adet, agirlik, analiz, yukleme_tipi))
            conn.commit()
        finally:
            conn.close()

def teklif_sil(teklif_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM offers WHERE id = %s", (teklif_id,))
        conn.commit()
        conn.close()

# --- SIDEBAR ---
if st.session_state.user_id:
    with st.sidebar:
        st.success(f"Giriş: {st.session_state.user_name}")
        if st.button("Güvenli Çıkış"):
            st.session_state.user_id = None
            st.rerun()

# --- 1. DURUM: ZİYARETÇİ ---
if not st.session_state.user_id:
    tab1, tab2 = st.tabs(["🔍 Hızlı Analiz", "🔑 Giriş / Kayıt"])
    with tab1:
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.subheader("Ürün ve Lojistik Bilgileri")
            with st.form("vitrin_form"):
                u = st.text_input("Ürün Adı", placeholder="Örn: Akıllı Saat")
                yuk_tipi = st.selectbox("Yükleme Tipi", ["Parsiyel (LCL)", "Tam Konteyner (FCL)", "Hava Kargo", "Kurye"])
                c1, c2 = st.columns(2)
                f = c1.number_input("Birim Fiyat ($)", min_value=0.0)
                a = c2.number_input("Adet", min_value=1, step=1)
                kg = st.number_input("Toplam Ağırlık (KG)")
                if st.form_submit_button("Analizi Gör ve Teklif Topla 🚀"):
                    res = requests.post("http://localhost:8000/hesapla", json={"isim": f"{u} ({yuk_tipi})", "fiyat": f, "adet": a, "agirlik": kg})
                    if res.status_code == 200:
                        st.session_state.temp_res = res.json()["analiz"]
                        st.session_state.last_calc = {"isim": u, "fiyat": f, "adet": a, "agirlik": kg, "yukleme_tipi": yuk_tipi}
        with col2:
            if st.session_state.temp_res:
                st.success("Analiz Hazır!")
                st.markdown(f"<div>{st.session_state.temp_res[:150]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='blur-text'>{st.session_state.temp_res[150:500]}</div>", unsafe_allow_html=True)
                st.info("🔒 Tam raporu görmek için Giriş Yapın.")
    with tab2:
        l, r = st.columns(2)
        with l:
            le, lp = st.text_input("Email", key="le"), st.text_input("Şifre", type="password", key="lp")
            if st.button("Giriş Yap"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (le, lp))
                    user = cursor.fetchone()
                    if user:
                        st.session_state.user_id, st.session_state.user_type, st.session_state.user_name = user['id'], user['user_type'], user['username']
                        if st.session_state.last_calc: talebi_kaydet(user['id'], **st.session_state.last_calc, analiz=st.session_state.temp_res)
                        st.rerun()
        with r:
            ri, re, rp = st.text_input("Firma/Ad"), st.text_input("Email", key="re"), st.text_input("Şifre", type="password", key="rp")
            rt = st.selectbox("Rol", ["musteri", "lojistik_firmasi", "gumruk_musaviri"])
            if st.button("Kayıt Ol"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, email, password, user_type) VALUES (%s,%s,%s,%s)", (ri, re, rp, rt))
                    conn.commit()
                    st.success("Kayıt başarılı!")

# --- 2. DURUM: MÜŞTERİ PANELİ ---
elif st.session_state.user_type == 'musteri':
    st.header("🏢 İthalatçı Paneli")
    tab_l, tab_n = st.tabs(["📋 Taleplerim & Gelen Teklifler", "➕ Yeni Talep"])
    with tab_l:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM requests WHERE user_id = %s ORDER BY id DESC", (st.session_state.user_id,))
            for t in cursor.fetchall():
                with st.expander(f"📦 {t['product_name']} ({t['created_at'].strftime('%d/%m')})"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown("#### 🤖 AI Raporu")
                        st.markdown(f"<div class='report-card'>{t['ai_analysis']}</div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown("#### 🚢 Teklifler")
                        cursor.execute("SELECT o.*, u.username FROM offers o JOIN users u ON o.firm_id = u.id WHERE o.request_id = %s", (t['id'],))
                        for o in cursor.fetchall():
                            st.markdown(f"<div class='offer-box'><b>{o['username']}: {o['offer_amount']}$</b><br>{o['delivery_days']} Gün", unsafe_allow_html=True)
                            if st.button("Teklifi Sil", key=f"del_{o['id']}"):
                                teklif_sil(o['id'])
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
            conn.close()
    with tab_n:
        with st.form("new_req", clear_on_submit=True):
            nu = st.text_input("Ürün")
            ntip = st.selectbox("Yükleme", ["Parsiyel (LCL)", "Tam Konteyner (FCL)", "Hava", "Kurye"])
            nf, na, nk = st.columns(3)
            fv, av, kv = nf.number_input("Fiyat ($)"), na.number_input("Adet", step=1), nk.number_input("KG")
            if st.form_submit_button("Analiz Et ve İlana Çık"):
                res = requests.post("http://localhost:8000/hesapla", json={"isim": f"{nu} ({ntip})", "fiyat": fv, "adet": av, "agirlik": kv})
                if res.status_code == 200:
                    talebi_kaydet(st.session_state.user_id, nu, fv, av, kv, res.json()["analiz"], ntip)
                    st.success("Talebiniz yayında!")

# --- 3. DURUM: FİRMA PANELİ (FİLTRELİ) ---
else:
    st.header(f"🚛 {st.session_state.user_type.replace('_', ' ').upper()} PANELİ")
    f_tab1, f_tab2 = st.tabs(["🔔 Yeni Talepler", "✅ Teklif Verdiklerim"])
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        # Firma ID'sine göre teklif verdiklerini ve vermediklerini ayır
        if f_tab1: # YENİ TALEPLER (Teklif verilmemiş olanlar)
            cursor.execute("""
                SELECT r.*, u.username FROM requests r 
                JOIN users u ON r.user_id = u.id 
                WHERE r.id NOT IN (SELECT request_id FROM offers WHERE firm_id = %s)
                ORDER BY r.id DESC""", (st.session_state.user_id,))
            for i in cursor.fetchall():
                with st.expander(f"📦 {i['product_name']} | Müşteri: {i['username']}"):
                    c_data, c_form = st.columns([1, 1])
                    with c_data:
                        st.info(f"**Ürün:** {i['product_name']}\n\n**Miktar:** {i['quantity']} Adet\n\n**Birim Fiyat:** {i['price']}$\n\n**Ağırlık:** {i['weight']} KG\n\n**Yükleme:** {i['extra_info']}")
                    with c_form:
                        with st.form(key=f"f_{i['id']}", clear_on_submit=True):
                            amt = st.number_input("Teklif Tutarı ($)")
                            day = st.number_input("Süre (Gün)", step=1)
                            note = st.text_area("Not")
                            if st.form_submit_button("Teklifi İlet"):
                                cursor.execute("INSERT INTO offers (request_id, firm_id, offer_amount, delivery_days, firm_note) VALUES (%s,%s,%s,%s,%s)", (i['id'], st.session_state.user_id, amt, day, note))
                                conn.commit()
                                st.rerun()
        
        if f_tab2: # TEKLİF VERDİKLERİM
            cursor.execute("""
                SELECT r.product_name, o.* FROM offers o 
                JOIN requests r ON o.request_id = r.id 
                WHERE o.firm_id = %s ORDER BY o.id DESC""", (st.session_state.user_id,))
            for o in cursor.fetchall():
                st.markdown(f"""<div class='offer-box'><b>Ürün: {o['product_name']}</b><br>Sizin Teklifiniz: {o['offer_amount']}$ | Süre: {o['delivery_days']} Gün<br>Not: {o['firm_note']}</div>""", unsafe_allow_html=True)
        conn.close()
