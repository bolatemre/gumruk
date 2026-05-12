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
st.set_page_config(page_title="Lojistik & Gümrük Borsası", page_icon="🚢", layout="wide")

# --- SESSION STATE ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_type = None
    st.session_state.user_name = None

# --- CSS (MÜŞTERİ PANELİ İÇİN ÖZEL) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .report-card { background: white; padding: 20px; border-radius: 12px; border-left: 8px solid #1e3a8a; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .offer-card { background: #f0f9ff; padding: 15px; border-radius: 10px; border: 1px solid #bae6fd; margin-bottom: 10px; }
    .price-tag { font-size: 20px; color: #1e3a8a; font-weight: 800; }
    .info-box { background: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FONKSİYONLAR ---
def talebi_kaydet(uid, isim, fiyat, adet, agirlik, analiz, yuk_tipi):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "INSERT INTO requests (user_id, product_name, price, quantity, weight, ai_analysis, extra_info) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (uid, isim, fiyat, adet, agirlik, analiz, yuk_tipi))
            conn.commit()
        finally:
            conn.close()

# --- ANA DÖNGÜ ---
if not st.session_state.user_id:
    # --- GİRİŞ / KAYIT VE VİTRİN EKRANI (BURASI ZATEN ÇALIŞIYORDU) ---
    st.title("🚢 Lojistik & Gümrük Borsası")
    # ... (Önceki mesajdaki Giriş/Kayıt/Vitrin kodları burada yer almalı)
    st.info("Lütfen giriş yapın veya analiz yapın.")

else:
    # --- GİRİŞ YAPILMIŞ: MÜŞTERİ VEYA FİRMA PANELİ ---
    st.sidebar.success(f"Hoş geldin, {st.session_state.user_name}")
    if st.sidebar.button("🚪 Güvenli Çıkış"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.user_type == 'musteri':
        st.header("🏢 İthalatçı İşlem Paneli")
        
        tab_list, tab_new = st.tabs(["📋 Taleplerim & Teklifler", "➕ Yeni Talep Oluştur"])
        
        with tab_list:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM requests WHERE user_id = %s ORDER BY id DESC", (st.session_state.user_id,))
                talepler = cursor.fetchall()
                
                if not talepler:
                    st.warning("Henüz kayıtlı bir ithalat talebiniz bulunmuyor.")
                
                for t in talepler:
                    with st.expander(f"📦 {t['product_name']} - {t['created_at'].strftime('%d/%m/%Y')}"):
                        col_analiz, col_teklif = st.columns([1.5, 1])
                        
                        with col_analiz:
                            st.markdown("#### 🤖 AI Analiz Raporu")
                            st.markdown(f"<div class='report-card'>{t['ai_analysis']}</div>", unsafe_allow_html=True)
                        
                        with col_teklif:
                            st.markdown("#### 🚢 Gelen Teklifler")
                            cursor.execute("""SELECT o.*, u.username, u.phone FROM offers o 
                                           JOIN users u ON o.firm_id = u.id 
                                           WHERE o.request_id = %s""", (t['id'],))
                            teklifler = cursor.fetchall()
                            if not teklifler:
                                st.info("Şu an teklif bekleniyor...")
                            for o in teklifler:
                                st.markdown(f"""
                                <div class='offer-card'>
                                    <div class='price-tag'>{o['offer_amount']}$</div>
                                    <b>Firma:</b> {o['username']}<br>
                                    ⏱ <b>Süre:</b> {o['delivery_days']} Gün<br>
                                    📞 <b>İletişim:</b> {o['phone']}
                                    <p style='font-size:13px; color:#64748b; margin-top:5px;'>{o['firm_note']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                if st.button("Teklifi Sil", key=f"del_{o['id']}"):
                                    cursor.execute("DELETE FROM offers WHERE id=%s", (o['id'],))
                                    conn.commit()
                                    st.rerun()
                conn.close()

        with tab_new:
            st.subheader("Yeni Bir İthalat Maliyeti Hesapla")
            with st.form("yeni_talep_form", clear_on_submit=True):
                u_n = st.text_input("Ürün İsmi")
                y_n = st.selectbox("Yükleme Tipi", ["Parsiyel", "Konteyner", "Hava", "Kurye"])
                c1, c2, c3 = st.columns(3)
                f_n = c1.number_input("Birim $")
                a_n = c2.number_input("Adet", step=1)
                k_n = c3.number_input("Toplam KG")
                
                if st.form_submit_button("Analiz Et ve İlana Çık 🚀"):
                    with st.spinner("AI Rapor Hazırlıyor..."):
                        res = requests.post("http://localhost:8000/hesapla", json={"isim": f"{u_n} ({y_n})", "fiyat": f_n, "adet": a_n, "agirlik": k_n})
                        if res.status_code == 200:
                            talebi_kaydet(st.session_state.user_id, u_n, f_n, a_n, k_n, res.json()["analiz"], y_n)
                            st.balloons()
                            st.success("Talebiniz başarıyla oluşturuldu! 'Taleplerim' sekmesinden takip edebilirsiniz.")
                            time.sleep(1)
                            st.rerun()

    else:
        # --- FİRMA PANELİ ---
        st.header("🚛 Firma Teklif Borsası")
        # Firma paneli kodları (Teklif verme ve düzenleme) burada yer alacak
