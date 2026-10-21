import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re

# Sayfa Yapılandırması
st.set_page_config(
    page_title="YouTube AI Retention & Content Studio",
    layout="wide",
    page_icon="⚡"
)

# Özel CSS ile Ultra Modern Dashboard Tasarımı
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    
    /* Blok Kart Tasarımları */
    .block-card {
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* 1. Negatif Blok (Sert Eleştiri & İvme Kaybı) */
    .negatif-block {
        background: #221517;
        border: 1px solid #f85149;
    }
    .negatif-title {
        color: #f85149;
        font-size: 1.25rem;
        font-weight: bold;
        margin-bottom: 12px;
    }

    /* 2. Pozitif Blok (Viral Kancalar & Başarılar) */
    .pozitif-block {
        background: #12251e;
        border: 1px solid #2ea043;
    }
    .pozitif-title {
        color: #2ea043;
        font-size: 1.25rem;
        font-weight: bold;
        margin-bottom: 12px;
    }

    /* 3. Öneri & Format Bloğu */
    .oneri-block {
        background: #161b26;
        border: 1px solid #388bfd;
    }
    .oneri-title {
        color: #58a6ff;
        font-size: 1.25rem;
        font-weight: bold;
        margin-bottom: 12px;
    }

    /* 4. Beyaz Sonuç Paneli */
    .sonuc-block {
        background: #ffffff;
        color: #0d1117 !important;
        border-radius: 12px;
        padding: 25px;
        margin-top: 15px;
        box-shadow: 0 5px 25px rgba(255, 255, 255, 0.15);
    }
    .sonuc-title {
        color: #0d1117;
        font-size: 1.4rem;
        font-weight: 800;
        margin-bottom: 10px;
    }

    /* Buton Tasarımı */
    .stButton>button {
        background: linear-gradient(90deg, #2ea043 0%, #238636 100%);
        color: white;
        font-weight: bold;
        font-size: 16px;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.01);
        box-shadow: 0 4px 15px rgba(46, 160, 67, 0.4);
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ YouTube AI Retention & Video Analizörü")
st.caption("YouTube linki veya metin yapıştırın; ivme kayıplarını, güçlü anları ve format önerilerini ayrıştırılmış bloklarda görün.")

# API Key'i Streamlit Secrets'tan okuyoruz
api_key = st.secrets.get("GEMINI_API_KEY")

# Giriş Seçenekleri
tab1, tab2 = st.tabs(["🔗 YouTube Linki", "📝 Transkript / Metin Yapıştır"])

youtube_url = ""
user_transcript = ""

with tab1:
    youtube_url = st.text_input("YouTube Video URL / Linki:")

with tab2:
    user_transcript = st.text_area("Video konuşma metnini veya transkriptini buraya yapıştırın:", height=150)

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

if st.button("🚀 Analizi Başlat"):
    if not api_key:
        st.error("Sistemde Gemini API anahtarı bulunamadı! Lütfen Streamlit Secrets ayarlarını kontrol edin.")
    else:
        time_stamped_text = ""
        video_id = None
        
        # Veri Kontrolü
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

        if time_stamped_text:
            with st.spinner("AI video içeriğini inceliyor ve 3 farklı blok raporunu oluşturuyor..."):
                try:
                    genai.configure(api_key=api_key)
                    # Limitlere takılmamak için en kararlı modellerden biri
                    model = genai.GenerativeModel('gemini-1.5-flash')

                    # Özel Ayrıştırıcı Yapı İsteği
                    prompt = f"""
                    Sen profesyonel bir YouTube Algoritma & İçerik Analistisin.
                    Aşağıdaki video metnini inceleyerek yanıtını tam olarak belirtilen özel etiketler (TAG) arasında Türkçe olarak ver.

                    --- TRANSKRİPT ---
                    {time_stamped_text}
                    --- SONU ---

                    Lütfen cevabı şu formatı HİÇ BOZMADAN üret:

                    [NEGATIF]
                    - İvme kaybının yaşandığı dakikalar/kısımlar.
                    - Temponun düştüğü, izleyicinin sıkılabileceği anlar ve sert eleştiriler.
                    [/NEGATIF]

                    [POZITIF]
                    - Temponun tavan yaptığı, izleyiciyi elde tutan güçlü anlar.
                    - Videodaki en başarılı anlatım, ceza/ödül veya aksiyon kancaları (hooks).
                    [/POZITIF]

                    [ONERI]
                    - İvme kayıplarını engellemek için yapılması gereken düzeltmeler.
                    - Gelecek video için 3 adet yüksek tıklanmalı (CTR) Başlık & Thumbnail konsepti.
                    - Sonraki video için 1 adet format/kurgu tavsiyesi.
                    [/ONERI]

                    [SONUC]
                    - VİRAL POTANSİYEL SKORU: X / 100
                    - Genel Değerlendirme ve Özeti (2-3 cümlelik net sonuç kararı).
                    [/SONUC]
                    """

                    response = model.generate_content(prompt)
                    raw_text = response.text

                    # Regex ile Metinleri Bloklara Ayırma
                    negatif = re.search(r'\[NEGATIF\](.*?)\[/NEGATIF\]', raw_text, re.DOTALL)
                    pozitif = re.search(r'\[POZITIF\](.*?)\[/POZITIF\]', raw_text, re.DOTALL)
                    oneri = re.search(r'\[ONERI\](.*?)\[/ONERI\]', raw_text, re.DOTALL)
                    sonuc = re.search(r'\[SONUC\](.*?)\[/SONUC\]', raw_text, re.DOTALL)

                    negatif_txt = negatif.group(1).strip() if negatif else "Analiz oluşturulamadı."
                    pozitif_txt = pozitif.group(1).strip() if pozitif else "Analiz oluşturulamadı."
                    oneri_txt = oneri.group(1).strip() if oneri else "Analiz oluşturulamadı."
                    sonuc_txt = sonuc.group(1).strip() if sonuc else "Analiz oluşturulamadı."

                    st.success("Analiz Tamamlandı!")

                    # Video Varsa Küçük Önizleme Alanı
                    if video_id:
                        st.video(f"https://www.youtube.com/watch?v={video_id}")

                    # 3 ANA RENKLİ BLOK (Sütunlar)
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f'''
                        <div class="block-card negatif-block">
                            <div class="negatif-title">🔴 İvme Kaybı & Eleştiri</div>
                            {negatif_txt}
                        </div>
                        ''', unsafe_allow_html=True)

                    with col2:
                        st.markdown(f'''
                        <div class="block-card pozitif-block">
                            <div class="pozitif-title">🟢 Pozitif Yanlar & Kancalar</div>
                            {pozitif_txt}
                        </div>
                        ''', unsafe_allow_html=True)

                    with col3:
                        st.markdown(f'''
                        <div class="block-card oneri-block">
                            <div class="oneri-title">💡 Öneriler & Format Fikirleri</div>
                            {oneri_txt}
                        </div>
                        ''', unsafe_allow_html=True)

                    # EN ALTTA BEYAZ SONUÇ BLOĞU
                    st.markdown(f'''
                    <div class="sonuc-block">
                        <div class="sonuc-title">🏁 Genel Sonuç & Viral Potansiyel Raporu</div>
                        <div style="font-size: 1.1rem; line-height: 1.6;">
                            {sonuc_txt}
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                    # TXT İndirme Butonu
                    full_report = f"--- İVME KAYBI & ELEŞTİRİ ---\n{negatif_txt}\n\n--- POZİTİF YANLAR ---\n{pozitif_txt}\n\n--- ÖNERİLER ---\n{oneri_txt}\n\n--- GENEL SONUÇ ---\n{sonuc_txt}"
                    st.download_button(
                        label="📥 Tam Analiz Raporunu İndir (.txt)",
                        data=full_report,
                        file_name="YouTube_AI_Analiz_Raporu.txt",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"Bir hata oluştu: {str(e)}")
