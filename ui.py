import streamlit as st
import mysql.connector
import requests
import time
import json

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
    st.session_state.user_items = [] 

# --- GELİŞMİŞ CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .item-row { background: #f1f5f9; padding: 12px; border-radius: 10px; margin-bottom: 8px; border: 1px solid #cbd5e1; display: flex; justify-content: space-between; }
    .premium-card { background: white; padding: 25px; border-radius: 15px; border-left: 8px solid #1e3a8a; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .blur-text { filter: blur(5px); opacity: 0.4; pointer-events: none; }
    .total-kg-box { background: #1e3a8a; color: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-top: 10px; }
    .offer-card { background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 15px; margin-bottom: 10px; border-left: 5px solid #3b82f6; }
    .badge-log { background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; }
    .badge-gum { background: #fef9c3; color: #854d0e; padding: 2px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FONKSİYONLAR ---
def talebi_kaydet(uid, urunler, yuk_tipi, teslim_sekli, analiz):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            urunler_str = json.dumps(urunler, ensure_ascii=False)
            query = "INSERT INTO requests (user_id, product_name, extra_info, load_type, ai_analysis, status) VALUES (%s, %s, %s, %s, %s, 'aktif')"
            cursor.execute(query, (uid, urunler_str, teslim_sekli, yuk_tipi, analiz))
            conn.commit()
        finally:
            conn.close()

# --- 1. DURUM: ZİYARETÇİ EKRANI ---
if not st.session_state.user_id:
    tab_ana, tab_auth = st.tabs(["📊 Çoklu Ürün Analizi", "🔐 Giriş / Kayıt"])
    
    with tab_ana:
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.subheader("📦 İthalat Kalemlerini Ekleyin")
            with st.container(border=True):
                u_ad = st.text_input("Ürün İsmi", placeholder="Örn: Akıllı Saat")
                c1, c2, c3 = st.columns(3)
                u_fiyat = c1.number_input("Birim Fiyat ($)", min_value=0.0)
                u_adet = c2.number_input("Adet", min_value=1, step=1)
                u_kilo = c3.number_input("Birim Kilo (KG)", min_value=0.0, format="%.2f")
                if st.button("➕ Listeye Ekle"):
                    if u_ad and u_fiyat > 0:
                        st.session_state.user_items.append({"isim": u_ad, "fiyat": u_fiyat, "adet": int(u_adet), "kilo": u_kilo})
                        st.rerun()
                if st.session_state.user_items:
                    st.write("---")
                    toplam_kg = 0
                    for idx, itm in enumerate(st.session_state.user_items):
                        satir_kg = itm['kilo'] * itm['adet']
                        toplam_kg += satir_kg
                        st.markdown(f"<div class='item-row'><span>📦 <b>{itm['isim']}</b> - {itm['adet']} Adet ({itm['fiyat']}$) - Toplam: {satir_kg:.2f} KG</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='total-kg-box'>🚛 TOPLAM SEVKİYAT AĞIRLIĞI: {toplam_kg:.2f} KG</div>", unsafe_allow_html=True)
                    if st.button("🗑 Listeyi Temizle"):
                        st.session_state.user_items = []
                        st.rerun()

            st.subheader("🚛 Lojistik ve Teslimat Detayları")
            with st.container(border=True):
                y_tip = st.selectbox("Yükleme Tipi", ["Konteyner (FCL)", "Parsiyel (LCL)", "Hava Kargo", "Hızlı Kurye", "Karayolu Tır"])
                t_sekli = st.selectbox("Teslim Şekli (Incoterms)", ["EXW - Fabrika Teslim", "FOB - Liman Teslim", "CIF - Sigorta ve Navlun Dahil", "DDP - Gümrük Ödenmiş Kapı Teslim"])
                if st.button("Analiz Et ve İlana Çık 🚀"):
                    if not st.session_state.user_items:
                        st.error("Lütfen önce en az bir ürün ekleyin.")
                    else:
                        with st.spinner("AI Mevzuatı İnceliyor..."):
                            t_kg = sum(x['kilo'] * x['adet'] for x in st.session_state.user_items)
                            prompt_text = f"Ürünler: {json.dumps(st.session_state.user_items)} | Toplam Ağırlık: {t_kg} KG | Yükleme: {y_tip} | Teslim: {t_sekli}"
                            res = requests.post("http://localhost:8000/hesapla", json={"isim": prompt_text, "fiyat": 0, "adet": 0, "agirlik": t_kg})
                            if res.status_code == 200:
                                st.session_state.temp_res = res.json()["analiz"]
                                st.rerun()

        with col2:
            st.subheader("📊 Analiz Ön İzleme")
            if st.session_state.temp_res:
                st.markdown(f"<div class='premium-card'>{st.session_state.temp_res[:250]}...</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='blur-text'>{st.session_state.temp_res[250:800]}</div>", unsafe_allow_html=True)
                st.info("🔒 Tam raporu ve firmaların navlun tekliflerini görmek için Giriş Yapın.")
            else:
                st.info("Ürünleri ekleyip detayları seçtiğinizde raporunuz burada belirecek.")

    with tab_auth:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### 🔑 Giriş Yap")
            with st.container(border=True):
                le = st.text_input("E-posta", key="log_email")
                lp = st.text_input("Şifre", type="password", key="log_pass")
                if st.button("Giriş Yap 🚀"):
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor(dictionary=True)
                        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (le, lp))
                        u = cursor.fetchone()
                        if u:
                            st.session_state.user_id = u['id']
                            st.session_state.user_type = u['user_type']
                            st.session_state.user_name = u['username']
                            if st.session_state.user_items and st.session_state.temp_res:
                                talebi_kaydet(u['id'], st.session_state.user_items, y_tip, t_sekli, st.session_state.temp_res)
                            st.rerun()
                        else: st.error("Hatalı e-posta veya şifre.")
        with col_r:
            st.markdown("### 📝 Yeni Kayıt Ol")
            with st.container(border=True):
                r_type = st.radio("Üyelik Tipiniz", ["musteri", "lojistik_firmasi", "gumruk_musaviri"], horizontal=True)
                r_name = st.text_input("İlgili Kişi / Firma Adı")
                r_mail = st.text_input("E-posta Adresi", key="reg_email")
                r_tel = st.text_input("Telefon Numarası")
                r_pass = st.text_input("Şifre Belirleyin", type="password", key="reg_pass")
                if st.button("Kaydı Tamamla ✨"):
                    if r_name and r_mail and r_pass:
                        conn = get_db_connection()
                        if conn:
                            try:
                                cursor = conn.cursor()
                                cursor.execute("INSERT INTO users (username, email, password, user_type, phone) VALUES (%s,%s,%s,%s,%s)", (r_name, r_mail, r_pass, r_type, r_tel))
                                conn.commit()
                                st.success("Kayıt Başarılı! Şimdi giriş yapabilirsiniz.")
                            except: st.error("Hata: Bu e-posta zaten kayıtlı olabilir.")
                            finally: conn.close()
                    else: st.warning("Lütfen zorunlu alanları doldurun.")

# --- 2. DURUM: GİRİŞ YAPILMIŞ PANELLER ---
else:
    st.sidebar.success(f"Hoş geldin, {st.session_state.user_name}")
    if st.sidebar.button("🚪 Güvenli Çıkış"):
        st.session_state.clear()
        st.rerun()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if st.session_state.user_type == 'musteri':
        st.header("🏢 İthalatçı Kontrol Merkezi")
        m_tab1, m_tab2 = st.tabs(["📋 Taleplerim & Gelen Teklifler", "➕ Yeni Talep Oluştur"])
        
        with m_tab1:
            cursor.execute("SELECT * FROM requests WHERE user_id=%s ORDER BY id DESC", (st.session_state.user_id,))
            talepler = cursor.fetchall()
            for t in talepler:
                # Ürün listesini çöz
                try: urun_listesi = json.loads(t['product_name'])
                except: urun_listesi = [{"isim": t['product_name'], "fiyat": 0, "adet": 0, "kilo": 0}]
                
                with st.expander(f"📦 Talep Detayı: {t['created_at'].strftime('%d/%m/%Y %H:%M')}"):
                    st.write("### 📝 Talep İçeriği")
                    c_info1, c_info2 = st.columns(2)
                    with c_info1:
                        st.info(f"**Yükleme Tipi:** {t['load_type']}\n\n**Teslim Şekli:** {t['extra_info']}")
                    with c_info2:
                        toplam_agirlik = sum(itm.get('kilo', 0) * itm.get('adet', 0) for itm in urun_listesi)
                        st.success(f"**Toplam Ürün Sayısı:** {len(urun_listesi)}\n\n**Toplam Ağırlık:** {toplam_agirlik:.2f} KG")
                    
                    st.write("#### Ürün Kalemleri")
                    for itm in urun_listesi:
                        st.markdown(f"- **{itm.get('isim')}**: {itm.get('adet')} Adet | Birim: {itm.get('fiyat')}$ | Toplam: {itm.get('kilo',0)*itm.get('adet',0):.2f} KG")
                    
                    st.divider()
                    col_analiz, col_teklifler = st.columns([1.5, 1])
                    with col_analiz:
                        st.markdown(f"<div class='premium-card'><b>🤖 AI Gümrük & Mevzuat Analizi:</b><br>{t['ai_analysis']}</div>", unsafe_allow_html=True)
                        if st.button("Talebi Güncelle/Düzenle", key=f"edit_{t['id']}"):
                            st.toast("Düzenleme özelliği yakında aktif edilecek!")
                    
                    with col_teklifler:
                        st.markdown("#### 🚢 Gelen Teklifler")
                        cursor.execute("SELECT o.*, u.username, u.user_type, u.phone FROM offers o JOIN users u ON o.firm_id = u.id WHERE o.request_id=%s", (t['id'],))
                        offers = cursor.fetchall()
                        if not offers: st.info("Teklif bekleniyor...")
                        for o in offers:
                            is_log = o['user_type'] == 'lojistik_firmasi'
                            label = "🚚 Lojistik Teklifi" if is_log else "📜 Gümrük Müşavirliği Teklifi"
                            badge_class = "badge-log" if is_log else "badge-gum"
                            st.markdown(f"""
                                <div class='offer-card'>
                                    <span class='{badge_class}'>{label}</span><br><br>
                                    <b>{o['username']}</b><br>
                                    Fiyat: <b>{o['offer_amount']}$</b> | Süre: {o['delivery_days']} Gün<br>
                                    📞 {o['phone']}
                                </div>""", unsafe_allow_html=True)
                            ca1, ca2 = st.columns(2)
                            ca1.button("✅ Kabul Et", key=f"acc_{o['id']}")
                            ca2.button("❌ Reddet", key=f"rej_{o['id']}")

        with m_tab2:
            # Ana sayfadaki ürün listesi formunu aynen buraya taşıdık
            st.subheader("📦 Yeni İthalat Kalemlerini Ekleyin")
            col_n1, col_n2 = st.columns([1, 1], gap="large")
            with col_n1:
                with st.container(border=True):
                    nu_ad = st.text_input("Ürün İsmi", placeholder="Örn: Akıllı Saat", key="nu_ad")
                    nc1, nc2, nc3 = st.columns(3)
                    nu_fiyat = nc1.number_input("Birim Fiyat ($)", min_value=0.0, key="nu_fiyat")
                    nu_adet = nc2.number_input("Adet", min_value=1, step=1, key="nu_adet")
                    nu_kilo = nc3.number_input("Birim Kilo (KG)", min_value=0.0, format="%.2f", key="nu_kilo")
                    if st.button("➕ Listeye Ekle", key="nu_add"):
                        if nu_ad and nu_fiyat > 0:
                            st.session_state.user_items.append({"isim": nu_ad, "fiyat": nu_fiyat, "adet": int(nu_adet), "kilo": nu_kilo})
                            st.rerun()
                    if st.session_state.user_items:
                        st.write("---")
                        t_kg = 0
                        for itm in st.session_state.user_items:
                            s_kg = itm['kilo'] * itm['adet']; t_kg += s_kg
                            st.markdown(f"<div class='item-row'><span>📦 <b>{itm['isim']}</b> - {itm['adet']} Adet ({itm['fiyat']}$)</span></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='total-kg-box'>🚛 TOPLAM AĞIRLIK: {t_kg:.2f} KG</div>", unsafe_allow_html=True)
                        if st.button("🗑 Listeyi Temizle", key="nu_clr"):
                            st.session_state.user_items = []
                            st.rerun()
            with col_n2:
                st.subheader("🚛 Lojistik ve Teslimat")
                with st.container(border=True):
                    ny_tip = st.selectbox("Yükleme Tipi", ["Konteyner (FCL)", "Parsiyel (LCL)", "Hava Kargo", "Hızlı Kurye"], key="ny_tip")
                    nt_sekli = st.selectbox("Teslim Şekli (Incoterms)", ["EXW", "FOB", "CIF", "DDP"], key="nt_sekli")
                    if st.button("Analizi Başlat ve Yayınla 🚀", key="nu_pub"):
                        if not st.session_state.user_items: st.error("Ürün eklemediniz!")
                        else:
                            with st.spinner("AI Analiz Ediyor..."):
                                tkg = sum(x['kilo']*x['adet'] for x in st.session_state.user_items)
                                p_text = f"Ürünler: {json.dumps(st.session_state.user_items)} | Toplam: {tkg}KG | Yük: {ny_tip} | Teslim: {nt_sekli}"
                                res = requests.post("http://localhost:8000/hesapla", json={"isim": p_text, "fiyat": 0, "adet": 0, "agirlik": tkg})
                                if res.status_code == 200:
                                    talebi_kaydet(st.session_state.user_id, st.session_state.user_items, ny_tip, nt_sekli, res.json()["analiz"])
                                    st.session_state.user_items = []
                                    st.success("Talebiniz başarıyla yayınlandı!"); time.sleep(1); st.rerun()

    else:
        # --- FİRMA PANELİ ---
        st.header(f"🏢 {st.session_state.user_type.upper()} Paneli")
        f_tab1, f_tab2 = st.tabs(["🔔 Yeni Talepler", "✅ Verdiklerim"])
        with f_tab1:
            cursor.execute("""SELECT r.*, u.username as musterı FROM requests r JOIN users u ON r.user_id = u.id 
                           WHERE r.id NOT IN (SELECT request_id FROM offers WHERE firm_id = %s) ORDER BY r.id DESC""", (st.session_state.user_id,))
            ilanlar = cursor.fetchall()
            for i in ilanlar:
                with st.expander(f"📦 Yeni İthalat Talebi | Müşteri: {i['musterı']}"):
                    st.write(f"**Yükleme:** {i['load_type']} | **Teslim:** {i['extra_info']}")
                    try: urunler = json.loads(i['product_name'])
                    except: urunler = []
                    for pr in urunler: st.write(f"- {pr.get('isim')}: {pr.get('adet')} Adet ({pr.get('kilo')} KG/Birim)")
                    with st.form(key=f"bid_{i['id']}"):
                        amt = st.number_input("Teklif Tutarı ($)", min_value=0.0)
                        days = st.number_input("Süre (Gün)", min_value=1, step=1)
                        if st.form_submit_button("Teklifi Gönder"):
                            cursor.execute("INSERT INTO offers (request_id, firm_id, offer_amount, delivery_days, firm_note) VALUES (%s,%s,%s,%s,%s)", (i['id'], st.session_state.user_id, amt, days, ""))
                            conn.commit(); st.success("Teklif iletildi!"); time.sleep(1); st.rerun()
        with f_tab2:
            cursor.execute("""SELECT r.product_name, o.* FROM offers o JOIN requests r ON o.request_id = r.id 
                           WHERE o.firm_id=%s ORDER BY o.id DESC""", (st.session_state.user_id,))
            for v in cursor.fetchall():
                st.markdown(f"<div class='offer-card'><b>İş: {v['product_name'][:50]}...</b><br>Teklifiniz: {v['offer_amount']}$ | Süre: {v['delivery_days']} Gün</div>", unsafe_allow_html=True)
    conn.close()
