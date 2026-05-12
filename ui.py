import streamlit as st
import mysql.connector
import requests

# SQL Bağlantı Bilgilerin
DB_CONFIG = {
    "host": "localhost", # Eğer phpMyAdmin aynı sunucudaysa localhost, dışarıdaysa IP yazılmalı
    "user": "u115468925_lojistik",
    "password": "l123456M.",
    "database": "u115468925_lojistik"
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        st.error(f"Veritabanı bağlantı hatası: {e}")
        return None

# Sayfa Ayarları
st.set_page_config(page_title="Lojistik Borsası", layout="wide")

# Giriş Kontrolü
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_type = None

st.title("🚢 Gümrük & Lojistik İthalat Borsası")

# --- KAYIT VE GİRİŞ FONKSİYONLARI ---
def kayit_ol(email, sifre, tip, isim):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            query = "INSERT INTO users (email, password, user_type, username) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (email, sifre, tip, isim))
            conn.commit()
            st.success("Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
        except Exception as e:
            st.error(f"Kayıt hatası: {e}")
        finally:
            conn.close()

def giris_yap(email, sifre):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE email = %s AND password = %s"
        cursor.execute(query, (email, sifre))
        user = cursor.fetchone()
        conn.close()
        return user
    return None

# --- ANA EKRAN ---
if not st.session_state.user_id:
    tab1, tab2, tab3 = st.tabs(["📊 Hızlı Hesapla", "🔑 Giriş Yap", "📝 Kayıt Ol"])
    
    with tab1:
        st.subheader("Ürün Maliyetini Gör")
        urun = st.text_input("Ürün Adı")
        fiyat = st.number_input("Birim Fiyat ($)")
        if st.button("Analiz Et"):
            # Burada AI çalışır ama sonucu kısıtlı gösterir
            st.warning("⚠️ Analizin tamamını görmek ve teklif toplamak için giriş yapmalısınız.")
            
    with tab2:
        e = st.text_input("Email", key="login_e")
        p = st.text_input("Şifre", type="password", key="login_p")
        if st.button("Giriş"):
            user = giris_yap(e, p)
            if user:
                st.session_state.user_id = user['id']
                st.session_state.user_type = user['user_type']
                st.rerun()
            else:
                st.error("Hatalı bilgiler.")

    with tab3:
        y_isim = st.text_input("Ad Soyad / Firma Ünvanı")
        y_e = st.text_input("Email")
        y_p = st.text_input("Şifre", type="password")
        y_tip = st.selectbox("Üyelik Tipi", ["musteri", "lojistik_firmasi", "gumruk_musaviri"])
        if st.button("Hesap Oluştur"):
            kayit_ol(y_e, y_p, y_tip, y_isim)

else:
    # GİRİŞ YAPILMIŞ PANEL
    st.sidebar.success(f"Giriş Başarılı: {st.session_state.user_type}")
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.user_id = None
        st.rerun()

    if st.session_state.user_type == 'musteri':
        st.header("🏢 Müşteri Paneli")
        # Burada ürün hesaplama ve "Teklif İste" butonları olacak
        st.write("Yeni bir ithalat talebi oluşturun veya eski tekliflerinizi görün.")
        
    else:
        st.header("🚛 Firma Teklif Paneli")
        st.write("Müşterilerden gelen güncel talepler burada listelenir.")
