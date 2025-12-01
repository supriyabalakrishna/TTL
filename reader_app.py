import cv2
import pytesseract
import pyttsx3
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
import os

# ===== Tesseract Path (Windows) =====
# Uncomment if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

engine = pyttsx3.init()
engine.setProperty("rate", 170)

# ===== OCR Speed Boost Functions =====
def preprocess_image(pil_img):
    gray = pil_img.convert("L")
    img_np = np.array(gray)
    _, thresh = cv2.threshold(img_np, 150, 255, cv2.THRESH_BINARY)
    return Image.fromarray(thresh)

def ocr_from_pil_image(pil_img, lang="eng"):
    MAX_SIZE = 1200
    w, h = pil_img.size
    if max(w, h) > MAX_SIZE:
        scale = MAX_SIZE / max(w, h)
        pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    pil_img = preprocess_image(pil_img)
    config = r"--oem 1 --psm 6"
    text = pytesseract.image_to_string(pil_img, lang=lang, config=config)
    return text

# ===== SPEAK FUNCTION =====
def speak(text):
    text = text.strip()
    if not text:
        return
    try:
        engine.stop()
    except:
        pass
    engine.say(text)
    engine.runAndWait()

# ===== GUI FUNCTIONS =====
def open_image():
    file_path = filedialog.askopenfilename(
        filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff")]
    )

    if not file_path:
        return

    img = Image.open(file_path).convert("RGB")
    display_img(img)

    extracted = ocr_from_pil_image(img)

    output_text.delete("1.0", END)
    output_text.insert(END, extracted)

    speak("Reading extracted text. " + extracted)

def display_img(pil_image):
    pil_image = pil_image.resize((350, 350))
    tk_image = ImageTk.PhotoImage(pil_image)
    image_label.config(image=tk_image)
    image_label.image = tk_image

def read_typed():
    txt = input_text.get("1.0", END)
    speak("Reading typed text. " + txt)

def capture_from_camera():
    speak("Opening camera. Press space to capture, escape to cancel.")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        speak("Camera error.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Camera - Press SPACE to capture", frame)
        key = cv2.waitKey(1)

        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)

            display_img(pil_img)
            text = ocr_from_pil_image(pil_img)

            output_text.delete("1.0", END)
            output_text.insert(END, text)
            speak("Reading captured text. " + text)
            break

    cap.release()
    cv2.destroyAllWindows()

# ===== GUI SETUP =====
root = Tk()
root.title("Document Reader for Visually Impaired")
root.geometry("900x650")
root.config(bg="white")

Label(root, text="Accessible Document Reader", font=("Arial", 20, "bold"), bg="white").pack(pady=10)

# === Image Preview ===
image_label = Label(root, bg="white")
image_label.pack(pady=10)

# === Buttons ===
btn_frame = Frame(root, bg="white")
btn_frame.pack(pady=10)

Button(btn_frame, text="Upload Image", font=("Arial", 12), command=open_image).grid(row=0, column=0, padx=10)
Button(btn_frame, text="Capture from Camera", font=("Arial", 12), command=capture_from_camera).grid(row=0, column=1, padx=10)

# === OCR Output ===
Label(root, text="Extracted Text:", font=("Arial", 14), bg="white").pack()
output_text = Text(root, height=8, width=80, font=("Arial", 12))
output_text.pack(pady=5)

# === Type & Read ===
Label(root, text="Type something to read aloud:", font=("Arial", 14), bg="white").pack()
input_text = Text(root, height=5, width=80, font=("Arial", 12))
input_text.pack(pady=5)
Button(root, text="Read Typed Text", font=("Arial", 12), command=read_typed).pack(pady=8)

root.mainloop()
