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
st.set_page_config(page_title="Lojistik & Gümrük Borsası", page_icon="🚢", layout="wide")

# --- SESSION STATE ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_type = None
    st.session_state.user_name = None
    st.session_state.temp_res = None
    st.session_state.last_calc = None

# --- GELİŞMİŞ CSS TASARIM ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    /* Teklif Kartları */
    .premium-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #1e3a8a;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .offer-item {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        transition: 0.3s;
    }
    .offer-item:hover { border-color: #3b82f6; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .price-tag { font-size: 24px; color: #1e3a8a; font-weight: 800; }
    .contact-box { background: #f1f5f9; padding: 10px; border-radius: 8px; font-size: 14px; margin-top: 10px; border: 1px dashed #cbd5e1; }
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-log { background: #dcfce7; color: #166534; }
    .badge-gum { background: #fef9c3; color: #854d0e; }
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
        finally: conn.close()

# --- 1. DURUM: ZİYARETÇİ ---
if not st.session_state.user_id:
    tab_a, tab_b = st.tabs(["🔍 Analiz ve Teklif", "🔑 Giriş / Kayıt"])
    with tab_a:
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.subheader("Ürün Detayları")
            with st.form("vitrin_form"):
                u = st.text_input("Ürün İsmi")
                yuk = st.selectbox("Yükleme", ["Parsiyel", "Konteyner", "Hava", "Kurye"])
                f, a, kg = st.columns(3)
                fv = f.number_input("Birim $")
                av = a.number_input("Adet", step=1)
                kv = kg.number_input("Toplam KG")
                if st.form_submit_button("Analiz Et ve Teklif İste 🚀"):
                    res = requests.post("http://localhost:8000/hesapla", json={"isim": f"{u} ({yuk})", "fiyat": fv, "adet": av, "agirlik": kv})
                    if res.status_code == 200:
                        st.session_state.temp_res = res.json()["analiz"]
                        st.session_state.last_calc = {"isim": u, "fiyat": fv, "adet": av, "agirlik": kv, "yukleme_tipi": yuk}
        with col2:
            if st.session_state.temp_res:
                st.success("Analiz Hazır!")
                st.markdown(f"<div class='blur-text'>{st.session_state.temp_res[:300]}</div>", unsafe_allow_html=True)
                st.info("🔒 Teklifleri ve raporun tamamını görmek için Giriş Yapın.")
    
    with tab_b:
        l, r = st.columns(2)
        with l:
            st.subheader("Giriş")
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
            st.subheader("Kayıt")
            ri, re, rp = st.text_input("İlgili Kişi / Firma"), st.text_input("Email", key="re"), st.text_input("Şifre", type="password", key="rp")
            rtel = st.text_input("Telefon Numarası", placeholder="05xx xxx xx xx")
            rt = st.selectbox("Üyelik Tipi", ["musteri", "lojistik_firmasi", "gumruk_musaviri"])
            if st.button("Kayıt Ol"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, email, password, user_type, phone) VALUES (%s,%s,%s,%s,%s)", (ri, re, rp, rt, rtel))
                    conn.commit()
                    st.success("Kayıt Başarılı!")

# --- 2. DURUM: MÜŞTERİ PANELİ ---
elif st.session_state.user_type == 'musteri':
    st.header("📋 Taleplerim ve Gelen Teklifler")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM requests WHERE user_id = %s ORDER BY id DESC", (st.session_state.user_id,))
        for t in cursor.fetchall():
            with st.expander(f"📦 {t['product_name']} - {t['created_at'].strftime('%d/%m/%Y')}"):
                c1, c2 = st.columns([1.5, 1])
                with c1:
                    st.markdown(f"<div class='premium-card'><b>AI ANALİZİ:</b><br>{t['ai_analysis']}</div>", unsafe_allow_html=True)
                with c2:
                    st.markdown("### 📥 Gelen Teklifler")
                    cursor.execute("SELECT o.*, u.username, u.email, u.phone, u.user_type FROM offers o JOIN users u ON o.firm_id = u.id WHERE o.request_id = %s", (t['id'],))
                    for o in cursor.fetchall():
                        badge = "🚚 Lojistik" if o['user_type'] == 'lojistik_firmasi' else "📜 Gümrük"
                        st.markdown(f"""
                        <div class='offer-item'>
                            <span class='badge {"badge-log" if o['user_type'] == "lojistik_firmasi" else "badge-gum"}'>{badge}</span>
                            <div class='price-tag'>{o['offer_amount']}$</div>
                            <b>{o['username']}</b><br>
                            ⏱ Teslim: {o['delivery_days']} Gün<br>
                            📝 Not: {o['firm_note']}
                            <div class='contact-box'>
                                📞 {o['phone']} | ✉️ {o['email']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Teklifi Sil", key=f"del_{o['id']}"):
                            cursor.execute("DELETE FROM offers WHERE id=%s", (o['id'],))
                            conn.commit()
                            st.rerun()
        conn.close()
    if st.button("➕ Yeni Teklif Talebi Oluştur"):
        st.session_state.user_id = st.session_state.user_id # Refresh logic

# --- 3. DURUM: FİRMA PANELİ ---
else:
    st.header(f"🏢 {st.session_state.user_type.upper()} PANELİ")
    t1, t2 = st.tabs(["🔔 Yeni İşler", "✅ Verdiklerim"])
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        with t1:
            # Teklif verilmemiş talepler
            cursor.execute("""SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id 
                           WHERE r.id NOT IN (SELECT request_id FROM offers WHERE firm_id = %s) ORDER BY id DESC""", (st.session_state.user_id,))
            for i in cursor.fetchall():
                with st.expander(f"📦 {i['product_name']} | {i['username']}"):
                    st.info(f"Fiyat: {i['price']}$ | Adet: {i['quantity']} | KG: {i['weight']} | Tip: {i['extra_info']}")
                    with st.form(key=f"frm_{i['id']}"):
                        if st.session_state.user_type == 'lojistik_firmasi':
                            st.markdown("### Lojistik Teklif Formu")
                            navlun = st.number_input("Navlun Bedeli ($)")
                            sure = st.number_input("Varış Süresi (Gün)", step=1)
                            note = st.text_area("İç nakliye, sigorta vb. detaylar")
                            total = navlun # Basitleştirme
                        else:
                            st.markdown("### Gümrük Teklif Formu")
                            servis = st.number_input("Müşavirlik Bedeli ($)")
                            sure = st.number_input("İşlem Süresi (Gün)", step=1)
                            note = st.text_area("GTİP Tahmini, Ardiye Notu vb.")
                            total = servis
                        
                        if st.form_submit_button("Teklifi Müşteriye İlet"):
                            cursor.execute("INSERT INTO offers (request_id, firm_id, offer_amount, delivery_days, firm_note) VALUES (%s,%s,%s,%s,%s)", (i['id'], st.session_state.user_id, total, sure, note))
                            conn.commit()
                            st.rerun()

        with t2:
            # Teklif verilmiş talepler (SABİT)
            cursor.execute("""SELECT r.product_name, o.*, u.username as musterı_adı FROM offers o 
                           JOIN requests r ON o.request_id = r.id 
                           JOIN users u ON r.user_id = u.id
                           WHERE o.firm_id = %s""", (st.session_state.user_id,))
            for v in cursor.fetchall():
                st.markdown(f"""
                <div class='offer-item'>
                    <b>Ürün:</b> {v['product_name']} | 👤 <b>Müşteri:</b> {v['musterı_adı']}<br>
                    <div class='price-tag'>Teklifiniz: {v['offer_amount']}$</div>
                    ⏱ Süre: {v['delivery_days']} Gün | 📝 Not: {v['firm_note']}
                </div>
                """, unsafe_allow_html=True)
        conn.close()

# SIDEBAR ÇIKIŞ
if st.session_state.user_id:
    st.sidebar.button("Çıkış Yap", on_click=lambda: st.session_state.clear())
