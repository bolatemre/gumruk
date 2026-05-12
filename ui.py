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
                        st.session_state.user_items.append({
                            "isim": u_ad, 
                            "fiyat": u_fiyat, 
                            "adet": int(u_adet),
                            "kilo": u_kilo
                        })
                        st.rerun()
                
                if st.session_state.user_items:
                    st.write("---")
                    toplam_kg = 0
                    for idx, itm in enumerate(st.session_state.user_items):
                        satir_kg = itm['kilo'] * itm['adet']
                        toplam_kg += satir_kg
                        st.markdown(f"""
                        <div class='item-row'>
                            <span>📦 <b>{itm['isim']}</b> - {itm['adet']} Adet ({itm['fiyat']}$) - Toplam: {satir_kg:.2f} KG</span>
                        </div>""", unsafe_allow_html=True)
                    
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
                        else:
                            st.error("Hatalı e-posta veya şifre.")

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
                                cursor.execute("INSERT INTO users (username, email, password, user_type, phone) VALUES (%s,%s,%s,%s,%s)", 
                                             (r_name, r_mail, r_pass, r_type, r_tel))
                                conn.commit()
                                st.success("Kayıt Başarılı! Şimdi giriş yapabilirsiniz.")
                            except Exception as e:
                                st.error(f"Hata: Bu e-posta zaten kayıtlı olabilir.")
                            finally:
                                conn.close()
                    else:
                        st.warning("Lütfen zorunlu alanları doldurun.")

else:
    st.sidebar.success(f"Hoş geldin, {st.session_state.user_name}")
    if st.sidebar.button("🚪 Güvenli Çıkış"):
        st.session_state.clear()
        st.rerun()
    
    # Burada kullanıcı tipine göre (Müşteri/Firma) paneller devam eder.
