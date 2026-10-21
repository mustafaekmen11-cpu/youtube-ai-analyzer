import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re

# Sayfa Yapılandırması
st.set_page_config(page_title="YouTube AI Retention & Content Analyzer", layout="wide")

st.title("🎬 YouTube AI Video & İzleyici Etkileşim Analizörü")
st.caption("YouTube linkini yapıştırın veya doğrudan transkript/konuşma metnini girerek AI analizini başlatın.")

# API Key'i Streamlit Secrets'tan alıyoruz
api_key = st.secrets.get("GEMINI_API_KEY")

tab1, tab2 = st.tabs(["🔗 Link ile Analiz Et", "📝 Metin / Transkript Yapıştır"])

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

if st.button("Analiz Et"):
    if not api_key:
        st.error("Sistemde Gemini API anahtarı bulunamadı! Lütfen Streamlit Secrets ayarlarını kontrol edin.")
    else:
        time_stamped_text = ""
        video_id = None
        
        # 1. Veri Kaynağını Belirleme
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
                    for entry in transcript_list[:100]:
                        start_time = int(entry['start'])
                        minutes = start_time // 60
                        seconds = start_time % 60
                        time_str = f"{minutes:02d}:{seconds:02d}"
                        time_stamped_text += f"[{time_str}] {entry['text']}\n"
                except Exception as e:
                    st.warning("YouTube sunucu IP engeli nedeniyle otomatik altyazı çekilemedi. Lütfen 'Metin / Transkript Yapıştır' sekmesini kullanarak videonun metnini ekleyin.")
        else:
            st.error("Lütfen bir YouTube linki girin veya metin yapıştırın.")

        # 2. AI Analiz Süreci
        if time_stamped_text:
            with st.spinner("AI Analizi yapılıyor..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')

                    prompt = f"""
                    Sen profesyonel bir YouTube İçerik ve Algoritma Danışmanısın.
                    Aşağıda verilmiş YouTube video metni/transkripti var:

                    --- METİN / TRANSKRİPT ---
                    {time_stamped_text}
                    --- SONU ---

                    Lütfen bu veriyi inceleyip şu başlıklar altında Türkçe detaylı rapor hazırla:
                    1. **İzleyici Etkileşiminin En Yüksek Olacağı Anlar:** Hangi kısımlardaki söylem veya olaylar izleyicinin dikkatini zirveye çıkarır? Neden?
                    2. **Kritik Bırakma Noktaları / Riskler:** Temponun düştüğü veya izleyicinin sıkılabileceği kısımlar var mı?
                    3. **Neden Artış Oldu? (Psikolojik & Format Analizi):** İzleyicinin tekrarlatarak izleyeceği kancalar (hooks) nelerdir?
                    4. **Gelecek Videolar İçin Taban & Tavsiyeler:** Bu formattan yola çıkarak bir sonraki video için 3 adet somut içerik/kurgu önerisi ver.
                    """

                    response = model.generate_content(prompt)

                    st.success("Analiz Tamamlandı!")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if video_id:
                            st.subheader("📌 Video")
                            st.video(f"https://www.youtube.com/watch?v={video_id}")
                        else:
                            st.subheader("📌 Analiz Edilen Metin")
                            st.text_area("Girdi Metni", time_stamped_text, height=300, disabled=True)
                    
                    with col2:
                        st.subheader("📊 AI Analiz Raporu")
                        st.markdown(response.text)

                except Exception as e:
                    st.error(f"Bir hata oluştu: {str(e)}")
