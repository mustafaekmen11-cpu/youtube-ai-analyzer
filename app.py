import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re

# Sayfa Yapılandırması ve Teması
st.set_page_config(
    page_title="YouTube AI Retention & Critique Studio",
    layout="wide",
    page_icon="⚡"
)

# Özel CSS ile Modern Bloklu (Card UI) Tasarım ve Çerçeveler
st.markdown("""
<style>
    /* Ana Arka Plan */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Özel Kart (Blok) Stilleri */
    .custom-card {
        background: #1e222d;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2e3545;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    
    .critique-card {
        background: #2a1b24;
        border: 1px solid #ff4b4b;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .success-card {
        background: #1b2a24;
        border: 1px solid #00c853;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .card-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    /* Buton Tasarımı */
    .stButton>button {
        background: linear-gradient(90deg, #ff4b4b 0%, #ff8c00 100%);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(255, 75, 75, 0.4);
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ YouTube AI Retention & İvme Analizörü")
st.caption("Videodaki ivme kayıplarını, sıkıcı noktaları tespit edin ve yapay zeka eleştirileriyle sonraki videolarınızı geliştirin.")

# API Key'i Streamlit Secrets'tan alıyoruz
api_key = st.secrets.get("GEMINI_API_KEY")

tab1, tab2 = st.tabs(["🔗 Link ile Analiz Et", "📝 Transkript / Metin Yapıştır"])

youtube_url = ""
user_transcript = ""

with tab1:
    youtube_url = st.text_input("YouTube Video URL / Linki:")

with tab2:
    user_transcript = st.text_area("Video konuşma metnini veya transkriptini buraya yapıştırın:", height=200)

def extract_video_id(url):
    """YouTube URL'sinden Video ID'sini çıkarır."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

if st.button("🔥 İvme Kayıplarını & Videoyu Analiz Et"):
    if not api_key:
        st.error("Sistemde Gemini API anahtarı bulunamadı! Lütfen Streamlit Secrets ayarlarını kontrol edin.")
    else:
        time_stamped_text = ""
        video_id = None
        
        # 1. Veri Kaynağı Kontrolü
        if user_transcript.strip():
            time_stamped_text = user_transcript
        elif youtube_url.strip():
            video_id = extract_video_id(youtube_url)
            if not video_id:
                st.error("Geçersiz YouTube URL'si!")
            else:
                try:
                    ytt = YouTubeTranscriptApi()
                    transcript_list = ytt.fetch(video_id, languages=['tr', 'en'])
                    for entry in transcript_list[:120]:
                        start_time = int(entry['start'])
                        minutes = start_time // 60
                        seconds = start_time % 60
                        time_str = f"{minutes:02d}:{seconds:02d}"
                        time_stamped_text += f"[{time_str}] {entry['text']}\n"
                except Exception as e:
                    st.warning("YouTube IP engeli nedeniyle otomatik altyazı çekilemedi. Lütfen 'Transkript / Metin Yapıştır' sekmesini kullanın.")
        else:
            st.error("Lütfen bir YouTube linki girin veya metin yapıştırın.")

        # 2. AI İvme & Eleştiri Analizi
        if time_stamped_text:
            with st.spinner("AI videonun ivme kayıplarını ve tempo düşüşlerini analiz ediyor..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-3.8-flash')

                    prompt = f"""
                    Sen profesyonel, dürüst ve sert bir YouTube Algoritma & İçerik Eleştirmenisin.
                    Aşağıdaki video transkriptini/metnini inceleyerek videonun tempo düşüşlerini ve izleyici kaybı yaşayacağı anları analiz et:

                    --- TRANSKRİPT ---
                    {time_stamped_text}
                    --- SONU ---

                    Lütfen yanıtını tam olarak şu 4 ana başlık altında ve net bir dille Türkçe olarak ver:

                    1. **🚨 İVME KAYBI & TEMPO DÜŞÜŞÜ (ELEŞTİRİ):**
                    - Hangi dakikalarda/kısımlarda video ivme kaybediyor? 
                    - İzleyici nerede sıkılıp videoyu kapatır? Sert ve açık bir dille eleştir.

                    2. **🔥 VİRAL KANCALAR (EN GÜÇLÜ ANLAR):**
                    - Temponun yüksek olduğu, izleyiciyi tutan 2-3 kilit an nedir?

                    3. **🎯 DÜZELTME & AKSIYON PLANLARI:**
                    - Bu ivme kayıplarını engellemek için kurguda/senaryoda ne değiştirilmeliydi?

                    4. **🚀 GELECEK VİDEO İÇİN TABAN & FORMAT FİKRİ:**
                    - Bu hatalardan ders çıkararak bir sonraki videoda uygulanacak 1 adet eksiksiz kurgu/format fikri.
                    """

                    response = model.generate_content(prompt)
                    ai_output = response.text

                    st.success("Analiz Tamamlandı!")
                    
                    col_left, col_right = st.columns([1, 1])
                    
                    with col_left:
                        if video_id:
                            st.markdown('<div class="custom-card"><div class="card-title">📌 Analiz Edilen Video</div></div>', unsafe_allow_html=True)
                            st.video(f"https://www.youtube.com/watch?v={video_id}")
                        else:
                            st.markdown('<div class="custom-card"><div class="card-title">📌 Analiz Edilen Metin</div></div>', unsafe_allow_html=True)
                            st.text_area("", time_stamped_text, height=350, disabled=True)

                    with col_right:
                        st.markdown(f'<div class="critique-card"><div class="card-title">📊 AI İvme Kaybı & Eleştiri Raporu</div>{ai_output}</div>', unsafe_allow_html=True)
                        
                        st.download_button(
                            label="📥 Eleştiri Raporunu İndir (.txt)",
                            data=ai_output,
                            file_name="YouTube_Ivme_Kayıp_Raporu.txt",
                            mime="text/plain"
                        )

                except Exception as e:
                    st.error(f"Bir hata oluştu: {str(e)}")
