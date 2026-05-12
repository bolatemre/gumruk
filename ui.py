import streamlit as st
import mysql.connector
import requests

# SQL Bağlantı Bilgilerin
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
    except Exception as e:
        st.error(f"⚠️ Veritabanı bağlantı hatası: {e}")
        return None

# Sayfa Ayarları
st.set_page_config(page_title="GümrükAsistanı AI", page_icon="🚢", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #1e3a8a; color: white; font-weight: bold; }
    .report-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# Oturum Durumu
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_type = None

# --- HEADER ---
st.title("🚢 GümrükAsistanı: İthalat & Teklif Borsası")
st.divider()

# --- GİRİŞ YAPILMAMIŞSA ---
if not st.session_state.user_id:
    tab1, tab2, tab3 = st.tabs(["📊 Hızlı Analiz", "🔑 Giriş Yap", "📝 Kayıt Ol"])
    
    with tab1:
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.subheader("📦 Ürün Bilgilerini Girin")
            with st.container(border=True):
                urun_adi = st.text_input("Ürün Adı", placeholder="Örn: Akıllı Robot Süpürge", key="input_urun")
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    fiyat = st.number_input("Birim Fiyat (USD)", min_value=0.0, format="%.2f", key="input_fiyat")
                    adet = st.number_input("Adet", min_value=1, step=1, key="input_adet")
                with f_col2:
                    agirlik = st.number_input("Toplam Ağırlık (KG)", min_value=0.0, key="input_agirlik")
                
                analiz_btn = st.button("Maliyeti Hesapla 🚀", key="btn_hesapla")
        
        with col2:
            st.subheader("📝 Analiz Raporu")
            if analiz_btn:
                if not urun_adi or fiyat == 0:
                    st.warning("Lütfen ürün adı ve fiyat bilgilerini girin.")
                else:
                    with st.spinner("AI Hesaplıyor..."):
                        try:
                            res = requests.post("http://localhost:8000/hesapla", 
                                             json={"isim": urun_adi, "fiyat": fiyat, "adet": int(adet), "agirlik": agirlik})
                            if res.status_code == 200:
                                st.info("🔒 Analizin tamamını görmek ve teklif toplamak için giriş yapmalısınız.")
                                st.markdown(f"<div class='report-card'>{res.json()['analiz'][:300]}... [İÇERİK GİZLENDİ]</div>", unsafe_allow_html=True)
                            else:
                                st.error("Analiz motoruna ulaşılamadı.")
                        except:
                            st.error("Bağlantı hatası.")

    with tab2:
        st.subheader("Sisteme Giriş Yap")
        login_e = st.text_input("Email Adresiniz", key="login_email")
        login_p = st.text_input("Şifre", type="password", key="login_pass")
        if st.button("Giriş Yap", key="btn_login"):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (login_e, login_p))
                user = cursor.fetchone()
                if user:
                    st.session_state.user_id = user['id']
                    st.session_state.user_type = user['user_type']
                    st.rerun()
                else:
                    st.error("Email veya şifre hatalı.")
                conn.close()

    with tab3:
        st.subheader("Yeni Hesap Oluştur")
        y_isim = st.text_input("Ad Soyad / Firma Ünvanı", key="reg_isim")
        y_e = st.text_input("Email", key="reg_email")
        y_p = st.text_input("Şifre", type="password", key="reg_pass")
        y_tip = st.selectbox("Üyelik Tipi", ["musteri", "lojistik_firmasi", "gumruk_musaviri"], key="reg_tip")
        if st.button("Kayıt Ol", key="btn_reg"):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO users (email, password, user_type, username) VALUES (%s, %s, %s, %s)", 
                                 (y_e, y_p, y_tip, y_isim))
                    conn.commit()
                    st.success("Kayıt başarılı! Giriş sekmesine geçebilirsiniz.")
                except Exception as e:
                    st.error(f"Hata: {e}")
                finally:
                    conn.close()

# --- GİRİŞ YAPILMAMIŞSA ---
else:
    st.sidebar.title("Menü")
    st.sidebar.write(f"Hoş geldiniz, **{st.session_state.user_type.upper()}**")
    if st.sidebar.button("Güvenli Çıkış", key="btn_logout"):
        st.session_state.user_id = None
        st.session_state.user_type = None
        st.rerun()

    if st.session_state.user_type == 'musteri':
        st.header("🏢 Müşteri Paneli")
        st.write("Hesaplamalarınızı yapın ve gümrük/lojistik firmalarından teklif toplayın.")
    else:
        st.header("🚛 Firma Teklif Paneli")
        st.write("Bekleyen müşteri talepleri aşağıda listelenmiştir.")
