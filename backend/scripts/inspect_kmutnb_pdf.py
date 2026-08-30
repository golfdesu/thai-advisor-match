import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, io
import pypdf
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
pdf_url = 'https://admission.kmutnb.ac.th/sites/default/files/2025-08/dataforcallcuricert-bacn.pdf'

print(f"Downloading KMUTNB official curriculum catalog PDF: {pdf_url}")
r = requests.get(pdf_url, headers=headers, timeout=20, verify=False)
print(f"Status: {r.status_code}, Length: {len(r.content)} bytes")

pdf = pypdf.PdfReader(io.BytesIO(r.content))
print(f"Total Pages in PDF: {len(pdf.pages)}")

all_text = ""
for i, page in enumerate(pdf.pages):
    txt = page.extract_text()
    all_text += f"\n--- Page {i+1} ---\n" + txt

print("PDF text sample (first 1000 chars):")
print(all_text[:1000])

# Save raw text to file
with open('kmutnb_catalog_pdf.txt', 'w', encoding='utf-8') as f:
    f.write(all_text)
print("Saved raw text to kmutnb_catalog_pdf.txt")
