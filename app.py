import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="Makro & Öğün Takipçisi", page_icon="🍱", layout="wide")

if 'ogun_listesi' not in st.session_state:
    st.session_state['ogun_listesi'] = {"Ana Yemek": [], "Salata": [], "Ara Öğün": []}

with st.sidebar:
    st.header("⚙️ Hedefler ve Kategori")
    secilen_kategori = st.selectbox("Hangi Kategori?", ["Ana Yemek", "Salata", "Ara Öğün"])
    st.divider()
    st.subheader("🎯 Günlük Hedeflerin")
    hedef_kalori = st.number_input("Günlük Kalori Hedefi", min_value=500, value=2000, step=100)
    hedef_protein = st.number_input("Protein Hedefi (g)", min_value=30, value=120, step=10)

st.title("📸 Akıllı Makro ve Öğün Hesaplayıcı")

def resmi_analiz_et(resim):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = 'Sen uzman diyetisyensin. Fotoğraf etiketse 100g değerini, yemekse porsiyonu tahmin et. Şu formatta JSON ver: {"kalori": 0, "protein": 0, "karbonhidrat": 0, "yag": 0}'
    try:
        # İşte sihirli kısım burası: Yapay zekayı sadece JSON vermeye zorluyoruz!
        response = model.generate_content([prompt, resim], generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Yapay zeka hatası: {e}")
        return {"kalori": 0, "protein": 0, "karbonhidrat": 0, "yag": 0}

st.subheader("1. Fotoğraf Yükle (Etiket veya Yemek)")
yuklenen_dosya = st.file_uploader("Yemek fotoğrafı seç", type=["jpg", "jpeg", "png"])

if yuklenen_dosya is not None:
    resim = Image.open(yuklenen_dosya)
    st.image(resim, width=300)
    if st.button("🔍 Yapay Zeka ile Analiz Et"):
        with st.spinner("Gemini analiz ediyor..."):
            st.session_state['gecici_degerler'] = resmi_analiz_et(resim)
            st.success("Tamamlandı!")

if 'gecici_degerler' in st.session_state:
    st.divider()
    d = st.session_state['gecici_degerler']
    with st.form("ekleme_formu"):
        malzeme_adi = st.text_input("Yemeğin Adı")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Kalori", f"{d.get('kalori', 0)} kcal")
        col2.metric("Protein", f"{d.get('protein', 0)} g")
        col3.metric("Karb", f"{d.get('karbonhidrat', 0)} g")
        col4.metric("Yağ", f"{d.get('yag', 0)} g")
        ekle_btn = st.form_submit_button("🍱 Tabağa Ekle")
        if ekle_btn and malzeme_adi:
            yeni = {"malzeme": malzeme_adi, "kalori": round(d.get('kalori',0),1), "protein": round(d.get('protein',0),1), "karb": round(d.get('karbonhidrat',0),1), "yag": round(d.get('yag',0),1)}
            st.session_state['ogun_listesi'][secilen_kategori].append(yeni)
            del st.session_state['gecici_degerler']
            st.rerun()

st.write("---")
st.header("📊 Günlük Özet ve İlerleme")
toplam_kalori, toplam_protein, toplam_karb, toplam_yag = 0, 0, 0, 0
ozet = "--- GÜNLÜK ÖZET ---\n\n"

for kategori, malzemeler in st.session_state['ogun_listesi'].items():
    if len(malzemeler) > 0:
        ozet += f"[{kategori}]\n"
        with st.expander(f"🔽 {kategori} Detayları", expanded=True):
            for m in malzemeler:
                st.write(f"🔹 {m['malzeme']} ➔ {m['kalori']} kcal | {m['protein']}g Pro | {m['karb']}g Karb | {m['yag']}g Yağ")
                ozet += f"- {m['malzeme']}: {m['kalori']} kcal, {m['protein']}g Pro\n"
                toplam_kalori += m['kalori']
                toplam_protein += m['protein']
                toplam_karb += m['karb']
                toplam_yag += m['yag']
        ozet += "\n"

m1, m2, m3, m4 = st.columns(4)
m1.metric("🔥 Toplam Kalori", f"{round(toplam_kalori, 1)} kcal")
m2.metric("🥩 Toplam Protein", f"{round(toplam_protein, 1)} g")
m3.metric("🍚 Toplam Karb.", f"{round(toplam_karb, 1)} g")
m4.metric("🥑 Toplam Yağ", f"{round(toplam_yag, 1)} g")

st.progress(min(toplam_kalori / hedef_kalori, 1.0))
st.progress(min(toplam_protein / hedef_protein, 1.0))

st.download_button("📥 Özeti İndir", data=ozet, file_name="ozet.txt", mime="text/plain")