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
    .report-card { background: white; padding: 25px; border-radius: 15px; border-left: 8px solid #1e3a8a; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-top:10px; }
    .blur-text { filter: blur(5px); opacity: 0.4; user-select: none; }
    .offer-box { background: #e0f2fe; padding: 15px; border-radius: 10px; border: 1px solid #0ea5e9; margin-bottom: 10px; }
    .stButton>button { border-radius: 10px; font-weight: bold; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- FONKSİYONLAR ---
def talebi_kaydet(uid, isim, fiyat, adet, agirlik, analiz, yukleme_tipi="Bilinmiyor"):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "INSERT INTO requests (user_id, product_name, price, quantity, weight, ai_analysis, extra_info) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (uid, isim, fiyat, adet, agirlik, analiz, yukleme_tipi))
            conn.commit()
        finally:
            conn.close()

# --- SIDEBAR ---
if st.session_state.user_id:
    with st.sidebar:
        st.success(f"Giriş Yapıldı: {st.session_state.user_name}")
        if st.button("Güvenli Çıkış"):
            st.session_state.user_id = None
            st.rerun()

# --- 1. DURUM: ZİYARETÇİ ---
if not st.session_state.user_id:
    t1, t2 = st.tabs(["🔍 Hızlı Maliyet Analizi", "🔑 Giriş / Kayıt"])
    
    with t1:
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.subheader("Ürün ve Lojistik Bilgileri")
            with st.form("vitrin_form"):
                u = st.text_input("Ürün Adı", placeholder="Örn: CNC Yedek Parça")
                yuk_tipi = st.selectbox("Yükleme Tipi", ["Parsiyel (LCL)", "Tam Konteyner (FCL)", "Hava Kargo", "Kurye/Numune"])
                c1, c2 = st.columns(2)
                f = c1.number_input("Birim Fiyat ($)", min_value=0.0)
                a = c2.number_input("Adet", min_value=1, step=1)
                kg = st.number_input("Toplam Ağırlık (KG)")
                submit = st.form_submit_button("Analizi Gör ve Teklif Topla 🚀")
                
                if submit:
                    if u and f > 0:
                        with st.spinner("AI Analiz Ediyor..."):
                            res = requests.post("http://localhost:8000/hesapla", json={"isim": f"{u} ({yuk_tipi})", "fiyat": f, "adet": a, "agirlik": kg})
                            if res.status_code == 200:
                                st.session_state.temp_res = res.json()["analiz"]
                                st.session_state.last_calc = {"isim": u, "fiyat": f, "adet": a, "agirlik": kg, "yukleme_tipi": yuk_tipi}
                    else: st.error("Eksik bilgi girdiniz.")
        
        with col2:
            st.subheader("📊 Ön Analiz Raporu")
            if st.session_state.temp_res:
                st.success("Analiz Hazır!")
                st.markdown(f"**Ürün:** {st.session_state.last_calc['isim']} | **Yük:** {st.session_state.last_calc['yukleme_tipi']}")
                st.markdown(f"<div>{st.session_state.temp_res[:150]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='blur-text'>{st.session_state.temp_res[150:600]}</div>", unsafe_allow_html=True)
                st.info("🔒 Tam rapor ve resmi teklifler için Giriş Yapın.")
            else: st.info("Formu doldurduğunuzda rapor burada belirecek.")

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
                    else: st.error("Hatalı bilgiler.")
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
                    st.success("Kayıt başarılı!")

# --- 2. DURUM: MÜŞTERİ PANELİ ---
elif st.session_state.user_type == 'musteri':
    st.header("🏢 İthalatçı Paneli")
    tab_list, tab_new = st.tabs(["📋 Taleplerim & Analizlerim", "➕ Yeni Talep Oluştur"])
    
    with tab_list:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM requests WHERE user_id = %s ORDER BY id DESC", (st.session_state.user_id,))
            for t in cursor.fetchall():
                with st.expander(f"📦 {t['product_name']} - {t['created_at'].strftime('%d/%m/%Y')}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown("#### 🤖 AI Analiz Raporu")
                        st.markdown(f"<div class='report-card'>{t['ai_analysis'] if t['ai_analysis'] else 'Analiz hazırlanıyor...'}</div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown("#### 🚢 Gelen Teklifler")
                        cursor.execute("SELECT o.*, u.username, u.user_type FROM offers o JOIN users u ON o.firm_id = u.id WHERE o.request_id = %s", (t['id'],))
                        for o in cursor.fetchall():
                            tip = "🚚 Lojistik" if o['user_type'] == 'lojistik_firmasi' else "📜 Gümrük"
                            st.markdown(f"<div class='offer-box'><b>{tip}: {o['offer_amount']}$</b><br>Firma: {o['username']}<br>Süre: {o['delivery_days']} Gün<br><i>{o['firm_note']}</i></div>", unsafe_allow_html=True)
            conn.close()

    with tab_new:
        with st.form("new_request_form", clear_on_submit=True):
            nu = st.text_input("Ürün Adı")
            nyuk = st.selectbox("Yükleme Tipi", ["Parsiyel (LCL)", "Tam Konteyner (FCL)", "Hava Kargo", "Kurye"])
            nf, na, nk = st.columns(3)
            f_val = nf.number_input("Birim Fiyat ($)")
            a_val = na.number_input("Adet", step=1)
            k_val = nk.number_input("Ağırlık (KG)")
            if st.form_submit_button("Analizi Başlat ve Yayınla 🚀"):
                res = requests.post("http://localhost:8000/hesapla", json={"isim": f"{nu} ({nyuk})", "fiyat": f_val, "adet": a_val, "agirlik": k_val})
                if res.status_code == 200:
                    talebi_kaydet(st.session_state.user_id, nu, f_val, a_val, k_val, res.json()["analiz"], nyuk)
                    st.success("Talebiniz yayına alındı!")

# --- 3. DURUM: FİRMA PANELİ ---
else:
    st.header(f"🚛 {'Lojistik' if st.session_state.user_type == 'lojistik_firmasi' else 'Gümrük'} Borsası")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT r.*, u.username FROM requests r JOIN users u ON r.user_id = u.id ORDER BY r.id DESC")
        for i in cursor.fetchall():
            with st.expander(f"📦 {i['product_name']} | Müşteri: {i['username']}"):
                col_i, col_f = st.columns([2, 1])
                with col_i:
                    st.write(f"**Talep:** {i['quantity']} Adet | {i['price']}$ Fiyat | {i['weight']} KG")
                    st.write(f"**Yükleme Tipi:** {i.get('extra_info', 'Belirtilmedi')}")
                    st.markdown("**AI Analizi:**")
                    # Hata düzeltme: Eğer analiz None ise boş string göster
                    analiz_text = i['ai_analysis'] if i['ai_analysis'] else "Analiz verisi bulunamadı."
                    st.write(analiz_text[:400] + "...")
                with col_f:
                    with st.form(key=f"bid_{i['id']}", clear_on_submit=True):
                        st.markdown("### Teklif Ver")
                        if st.session_state.user_type == 'lojistik_firmasi':
                            amt = st.number_input("Navlun Bedeli ($)")
                            days = st.number_input("Tahmini Varış (Gün)", step=1)
                            note = st.text_area("Lojistik Notu (Sigorta, İç nakliye vb.)")
                        else:
                            amt = st.number_input("Müşavirlik + Operasyon Bedeli ($)")
                            days = st.number_input("Gümrükleme Süresi (Gün)", step=1)
                            note = st.text_area("Gümrük Notu (GTİP, Ardiye tahmini vb.)")
                        
                        if st.form_submit_button("Teklifi Gönder"):
                            cursor.execute("INSERT INTO offers (request_id, firm_id, offer_amount, delivery_days, firm_note) VALUES (%s,%s,%s,%s,%s)", (i['id'], st.session_state.user_id, amt, days, note))
                            conn.commit()
                            st.success("Teklifiniz iletildi!")
        conn.close()
