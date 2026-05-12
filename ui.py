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
st.set_page_config(page_title="İthalat & Lojistik Borsası", page_icon="🏢", layout="wide")

# --- SESSION STATE ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_type = None
    st.session_state.user_name = None

# --- GELİŞMİŞ CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    /* Kurumsal Kartlar */
    .dashboard-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .info-label { color: #64748b; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }
    .info-value { color: #1e293b; font-size: 16px; font-weight: 700; }
    
    /* Teklif Kutuları */
    .offer-item {
        background: #ffffff;
        border-left: 5px solid #3b82f6;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .badge-label {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 800;
        margin-bottom: 10px;
        text-transform: uppercase;
    }
    .badge-log { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .badge-gum { background: #fef9c3; color: #854d0e; border: 1px solid #fef08a; }
    .price-text { font-size: 22px; color: #1e3a8a; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. DURUM: GİRİŞ VE KAYIT ---
if not st.session_state.user_id:
    tab_log, tab_reg = st.tabs(["🔑 Giriş Yap", "📝 Üye Ol"])
    
    with tab_log:
        st.subheader("Hoş Geldiniz")
        log_e = st.text_input("E-posta")
        log_p = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap 🚀"):
            with st.status("Veriler doğrulanıyor...", expanded=True) as status:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (log_e, log_p))
                    user = cursor.fetchone()
                    if user:
                        status.update(label="Giriş Başarılı! Panelinize aktarılıyorsunuz...", state="complete")
                        st.session_state.user_id = user['id']
                        st.session_state.user_type = user['user_type']
                        st.session_state.user_name = user['username']
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Giriş başarısız. Bilgileri kontrol edin.")
                conn.close()

    with tab_reg:
        # Kayıt kodları (Telefon numarası dahil)
        st.info("Kurumsal kayıt için formu doldurun.")

# --- 2. DURUM: MÜŞTERİ PANELİ ---
elif st.session_state.user_type == 'musteri':
    st.header("📋 İthalat Taleplerim & Teklif Takibi")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM requests WHERE user_id = %s ORDER BY id DESC", (st.session_state.user_id,))
        talepler = cursor.fetchall()
        
        if not talepler:
            st.info("Henüz bir talebiniz bulunmuyor.")
        
        for t in talepler:
            with st.expander(f"📦 {t['product_name']} - {t['created_at'].strftime('%d/%m/%Y %H:%M')}"):
                # Talep Bilgileri
                st.markdown(f"""
                <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px;'>
                    <div><div class='info-label'>Miktar</div><div class='info-value'>{t['quantity']} Adet</div></div>
                    <div><div class='info-label'>Toplam KG</div><div class='info-value'>{t['weight']} KG</div></div>
                    <div><div class='info-label'>Birim Fiyat</div><div class='info-value'>{t['price']}$</div></div>
                    <div><div class='info-label'>Yükleme Tipi</div><div class='info-value'>{t['extra_info']}</div></div>
                </div>
                """, unsafe_allow_html=True)
                
                # TEKLİF EKRANINI İKİYE BÖL
                col_gum, col_log = st.columns(2)
                
                with col_gum:
                    st.markdown("### 📜 Gümrükçü Teklifleri")
                    cursor.execute("""SELECT o.*, u.username, u.phone, u.email FROM offers o 
                                   JOIN users u ON o.firm_id = u.id 
                                   WHERE o.request_id = %s AND u.user_type = 'gumruk_musaviri'""", (t['id'],))
                    g_offers = cursor.fetchall()
                    if not g_offers: st.caption("Henüz gümrük teklifi yok.")
                    for go in g_offers:
                        st.markdown(f"""<div class='offer-item'><div class='badge-label badge-gum'>📜 GÜMRÜK MÜŞAVİRİ</div>
                        <div class='price-text'>{go['offer_amount']}$</div><b>{go['username']}</b><br>⏱ {go['delivery_days']} Gün | 📞 {go['phone']}</div>""", unsafe_allow_html=True)
                        if st.button("Sil", key=f"del_g_{go['id']}"):
                            cursor.execute("DELETE FROM offers WHERE id=%s", (go['id'],))
                            conn.commit()
                            st.rerun()

                with col_log:
                    st.markdown("### 🚚 Lojistikçi Teklifleri")
                    cursor.execute("""SELECT o.*, u.username, u.phone, u.email FROM offers o 
                                   JOIN users u ON o.firm_id = u.id 
                                   WHERE o.request_id = %s AND u.user_type = 'lojistik_firmasi'""", (t['id'],))
                    l_offers = cursor.fetchall()
                    if not l_offers: st.caption("Henüz lojistik teklifi yok.")
                    for lo in l_offers:
                        st.markdown(f"""<div class='offer-item'><div class='badge-label badge-log'>🚚 LOJİSTİK FİRMASI</div>
                        <div class='price-text'>{lo['offer_amount']}$</div><b>{lo['username']}</b><br>⏱ {lo['delivery_days']} Gün | 📞 {lo['phone']}</div>""", unsafe_allow_html=True)
                        if st.button("Sil", key=f"del_l_{lo['id']}"):
                            cursor.execute("DELETE FROM offers WHERE id=%s", (lo['id'],))
                            conn.commit()
                            st.rerun()
        conn.close()

# --- 3. DURUM: FİRMA PANELİ ---
else:
    st.header(f"🏢 {st.session_state.user_type.upper()} DASHBOARD")
    f_tab1, f_tab2 = st.tabs(["🔔 Yeni İş Fırsatları", "✅ Verdiklerim & Düzenle"])
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        with f_tab1:
            # Teklif verilmemiş olanlar
            cursor.execute("""SELECT r.*, u.username as musterı FROM requests r JOIN users u ON r.user_id = u.id 
                           WHERE r.id NOT IN (SELECT request_id FROM offers WHERE firm_id = %s) ORDER BY id DESC""", (st.session_state.user_id,))
            ilanlar = cursor.fetchall()
            for i in ilanlar:
                with st.expander(f"📦 {i['product_name']} | Müşteri: {i['musterı']}"):
                    st.markdown(f"""
                    <div class='dashboard-card'>
                        <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;'>
                            <div><div class='info-label'>Miktar</div><div class='info-value'>{i['quantity']} Adet</div></div>
                            <div><div class='info-label'>Ağırlık</div><div class='info-value'>{i['weight']} KG</div></div>
                            <div><div class='info-label'>Yükleme</div><div class='info-value'>{i['extra_info']}</div></div>
                            <div><div class='info-label'>Birim Fiyat</div><div class='info-value'>{i['price']}$</div></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.form(key=f"bid_f_{i['id']}", clear_on_submit=True):
                        st.write("### Teklifinizi Hazırlayın")
                        col_p, col_d = st.columns(2)
                        p_in = col_p.number_input("Hizmet Bedeli ($)", min_value=0.0)
                        d_in = col_d.number_input("Süre (Gün)", min_value=1, step=1)
                        n_in = st.text_area("Müşteri için notunuz")
                        if st.form_submit_button("Teklifi Gönder ve Kapat"):
                            cursor.execute("INSERT INTO offers (request_id, firm_id, offer_amount, delivery_days, firm_note) VALUES (%s,%s,%s,%s,%s)", (i['id'], st.session_state.user_id, p_in, d_in, n_in))
                            conn.commit()
                            st.success("✅ Teklifiniz iletildi. Bu ilan listenizden kaldırıldı.")
                            time.sleep(1)
                            st.rerun()

        with f_tab2:
            # Teklif verilmiş olanlar ve Düzenleme
            cursor.execute("""SELECT r.product_name, r.quantity, r.weight, r.extra_info, o.* FROM offers o 
                           JOIN requests r ON o.request_id = r.id WHERE o.firm_id = %s ORDER BY o.id DESC""", (st.session_state.user_id,))
            verilenler = cursor.fetchall()
            for v in verilenler:
                with st.container():
                    st.markdown(f"""<div class='offer-item'><b>Ürün: {v['product_name']}</b><br><span class='price-text'>{v['offer_amount']}$</span> | {v['delivery_days']} Gün</div>""", unsafe_allow_html=True)
                    with st.expander("Teklifi Güncelle"):
                        with st.form(key=f"edit_f_{v['id']}"):
                            np = st.number_input("Yeni Fiyat", value=float(v['offer_amount']))
                            nd = st.number_input("Yeni Süre", value=int(v['delivery_days']))
                            nn = st.text_area("Yeni Not", value=v['firm_note'])
                            if st.form_submit_button("Güncellemeyi Kaydet"):
                                cursor.execute("UPDATE offers SET offer_amount=%s, delivery_days=%s, firm_note=%s WHERE id=%s", (np, nd, nn, v['id']))
                                conn.commit()
                                st.success("Düzenleme kaydedildi.")
                                st.rerun()
        conn.close()

# SIDEBAR
if st.session_state.user_id:
    st.sidebar.button("🚪 Çıkış Yap", on_click=lambda: st.session_state.clear())
