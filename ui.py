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

# --- GELİŞMİŞ KURUMSAL CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .premium-card { background: white; padding: 20px; border-radius: 12px; border-left: 8px solid #1e3a8a; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .blur-text { filter: blur(5px); opacity: 0.4; pointer-events: none; }
    .status-accepted { background: #dcfce7; border: 1px solid #22c55e; padding: 15px; border-radius: 10px; color: #166534; font-weight: bold; margin-bottom:10px; }
    .offer-item { background: #ffffff; border: 1px solid #e2e8f0; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .price-text { font-size: 22px; color: #1e3a8a; font-weight: 900; }
    .info-label { color: #64748b; font-size: 11px; font-weight: 700; text-transform: uppercase; }
    .info-value { color: #1e293b; font-size: 15px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- ANA DÖNGÜ ---
if not st.session_state.user_id:
    # --- GİRİŞ ÖNCESİ (VİTRİN VE LOGIN) ---
    st.title("🚢 Lojistik & Gümrük Borsası")
    # (Bu kısım sende çalışıyor, o yüzden sade geçiyorum ama ana dosyada tam olmalı)
    st.info("Lütfen Giriş Yap sekmesinden sisteme girin.")
    
    # Giriş/Kayıt kodların burada durmalı...
    # (Daha önceki mesajdaki t_calc, t_login, t_reg sekmelerini buraya yapıştırabilirsin)

else:
    # --- GİRİŞ SONRASI: PANELLER ---
    st.sidebar.success(f"Giriş: {st.session_state.user_name}")
    if st.sidebar.button("🚪 Güvenli Çıkış"):
        st.session_state.clear()
        st.rerun()

    conn = get_db_connection()
    if not conn:
        st.error("Veritabanı bağlantısı kurulamadı!")
        st.stop()
    cursor = conn.cursor(dictionary=True)

    if st.session_state.user_type == 'musteri':
        st.header("🏢 İthalatçı Kontrol Merkezi")
        m_tab1, m_tab2, m_tab3 = st.tabs(["📋 Aktif Taleplerim", "✅ Kabul Edilen Teklifler", "➕ Yeni Talep"])
        
        with m_tab1:
            cursor.execute("SELECT * FROM requests WHERE user_id=%s AND status='aktif' ORDER BY id DESC", (st.session_state.user_id,))
            talepler = cursor.fetchall()
            if not talepler: st.info("Şu an aktif bir talebiniz yok.")
            for t in talepler:
                with st.expander(f"📦 {t['product_name']} - Detaylar ve Teklifler"):
                    st.markdown(f"<div class='premium-card'><b>🤖 Yapay Zeka Analizi:</b><br>{t['ai_analysis']}</div>", unsafe_allow_html=True)
                    col_g, col_l = st.columns(2)
                    
                    with col_g:
                        st.markdown("### 📜 Gümrükçü Teklifleri")
                        cursor.execute("SELECT o.*, u.username, u.phone, u.email FROM offers o JOIN users u ON o.firm_id = u.id WHERE o.request_id=%s AND u.user_type='gumruk_musaviri'", (t['id'],))
                        for o in cursor.fetchall():
                            st.markdown(f"<div class='offer-item'><b>{o['username']}</b><br><span class='price-text'>{o['offer_amount']}$</span><br>⏱ {o['delivery_days']} Gün<br>📞 {o['phone']}</div>", unsafe_allow_html=True)
                            if st.button("Kabul Et", key=f"acc_g_{o['id']}"):
                                cursor.execute("UPDATE requests SET status='tamamlandi' WHERE id=%s", (t['id'],))
                                cursor.execute("UPDATE offers SET status='kabul_edildi' WHERE id=%s", (o['id'],))
                                conn.commit()
                                st.success("Teklif kabul edildi!")
                                time.sleep(1)
                                st.rerun()

                    with col_l:
                        st.markdown("### 🚚 Lojistikçi Teklifleri")
                        cursor.execute("SELECT o.*, u.username, u.phone, u.email FROM offers o JOIN users u ON o.firm_id = u.id WHERE o.request_id=%s AND u.user_type='lojistik_firmasi'", (t['id'],))
                        for o in cursor.fetchall():
                            st.markdown(f"<div class='offer-item'><b>{o['username']}</b><br><span class='price-text'>{o['offer_amount']}$</span><br>⏱ {o['delivery_days']} Gün<br>📞 {o['phone']}</div>", unsafe_allow_html=True)
                            if st.button("Kabul Et", key=f"acc_l_{o['id']}"):
                                cursor.execute("UPDATE requests SET status='tamamlandi' WHERE id=%s", (t['id'],))
                                cursor.execute("UPDATE offers SET status='kabul_edildi' WHERE id=%s", (o['id'],))
                                conn.commit()
                                st.success("Teklif kabul edildi!")
                                time.sleep(1)
                                st.rerun()

        with m_tab2:
            cursor.execute("""SELECT r.product_name, o.*, u.username as firma, u.phone, u.email 
                           FROM offers o JOIN requests r ON o.request_id = r.id 
                           JOIN users u ON o.firm_id = u.id 
                           WHERE r.user_id=%s AND o.status='kabul_edildi'""", (st.session_state.user_id,))
            kabuller = cursor.fetchall()
            for k in kabuller:
                st.markdown(f"<div class='status-accepted'>✅ {k['product_name']} işi için {k['firma']} ile anlaşıldı.<br>📞 {k['phone']} | 📧 {k['email']}</div>", unsafe_allow_html=True)

        with m_tab3:
            with st.form("new_req_form", clear_on_submit=True):
                st.subheader("Yeni Bir İthalat Maliyeti Hesapla & Yayınla")
                un = st.text_input("Ürün İsmi")
                yn = st.selectbox("Yükleme", ["Parsiyel", "Konteyner", "Hava"])
                c1, c2, c3 = st.columns(3)
                fn = c1.number_input("Birim $")
                an = c2.number_input("Adet", step=1)
                kn = c3.number_input("Toplam KG")
                if st.form_submit_button("Analizi Başlat ve İlana Çık 🚀"):
                    res = requests.post("http://localhost:8000/hesapla", json={"isim": f"{un} ({yn})", "fiyat": fn, "adet": an, "agirlik": kn})
                    if res.status_code == 200:
                        cursor.execute("INSERT INTO requests (user_id, product_name, price, quantity, weight, ai_analysis, extra_info, status) VALUES (%s,%s,%s,%s,%s,%s,%s,'aktif')", 
                                     (st.session_state.user_id, un, fn, an, kn, res.json()["analiz"], yn))
                        conn.commit()
                        st.balloons()
                        st.success("Talebiniz yayına alındı!")

    else:
        # --- FİRMA PANELİ (LOJİSTİK & GÜMRÜK) ---
        st.header(f"🏢 {st.session_state.user_type.upper()} Paneli")
        f_tab1, f_tab2, f_tab3 = st.tabs(["🔔 Yeni Talepler", "✅ Verdiklerim", "🤝 Kabul Edilenler"])
        
        with f_tab1:
            cursor.execute("""SELECT r.*, u.username as musterı FROM requests r JOIN users u ON r.user_id = u.id 
                           WHERE r.status='aktif' AND r.id NOT IN (SELECT request_id FROM offers WHERE firm_id = %s)""", (st.session_state.user_id,))
            ilanlar = cursor.fetchall()
            for i in ilanlar:
                with st.expander(f"📦 {i['product_name']} | Müşteri: {i['musterı']}"):
                    st.markdown(f"**Miktar:** {i['quantity']} Adet | **Ağırlık:** {i['weight']} KG | **Yükleme:** {i['extra_info']}")
                    with st.form(key=f"bid_form_{i['id']}"):
                        price = st.number_input("Teklif Tutarınız ($)")
                        days = st.number_input("Süre (Gün)", step=1)
                        note = st.text_area("Notunuz")
                        if st.form_submit_button("Teklifi Gönder"):
                            cursor.execute("INSERT INTO offers (request_id, firm_id, offer_amount, delivery_days, firm_note, status) VALUES (%s,%s,%s,%s,%s,'beklemede')", 
                                         (i['id'], st.session_state.user_id, price, days, note))
                            conn.commit()
                            st.success("Teklif iletildi!")
                            time.sleep(1)
                            st.rerun()

        with f_tab2:
            cursor.execute("""SELECT r.product_name, o.* FROM offers o JOIN requests r ON o.request_id = r.id 
                           WHERE o.firm_id=%s AND o.status='beklemede'""", (st.session_state.user_id,))
            for v in cursor.fetchall():
                with st.container(border=True):
                    st.write(f"**Ürün:** {v['product_name']} | **Teklifiniz:** {v['offer_amount']}$ | **Süre:** {v['delivery_days']} Gün")
                    if st.button("Düzenle", key=f"edit_v_{v['id']}"):
                        st.info("Düzenleme modu yakında aktif.")

        with f_tab3:
            cursor.execute("""SELECT r.product_name, o.*, u.username as musterı, u.phone, u.email 
                           FROM offers o JOIN requests r ON o.request_id = r.id 
                           JOIN users u ON r.user_id = u.id 
                           WHERE o.firm_id=%s AND o.status='kabul_edildi'""", (st.session_state.user_id,))
            kabuller = cursor.fetchall()
            for k in kabuller:
                st.markdown(f"<div class='status-accepted'>🤝 {k['product_name']} işi kabul edildi.<br>Müşteri: {k['musterı']} | 📞 {k['phone']}</div>", unsafe_allow_html=True)
    
    conn.close()
