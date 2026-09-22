import requests
from bs4 import BeautifulSoup
import json
import time
import re

def extract_99co_listing(soup):
    ld_json_tags = soup.find_all("script", type="application/ld+json")
    
    product = None
    breadcrumb = None
    
    for tag in ld_json_tags:
        try:
            parsed = json.loads(tag.string)
        except (json.JSONDecodeError, TypeError):
            continue
        
        if parsed.get("@type") == "Product":
            product = parsed
        elif parsed.get("@type") == "BreadcrumbList":
            breadcrumb = parsed
    
    if product is None:
        return None
    
    # ekstrak lokasi dari breadcrumb (biasanya: Jual > Tipe > Provinsi > Kota > Kecamatan)
    provinsi, kota, kecamatan = None, None, None
    if breadcrumb:
        items = breadcrumb.get("itemListElement", [])
        names = [item.get("name") for item in items]
        # posisi bisa bervariasi, ambil dari belakang biar lebih konsisten
        if len(names) >= 3:
            provinsi = names[2] if len(names) > 2 else None
            kota = names[3] if len(names) > 3 else None
            kecamatan = names[4] if len(names) > 4 else None
    
    # regex buat ekstrak spek dari description
    description = product.get("description", "")
    
    def extract_number(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE)
        return int(match.group(1)) if match else None
    
    luas_tanah = extract_number(r"LT\s*:?\s*(\d+)", description)
    luas_bangunan = extract_number(r"LB\s*:?\s*(\d+)", description)
    kamar_tidur = extract_number(r"KT\s*:?\s*(\d+)", description)
    kamar_mandi = extract_number(r"KM\s*:?\s*(\d+)", description)
    
    offers = product.get("offers", {})
    brand = product.get("brand", {})
    
    return {
        "url": product.get("url"),
        "nama_listing": product.get("name"),
        "deskripsi": description,
        "harga": offers.get("price"),
        "mata_uang": offers.get("priceCurrency"),
        "provinsi": provinsi,
        "kota": kota,
        "kecamatan": kecamatan,
        "luas_tanah_m2": luas_tanah,
        "luas_bangunan_m2": luas_bangunan,
        "kamar_tidur": kamar_tidur,
        "kamar_mandi": kamar_mandi,
        "nama_agen": brand.get("name"),
        "sku": product.get("sku")
    }

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def scrape_99co_detail(url):
    res = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")
    return extract_99co_listing(soup)


test_urls = [
    "https://www.99.co/id/properti/rumah-dijual-750jt-sambikerep-cp-1010236019",
    "https://www.99.co/id/properti/vila-dijual-280miliar-pererenan-cp-1013588608",
    "https://www.99.co/id/properti/apartemen-dijual-5miliar-lippo-karawaci-cp-1013696569",
    "https://www.99.co/id/properti/turun-harga-harus-terjual-bulan-ini-rumah-luas-462-meter-di-tengah-kota-solo-1011968172",
]

for url in test_urls:
    data = scrape_99co_detail(url)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("---")
    time.sleep(1)