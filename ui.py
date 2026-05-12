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

# --- GELİŞMİŞ KURUMSAL CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .premium-card { background: white; padding: 20px; border-radius: 12px; border-left: 8px solid #1e3a8a; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .blur-text { filter: blur(5px); opacity: 0.4; pointer-events: none; }
    .offer-box { background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 15px; margin-bottom: 10px; }
    .status-accepted { background: #dcfce7; border: 1px solid #22c55e; padding: 10px; border-radius: 8px; color: #166534; font-weight: bold; }
    .data-label { color: #64748b; font-size: 11px; font-weight: 700; text-transform: uppercase; }
    .data-value { color: #1e293b; font-size: 15px; font-weight: 700; }
    .stButton>button { border-radius: 8px; font-weight: bold; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- ANA DÖNGÜ ---
if not st.session_state.user_id:
    # --- 1. ZİYARETÇİ / GİRİŞ / KAYIT ---
    st.title("🚢 Lojistik & Gümrük Borsası")
    t_calc, t_login, t_reg = st.tabs(["📊 Hızlı Analiz", "🔑 Giriş Yap", "📝 Üye Ol"])
    
    with t_calc:
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.subheader("Ürün Bilgilerini Girin")
            with st.container(border=True):
                u = st.text_input("Ürün İsmi", placeholder="Örn: Akıllı Saat")
                yuk = st.selectbox("Yükleme", ["Parsiyel", "Konteyner", "Hava", "Kurye"])
                c1, c2, c3 = st.columns(3)
                fv = c1.number_input("Birim $")
                av = c2.number_input("Adet", step=1)
                kv = c3.number_input("Toplam KG")
                if st.button("Maliyeti Analiz Et 🚀"):
                    res = requests.post("http://localhost:8000/hesapla", json={"isim": f"{u} ({yuk})", "fiyat": fv, "adet": av, "agirlik": kv})
                    if res.status_code == 200:
                        st.session_state.temp_res = res.json()["analiz"]
                        st.session_state.last_calc = {"isim": u, "fiyat": fv, "adet": av, "agirlik": kv, "yukleme_tipi": yuk}
                        st.rerun()
        with col2:
            st.subheader("📊 Analiz Ön İzleme")
            if st.session_state.temp_res:
                st.success("✅ Tahmini Rapor Hazır!")
                st.markdown(f"<div>{st.session_state.temp_res[:150]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='blur-text'>{st.session_state.temp_res[150:600]}</div>", unsafe_allow_html=True)
                st.info("🔒 Tam rapor için giriş yapın.")
            else: st.info("Verileri girdiğinizde rapor burada belirecek.")

    with t_login:
        st.subheader("Hoş Geldiniz")
        le, lp = st.text_input("E-posta"), st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap"):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (le, lp))
                user = cursor.fetchone()
                if user:
                    st.session_state.user_id, st.session_state.user_type, st.session_state.user_name = user['id'], user['user_type'], user['username']
                    st.rerun()
                else: st.error("Hatalı giriş.")
                conn.close()

    with t_reg:
        st.subheader("Borsaya Katılın")
        r_type = st.radio("Üyelik Tipiniz", ["musteri", "lojistik_firmasi", "gumruk_musaviri"], horizontal=True)
        r_name = st.text_input("İlgili Kişi" if r_type == 'musteri' else "Firma Adı")
        r_mail = st.text_input("E-posta Adresi")
        r_tel = st.text_input("Telefon Numarası")
        r_pass = st.text_input("Şifre Belirleyin", type="password")
        if st.button("Kaydı Tamamla"):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, email, password, user_type, phone) VALUES (%s,%s,%s,%s,%s)", (r_name, r_mail, r_pass, r_type, r_tel))
                conn.commit()
                st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
                conn.close()

else:
    # --- 2. GİRİŞ YAPILMIŞ PANELLER ---
    st.sidebar.success(f"Giriş: {st.session_state.user_name}")
    if st.sidebar.button("🚪 Güvenli Çıkış"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.user_type == 'musteri':
        # --- MÜŞTERİ PANELİ ---
        st.header("🏢 İthalatçı Kontrol Merkezi")
        m_tab1, m_tab2, m_tab3 = st.tabs(["📋 Aktif Taleplerim", "✅ Kabul Edilen Teklifler", "➕ Yeni Talep"])
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        with m_tab1:
            cursor.execute("SELECT * FROM requests WHERE user_id=%s AND status='aktif' ORDER BY id DESC", (st.session_state.user_id,))
            for t in cursor.fetchall():
                with st.expander(f"📦 {t['product_name']} - Teklifleri Gör"):
                    st.markdown(f"<div class='premium-card'><b>🤖 Yapay Zeka Analizi:</b><br>{t['ai_analysis']}</div>", unsafe_allow_html=True)
                    
                    col_g, col_l = st.columns(2)
                    # Gümrük Teklifleri
                    with col_g:
                        st.markdown("### 📜 Gümrükçü Teklifleri")
                        cursor.execute("SELECT o.*, u.username, u.phone, u.email FROM offers o JOIN users u ON o.firm_id = u.id WHERE o.request_id=%s AND u.user_type='gumruk_musaviri'", (t['id'],))
                        for o in cursor.fetchall():
                            with st.container(border=True):
                                st.write(f"**{o['username']}** | 📞 {o['phone']}")
                                st.write(f"**Fiyat:** {o['offer_amount']}$ | **Süre:** {o['delivery_days']} Gün")
                                if st.button("Teklifi Kabul Et", key=f"acc_{o['id']}"):
                                    cursor.execute("UPDATE requests SET status='tamamlandi' WHERE id=%s", (t['id'],))
                                    cursor.execute("UPDATE offers SET status='kabul_edildi' WHERE id=%s", (o['id'],))
                                    conn.commit()
                                    st.rerun()
                    # Lojistik Teklifleri
                    with col_l:
                        st.markdown("### 🚚 Lojistikçi Teklifleri")
                        cursor.execute("SELECT o.*, u.username, u.phone, u.email FROM offers o JOIN users u ON o.firm_id = u.id WHERE o.request_id=%s AND u.user_type='lojistik_firmasi'", (t['id'],))
                        for o in cursor.fetchall():
                            with st.container(border=True):
                                st.write(f"**{o['username']}** | 📞 {o['phone']}")
                                st.write(f"**Fiyat:** {o['offer_amount']}$ | **Süre:** {o['delivery_days']} Gün")
                                if st.button("Teklifi Kabul Et", key=f"accl_{o['id']}"):
                                    cursor.execute("UPDATE requests SET status='tamamlandi' WHERE id=%s", (t['id'],))
                                    cursor.execute("UPDATE offers SET status='kabul_edildi' WHERE id=%s", (o['id'],))
                                    conn.commit()
                                    st.rerun()

        with m_tab2:
            st.subheader("Eşleşen Firmalar ve Detaylar")
            cursor.execute("""SELECT r.product_name, o.*, u.username as firma_adi, u.phone, u.email 
                           FROM offers o JOIN requests r ON o.request_id = r.id 
                           JOIN users u ON o.firm_id = u.id 
                           WHERE r.user_id=%s AND o.status='kabul_edildi'""", (st.session_state.user_id,))
            for k in cursor.fetchall():
                st.markdown(f"<div class='status-accepted'>✅ {k['product_name']} için {k['firma_adi']} ile anlaştınız.<br>İletişim: {k['phone']} | {k['email']}</div>", unsafe_allow_html=True)

        with m_tab3:
            # Yeni Talep Formu (Analiz + Kayıt)
            with st.form("new_req"):
                u_n = st.text_input("Ürün")
                y_n = st.selectbox("Yükleme", ["Parsiyel", "Konteyner", "Hava"])
                f_n = st.number_input("Birim $")
                a_n = st.number_input("Adet")
                k_n = st.number_input("KG")
                if st.form_submit_button("Analiz Et ve Yayınla"):
                    res = requests.post("http://localhost:8000/hesapla", json={"isim": u_n, "fiyat": f_n, "adet": a_n, "agirlik": k_n})
                    if res.status_code == 200:
                        cursor.execute("INSERT INTO requests (user_id, product_name, price, quantity, weight, ai_analysis, extra_info) VALUES (%s,%s,%s,%s,%s,%s,%s)", 
                                     (st.session_state.user_id, u_n, f_n, a_n, k_n, res.json()["analiz"], y_n))
                        conn.commit()
                        st.success("Talebiniz başarıyla yayınlandı!")

    else:
        # --- FİRMA PANELİ (LOJİSTİK & GÜMRÜK) ---
        st.header(f"🏢 {st.session_state.user_type.upper()} Paneli")
        f_tab1, f_tab2, f_tab3 = st.tabs(["🔔 Yeni Talepler", "✅ Teklif Verdiklerim", "🤝 Kabul Edilenler"])
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        with f_tab1:
            cursor.execute("""SELECT r.*, u.username as musterı FROM requests r JOIN users u ON r.user_id = u.id 
                           WHERE r.status='aktif' AND r.id NOT IN (SELECT request_id FROM offers WHERE firm_id = %s)""", (st.session_state.user_id,))
            for i in cursor.fetchall():
                with st.expander(f"📦 {i['product_name']} | Müşteri: {i['musterı']}"):
                    st.write(f"Adet: {i['quantity']} | KG: {i['weight']} | Yükleme: {i['extra_info']}")
                    with st.form(key=f"bid_{i['id']}"):
                        st.write("Teklif Formunuz")
                        p_in = st.number_input("Teklif Tutarı ($)")
                        d_in = st.number_input("Süre (Gün)")
                        n_in = st.text_area("Müşteriye Not")
                        if st.form_submit_button("Teklifi İlet"):
                            cursor.execute("INSERT INTO offers (request_id, firm_id, offer_amount, delivery_days, firm_note) VALUES (%s,%s,%s,%s,%s)", (i['id'], st.session_state.user_id, p_in, d_in, n_in))
                            conn.commit()
                            st.rerun()

        with f_tab2:
            cursor.execute("""SELECT r.product_name, o.* FROM offers o JOIN requests r ON o.request_id = r.id 
                           WHERE o.firm_id=%s AND o.status='beklemede'""", (st.session_state.user_id,))
            for v in cursor.fetchall():
                with st.container(border=True):
                    st.write(f"**Ürün:** {v['product_name']} | **Teklifiniz:** {v['offer_amount']}$")
                    if st.button("Düzenle", key=f"edit_{v['id']}"):
                        st.info("Düzenleme formu açılıyor...") # Geliştirilebilir

        with f_tab3:
            cursor.execute("""SELECT r.product_name, o.*, u.username as musterı, u.phone, u.email 
                           FROM offers o JOIN requests r ON o.request_id = r.id 
                           JOIN users u ON r.user_id = u.id 
                           WHERE o.firm_id=%s AND o.status='kabul_edildi'""", (st.session_state.user_id,))
            for k in cursor.fetchall():
                st.markdown(f"<div class='status-accepted'>🤝 {k['product_name']} işi kabul edildi.<br>Müşteri: {k['musterı']} | 📞 {k['phone']}</div>", unsafe_allow_html=True)
        
        conn.close()
