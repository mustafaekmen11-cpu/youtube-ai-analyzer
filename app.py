import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re

# Sayfa Yapılandırması
st.set_page_config(page_title="YouTube AI Retention & Content Analyzer", layout="wide")

st.title("🎬 YouTube AI Video & İzleyici Etkileşim Analizörü")
st.caption("YouTube linkini yapıştırın; izlenmenin nerede arttığını ve sonraki videolar için tavsiyeleri AI çıkarsın.")

# API Key'i Streamlit Secrets'tan (Gizli Değişkenlerden) alıyoruz
api_key = st.secrets.get("GEMINI_API_KEY")

youtube_url = st.text_input("YouTube Video URL / Linki:")

def extract_video_id(url):
    """YouTube URL'sinden Video ID'sini çıkarır."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

if st.button("Analiz Et") and youtube_url:
    if not api_key:
        st.error("Sistemde Gemini API anahtarı bulunamadı! Lütfen Streamlit Secrets ayarlarını kontrol edin.")
    else:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            st.error("Geçersiz YouTube URL'si!")
        else:
            with st.spinner("Video transkripti çekiliyor ve AI analizi yapılıyor..."):
                try:
                    # 1. Transkript Çekme (Güncellenmiş Kullanım)
                    ytt = YouTubeTranscriptApi()
                    transcript_list = ytt.fetch(video_id, languages=['tr', 'en'])
                    
                    time_stamped_text = ""
                    for entry in transcript_list[:100]: # İlk bölüm örneklemesi
                        start_time = int(entry['start'])
                        minutes = start_time // 60
                        seconds = start_time % 60
                        time_str = f"{minutes:02d}:{seconds:02d}"
                        time_stamped_text += f"[{time_str}] {entry['text']}\n"

                    # 2. AI Analizi Hazırlığı
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')

                    prompt = f"""
                    Sen profesyonel bir YouTube İçerik ve Algoritma Danışmanısın.
                    Aşağıda zaman damgaları (timestamp) ile verilmiş bir YouTube video transkripti var:

                    --- TRANSKRİPT ---
                    {time_stamped_text}
                    --- SONU ---

                    Lütfen bu veriyi inceleyip şu başlıklar altında Türkçe detaylı rapor hazırla:
                    1. **İzleyici Etkileşiminin En Yüksek Olacağı Anlar:** Hangi dakikalardaki söylem veya olaylar izleyicinin dikkatini zirveye çıkarır? Neden?
                    2. **Kritik Bırakma Noktaları / Riskler:** Temponun düştüğü veya izleyicinin sıkılabileceği kısımlar var mı?
                    3. **Neden Artış Oldu? (Psikolojik & Format Analizi):** İzleyicinin tekrarlatarak izleyeceği kancalar (hooks) nelerdir?
                    4. **Gelecek Videolar İçin Taban & Tavsiyeler:** Bu formattan yola çıkarak bir sonraki video için 3 adet somut içerik/kurgu önerisi ver.
                    """

                    response = model.generate_content(prompt)

                    # 3. Sonuçları Gösterme
                    st.success("Analiz Tamamlandı!")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.subheader("📌 Video")
                        st.video(f"https://www.youtube.com/watch?v={video_id}")
                    
                    with col2:
                        st.subheader("📊 AI Analiz Raporu")
                        st.markdown(response.text)

                except Exception as e:
                    st.error(f"Bir hata oluştu: {str(e)}")
