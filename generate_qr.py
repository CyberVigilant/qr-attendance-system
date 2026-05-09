"""
QR Attendance System — QR Code Generator
=========================================
Generates one QR code image per student.
Output: 'qrcodes/' folder with PNG files named by student ID.

Install:
  pip3 install qrcode pillow

Run:
  python3 generate_qr.py
"""

import qrcode
import os
from PIL import Image, ImageDraw, ImageFont

# ── STUDENT LIST ─────────────────────────────────────────────
# Format: ("STUDENT_ID", "Full Name")
# The QR code contains ONLY the student ID — not the name
STUDENTS = [
    ("STU001", "Student One"),
    ("STU002", "Student Two"),
    ("STU003", "Student Three"),
    # Add all students here...
]
# ─────────────────────────────────────────────────────────────

OUTPUT_DIR = "qrcodes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

for student_id, name in STUDENTS:
    # Generate QR code (contains ID only)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(student_id)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Add label below QR
    qr_w, qr_h = qr_img.size
    label_h = 70
    final = Image.new("RGB", (qr_w, qr_h + label_h), "white")
    final.paste(qr_img, (0, 0))
    draw = ImageDraw.Draw(final)

    try:
        font_id   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except:
        font_id   = ImageFont.load_default()
        font_name = font_id

    draw.text((qr_w // 2, qr_h + 10), student_id, fill="#000000", font=font_id,   anchor="mt")
    draw.text((qr_w // 2, qr_h + 35), name,       fill="#444444", font=font_name, anchor="mt")

    filename = f"{OUTPUT_DIR}/{student_id}.png"
    final.save(filename)
    print(f"✓ {student_id} — {name}")

print(f"\n✅ Done! {len(STUDENTS)} QR codes saved to /{OUTPUT_DIR}/")
