import os
import io

import cv2
import numpy as np
import pytesseract
from PIL import Image

import streamlit as st
import streamlit.components.v1 as components

# ====== OPTIONAL: SET TESSERACT PATH (Windows users) ======
# Uncomment and update this if needed:
# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

os.environ["OMP_THREAD_LIMIT"] = "1"  # minor speed tweak


# ====== OCR HELPERS ======
def preprocess_image(pil_img):
    """Convert to grayscale + threshold for faster, cleaner OCR."""
    gray = pil_img.convert("L")
    img_np = np.array(gray)

    # Simple binary threshold
    _, thresh = cv2.threshold(img_np, 150, 255, cv2.THRESH_BINARY)
    return Image.fromarray(thresh)


def ocr_from_pil_image(pil_img, lang="eng"):
    """Run Tesseract OCR on a PIL image."""
    # Resize very large images to speed up OCR
    max_size = 1200
    w, h = pil_img.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        pil_img = pil_img.resize(
            (int(w * scale), int(h * scale)), Image.LANCZOS
        )

    pil_img = preprocess_image(pil_img)

    custom_config = r"--oem 1 --psm 6"
    text = pytesseract.image_to_string(pil_img, lang=lang, config=custom_config)
    return text


# ====== BROWSER TTS HELPER (Web Speech API) ======
def speak_in_browser(text: str):
    """
    Use the browser's speechSynthesis API to read text aloud.
    This runs entirely in the user's browser.
    """
    text = (text or "").strip()
    if not text:
        st.warning("No text to read.")
        return

    # Escape for JS
    safe_text = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")

    js_code = f"""
    <script>
    (function() {{
        var text = '{safe_text}';
        if (!('speechSynthesis' in window)) {{
            alert("Speech synthesis not supported in this browser.");
            return;
        }}
        window.speechSynthesis.cancel();
        var utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.volume = 1.0;
        window.speechSynthesis.speak(utterance);
    }})();
    </script>
    """

    components.html(js_code, height=0, width=0)


# ====== STREAMLIT UI ======
st.set_page_config(
    page_title="Accessible Document Reader",
    layout="centered",
)

st.title("📖 Document Reading System for Visually Impaired")

st.markdown(
    "Upload a document image, I'll extract the text and **read it aloud**. "
    "You can also type text and have it read."
)

# Sidebar settings
st.sidebar.header("Settings")

ocr_lang = st.sidebar.selectbox(
    "OCR Language (Tesseract code):",
    options=["eng", "hin", "kan", "tam"],
    index=0,
    help="Make sure this language is installed in your Tesseract.",
)

font_size = st.sidebar.slider("Text font size", 14, 28, 18, step=2)

autorun_ocr_speech = st.sidebar.checkbox(
    "Automatically read extracted text", value=True
)

st.sidebar.info(
    "💡 Tip: For best results, use clear, well-lit images with horizontal text."
)

# ====== IMAGE UPLOAD & OCR ======
st.subheader("1️⃣ Upload Image for OCR")

uploaded_file = st.file_uploader(
    "Drag & drop or click to select an image",
    type=["png", "jpg", "jpeg", "bmp", "tiff"],
)

ocr_text = ""

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded image", use_column_width=True)

    with st.spinner("Running OCR..."):
        ocr_text = ocr_from_pil_image(image, lang=ocr_lang)

    if ocr_text.strip():
        st.success("Text extracted successfully!")
        if autorun_ocr_speech:
            speak_in_browser("Reading document from uploaded image. " + ocr_text)
    else:
        st.warning("No readable text detected in the image.")
        if autorun_ocr_speech:
            speak_in_browser("No readable text detected in the image.")

# ====== EXTRACTED TEXT + READ ALOUD BUTTON ======
st.subheader("2️⃣ Extracted Text")

text_area_style = f"font-size:{font_size}px; font-family:monospace;"

ocr_text = st.text_area(
    "OCR Output (you can edit this before reading):",
    value=ocr_text,
    height=220,
    key="ocr_output",
)

# Stats
if ocr_text:
    words = len(ocr_text.split())
    chars = len(ocr_text)
    st.caption(f"Words: {words} | Characters: {chars}")

# Button to read extracted text
if st.button("🔊 Read Extracted Text Aloud"):
    speak_in_browser(ocr_text)

# ====== TYPE & READ SECTION ======
st.subheader("3️⃣ Type & Read")

typed_text = st.text_area(
    "Type something here:",
    height=150,
    key="typed_input",
)

if st.button("🔊 Read Typed Text Aloud"):
    speak_in_browser("Reading typed text. " + typed_text)

st.markdown("---")
st.markdown("✅ Built with **Streamlit + Tesseract + Browser TTS**")
