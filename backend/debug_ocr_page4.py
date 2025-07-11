import pdfplumber
import pytesseract
from PIL import Image
import os

def ocr_page4_lines(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"❌ No existe el archivo: {pdf_path}")
        return
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) < 4:
            print("❌ El PDF no tiene al menos 4 páginas.")
            return
        page = pdf.pages[3]  # Página 4 (índice 3)
        print("\n=== OCR de la página 4 (líneas) ===\n")
        img = page.to_image(resolution=300)
        pil_img = img.original
        text = pytesseract.image_to_string(pil_img, lang="spa")
        lines = text.split('\n')
        for i, line in enumerate(lines):
            print(f"{i+1:02d}: {line}")
        print("\n=== FIN OCR página 4 ===\n")

if __name__ == "__main__":
    ocr_page4_lines("uploaded_pdfs/2025-05-16_Estado_de_cuenta.pdf") 