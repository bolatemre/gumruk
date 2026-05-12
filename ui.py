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
    .report-card { background: white; padding: 25px; border-radius: 15px; border-left: 8px solid #1e3a8a; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .blur-text { filter: blur(5px); opacity: 0.4; user-select: none; }
    .offer-box { background: #e0f2fe; padding: 15px; border-radius: 10px; border: 1px solid #0ea5e9; margin-bottom: 10px; }
    .stButton>button { border-radius: 10px; font-weight: bold; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- FONKSİYONLAR ---
def talebi_kaydet(uid, isim, fiyat, adet, agirlik, analiz):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "INSERT INTO requests (user_id, product_name, price, quantity, weight, ai_analysis) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (uid, isim, fiyat, adet, agirlik, analiz))
        conn.commit()
        conn.close()

# --- SIDEBAR & ÇIKIŞ ---
if st.session_state.user_id:
    with st.sidebar:
        st.success(f"Giriş Yapıldı: {st.session_state.user_name}")
        if st.button("Güvenli Çıkış"):
            st.session_state.user_id = None
            st.rerun()

# --- 1. DURUM: ZİYARETÇİ (GİRİŞSİZ) ---
if not st.session_state.user_id:
    t1, t2 = st.tabs(["🔍 Ücretsiz Maliyet Analizi", "🔑 Giriş / Kayıt"])
    
    with t1:
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.subheader("İthalat Bilgilerini Girin")
            with st.form("vitrin_form"):
                u = st.text_input("Ürün Adı", placeholder="Örn: CNC Yedek Parça")
                c1, c2 = st.columns(2)
                f = c1.number_input("Birim Fiyat ($)", min_value=0.0)
                a = c2.number_input("Adet", min_value=1, step=1)
                kg = st.number_input("Toplam Ağırlık (KG)")
                submit = st.form_submit_button("Analizi Gör ve Teklif Al 🚀")
                
                if submit:
                    if u and f > 0:
                        with st.spinner("Yapay Zeka 2026 Mevzuatını Tarıyor..."):
                            res = requests.post("http://localhost:8000/hesapla", json={"isim": u, "fiyat": f, "adet": a, "agirlik": kg})
                            if res.status_code == 200:
                                st.session_state.temp_res = res.json()["analiz"]
                                st.session_state.last_calc = {"isim": u, "fiyat": f, "adet": a, "agirlik": kg}
                    else:
                        st.error("Lütfen tüm alanları doldurun.")
        
        with col2:
            st.subheader("📊 Ön Analiz Raporu")
            if st.session_state.temp_res:
                st.success("Analiz Hazır! Özet aşağıdadır.")
                st.markdown(f"**Ürün:** {st.session_state.last_calc['isim']}")
                st.markdown(f"<div>{st.session_state.temp_res[:150]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='blur-text'>{st.session_state.temp_res[150:500]}</div>", unsafe_allow_html=True)
                st.info("🔒 Detaylı vergi dökümü ve nakliye teklifleri için lütfen giriş yapın.")
            else:
                st.info("Formu doldurduğunuzda AI raporu burada görünecek.")

    with t2:
        l_col, r_col = st.columns(2)
        with l_col:
            st.subheader("Giriş Yap")
            le = st.text_input("Email", key="l_e")
            lp = st.text_input("Şifre", type="password", key="l_p")
            if st.button("Giriş Yap"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (le, lp))
                    user = cursor.fetchone()
                    if user:
                        st.session_state.user_id = user['id']
                        st.session_state.user_type = user['user_type']
                        st.session_state.user_name = user['username']
                        if st.session_state.last_calc and st.session_state.temp_res:
                            talebi_kaydet(user['id'], **st.session_state.last_calc, analiz=st.session_state.temp_res)
                        st.rerun()
                    else: st.error("Email veya şifre hatalı.")
        with r_col:
            st.subheader("Üye Ol")
            ri = st.text_input("Ad Soyad / Firma")
            re = st.text_input("Email")
            rp = st.text_input("Şifre", type="password")
            rt = st.selectbox("Rol", ["musteri", "lojistik_firmasi", "gumruk_musaviri"])
            if st.button("Kayıt Ol"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, email, password, user_type) VALUES (%s,%s,%s,%s)", (ri, re, rp, rt))
                    conn.commit()
                    st.success("Kayıt başarılı! Giriş yapabilirsiniz.")

# --- 2. DURUM: MÜŞTERİ PANELİ ---
elif st.session_state.user_type == 'musteri':
    st.header("🏢 İthalatçı Kontrol Paneli")
    tab_list, tab_new = st.tabs(["📋 Taleplerim & AI Analizleri", "➕ Yeni Teklif Al ve Analiz Et"])
    
    with tab_list:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM requests WHERE user_id = %s ORDER BY id DESC", (st.session_state.user_id,))
            talepler = cursor.fetchall()
            if not talepler: st.info("Henüz bir talebiniz yok.")
            for t in talepler:
                with st.expander(f"📦 {t['product_name']} - {t['created_at'].strftime('%d/%m/%Y')}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown("#### 🤖 AI Gümrük & Maliyet Analizi")
                        st.markdown(f"<div class='report-card'>{t['ai_analysis']}</div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown("#### 🚢 Firma Teklifleri")
                        cursor.execute("SELECT * FROM offers WHERE request_id = %s", (t['id'],))
                        offers = cursor.fetchall()
                        if not offers: st.warning("Teklif bekleniyor...")
                        for o in offers:
                            st.markdown(f"<div class='offer-box'><b>Fiyat: {o['offer_amount']}$</b><br>Süre: {o['delivery_days']} Gün<br><i>{o['firm_note']}</i></div>", unsafe_allow_html=True)
            conn.close()

    with tab_new:
        st.subheader("Yeni Bir Ürün İçin Maliyet Çıkar")
        with st.form("new_request_form", clear_on_submit=True):
            nu = st.text_input("Ürün Adı")
            nc1, nc2 = st.columns(2)
            nf = nc1.number_input("Birim Fiyat ($)")
            na = nc2.number_input("Adet", step=1)
            nk = st.number_input("Ağırlık (KG)")
            if st.form_submit_button("Analiz Et ve Teklif Al 🚀"):
                with st.spinner("AI Raporu Hazırlanıyor..."):
                    res = requests.post("http://localhost:8000/hesapla", json={"isim": nu, "fiyat": nf, "adet": na, "agirlik": nk})
                    if res.status_code == 200:
                        talebi_kaydet(st.session_state.user_id, nu, nf, na, nk, res.json()["analiz"])
                        st.balloons()
                        st.success("✅ Teklif Talebiniz Başarıyla Alındı! 'Taleplerim' sekmesinden analizi görebilirsiniz.")

# --- 3. DURUM: FİRMA PANELİ ---
else:
    st.header("🚛 Lojistik & Gümrük Borsası")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id ORDER BY r.id DESC")
        ilanlar = cursor.fetchall()
        for i in ilanlar:
            with st.expander(f"📦 {i['product_name']} | Müşteri: {i['username']}"):
                col_i, col_f = st.columns([2, 1])
                with col_i:
                    st.write(f"**Talep:** {i['quantity']} Adet | {i['price']}$ Fiyat | {i['weight']} KG")
                    st.markdown("**AI Analizi:**")
                    st.write(i['ai_analysis'][:300] + "...")
                with col_f:
                    with st.form(key=f"bid_{i['id']}", clear_on_submit=True):
                        price = st.number_input("Teklifiniz ($)")
                        days = st.number_input("Süre (Gün)", step=1)
                        note = st.text_area("Not")
                        if st.form_submit_button("Teklifi Gönder"):
                            cursor.execute("INSERT INTO offers (request_id, firm_id, offer_amount, delivery_days, firm_note) VALUES (%s,%s,%s,%s,%s)", (i['id'], st.session_state.user_id, price, days, note))
                            conn.commit()
                            st.success("Teklifiniz iletildi!")
        conn.close()
