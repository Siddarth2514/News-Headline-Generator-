import streamlit as st
from transformers import pipeline
import re
import base64
from gtts import gTTS
from io import BytesIO
from deep_translator import GoogleTranslator

# ✅ Set page config
st.set_page_config(
    page_title="News Article Headline Generator",
    layout="centered",
    page_icon="📰"
)

# ✅ Load model with caching
@st.cache_resource
def load_model():
    return pipeline("text2text-generation", model="google/flan-t5-large")

headline_model = load_model()

# ✅ Inject CSS and Floating Tips
st.markdown("""
<style>
body {
    background: linear-gradient(-45deg, #e0eafc, #cfdef3, #c2e9fb, #e0c3fc);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
}
@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
#floating-tips {
    position: fixed;
    top: 100px;
    left: 15px;
    width: 250px;
    background: #f9fbff;
    padding: 16px;
    border-radius: 12px;
    box-shadow: 0 0 15px rgba(0,0,0,0.1);
    font-size: 14px;
    z-index: 999;
    border-left: 5px solid #4a90e2;
}
#floating-tips h4 {
    margin-top: 0;
    font-size: 16px;
    color: #4a90e2;
}
.main-title {
    text-align: center;
    font-size: 48px;
    font-weight: 800;
    background: -webkit-linear-gradient(45deg, #4a90e2, #00c6ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.subtitle {
    text-align: center;
    font-size: 20px;
    color: #555;
    margin-bottom: 20px;
}
.headline-card {
    background: linear-gradient(135deg, #f0f4ff, #e3f2fd);
    border-left: 5px solid #4a90e2;
    padding: 20px;
    border-radius: 12px;
    font-size: 22px;
    font-weight: bold;
    margin-top: 20px;
    color: #222;
}
.stTextArea textarea {
    background-color: #fff;
    font-size: 16px;
}
.stButton>button {
    background-color: #4a90e2;
    color: white;
    font-weight: bold;
    font-size: 16px;
    padding: 0.6em 1.5em;
    border-radius: 8px;
    border: none;
    transition: 0.3s ease;
}
.stButton>button:hover {
    background-color: #336cb5;
}
.footer {
    text-align: center;
    font-size: 14px;
    color: #999;
    margin-top: 40px;
}
</style>

<div id="floating-tips">
    <h4>💡 Quick Tips</h4>
    <ul>
        <li>Paste real/fake articles.</li>
        <li>Try different samples.</li>
        <li>Slide to get multiple variations.</li>
        <li>Download your output easily!</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# ✅ App Header
st.markdown("<div class='main-title'>📰 Headline Generator</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'> Powered by FLAN-T5-Large | N-gram + Transformers</div>", unsafe_allow_html=True)


# ✅ Language selection
lang_map = {
    "English": "en", "Hindi": "hi", "Spanish": "es", "French": "fr", "German": "de",
    "Tamil": "ta", "Telugu": "te", "Kannada": "kn", "Malayalam": "ml",
    "Gujarati": "gu", "Bengali": "bn", "Marathi": "mr"
}
selected_lang = st.selectbox("🌐 Select the language of your article:", list(lang_map.keys()))
lang_code = lang_map[selected_lang]

# ✅ Sample Articles
sample_options = {
    "Select a sample": "",
    "Love & Crime": "Despite their turbulent past, the couple was seen plotting a high-profile heist in the heart of Mumbai, shocking even the most seasoned detectives.",
    "Politics - Real": "The Prime Minister inaugurated a new expressway connecting Delhi to Jaipur, aiming to boost economic development and regional connectivity.",
    "Politics - Fake": "The Prime Minister has resigned abruptly due to pressure from alien forces controlling global politics."
}
sample_choice = st.selectbox("💡 Or select a sample article:", list(sample_options.keys()))
if sample_choice != "Select a sample":
    st.session_state.article_content = sample_options[sample_choice]

# ✅ Article Input
article_content = st.text_area("✍️ Paste or upload your article content below:", value=st.session_state.get("article_content", ""), height=250)

# ✅ Number of Headlines
st.markdown("### 🔢 Headline Variations")
num_variants = st.slider("Select how many headlines you want:", 1, 3, 1)

# 🌙 Dark Mode Toggle
dark_mode = st.toggle("🌙 Dark Mode")
if dark_mode:
    st.markdown("""
    <style>
    body, .stApp {
        background-color: #121212 !important;
        color: #e0e0e0 !important;
    }
    .headline-card {
        background: #1e1e1e !important;
        border-left: 5px solid #90caf9 !important;
        color: #f0f0f0 !important;
    }
    .subtitle {
        color: #aaa !important;
    }
    .footer {
        color: #777 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ✅ Session History
if "history" not in st.session_state:
    st.session_state.history = []

# ✅ Generate Button
generate = st.button("🚀 Generate Headline(s)")

if generate:
    if article_content.strip() == "":
        st.warning("⚠️ Please enter some article content.")
    else:
        with st.spinner("🧠 Generating headline(s)..."):
            # Translate article content to English for FLAN model
            if lang_code != "en":
                try:
                    article_translated = GoogleTranslator(source='auto', target='en').translate(article_content)
                except Exception as e:
                    st.error(f"Translation failed: {e}")
                    article_translated = article_content
            else:
                article_translated = article_content

            # Generate headlines
            prompt = f"Write a short, catchy, news-style headline for this article:\n\n{article_translated}\n\nHeadline:"
            results = headline_model(
                prompt,
                max_length=50,
                do_sample=True,
                top_k=50,
                top_p=0.95,
                temperature=0.8,
                num_return_sequences=num_variants
            )

            headlines = []
            for i in range(num_variants):
                headline = results[i]['generated_text'].replace("Headline:", "").strip()
                headline = re.sub(r'(\b\w+\b)( \1\b)+', r'\1', headline)
                # Translate back to selected language if needed
                if lang_code != "en":
                    try:
                        headline = GoogleTranslator(source='auto', target=lang_code).translate(headline)
                    except Exception as e:
                        st.error(f"Headline translation failed: {e}")
                headlines.append(headline)

        st.markdown("## 🗞️ Generated Headlines:")
        for idx, hline in enumerate(headlines, 1):
            st.markdown(f"<div class='headline-card'>{idx}. {hline}</div>", unsafe_allow_html=True)

            # ✅ Text-to-Speech
            try:
                tts = gTTS(hline, lang=lang_code)
                audio_fp = BytesIO()
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)
                st.audio(audio_fp, format="audio/mp3")
            except Exception as e:
                st.error(f"⚠️ Text-to-Speech failed: {e}")

        # ✅ Keyword Highlights
        keywords = list(set(re.findall(r'\b\w{5,}\b', article_content)))
        if keywords:
            st.markdown("### 🔍 Keyword Highlights from Article:")
            st.markdown(", ".join(keywords))

        # ✅ Download Option
        st.markdown("### 📥 Download Headlines")
        all_headlines = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
        b64 = base64.b64encode(all_headlines.encode()).decode()
        href = f'<a href="data:file/txt;base64,{b64}" download="headlines.txt">📄 Download as TXT</a>'
        st.markdown(href, unsafe_allow_html=True)

        # ✅ Save to History
        st.session_state.history.append(headlines)

# ✅ Session History
if st.session_state.history:
    st.markdown("### 📚 Previous Session Headlines:")
    for sess_num, session_headlines in enumerate(st.session_state.history):
        st.markdown(f"**Session {sess_num+1}:**")
        for h in session_headlines:
            st.markdown(f"- {h}")

# ✅ Footer
st.markdown("<div class='footer'>Made with ❤️ by Siddarth | Powered by HuggingFace + Streamlit</div>", unsafe_allow_html=True)
