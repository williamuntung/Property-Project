import requests
from bs4 import BeautifulSoup
import json
import time
import os
import logging
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ======================
# TAHAP 1: Ambil URL dari sitemap
# ======================

def get_urls_from_sitemap(sitemap_url):
    res = requests.get(sitemap_url, headers=headers, timeout=8)
    soup = BeautifulSoup(res.content, "xml")
    return [loc.text for loc in soup.find_all("loc")]


def get_all_property_urls(index_url, cache_file="C:/Project/Deep_Learning_Project/Project-Property/data/raw/all_property_urls.json"):
    if os.path.exists(cache_file):
        logging.info(f"Cache ditemukan, load dari {cache_file}")
        with open(cache_file, "r", encoding='utf-8') as f:
            return json.load(f)

    child_sitemaps = get_urls_from_sitemap(index_url)
    logging.info(f"Total sitemap anak: {len(child_sitemaps)}")

    all_property_urls = []
    try:
        for i, child_url in enumerate(child_sitemaps):
            try:
                urls = get_urls_from_sitemap(child_url)

                if not isinstance(urls, list) or len(urls) == 0:
                    logging.warning(f"Sitemap kosong/gak valid, di-skip: {child_url}")
                    time.sleep(1)
                    continue

                urls_valid = [u for u in urls if isinstance(u, str) and u.startswith("http")]

                if len(urls_valid) != len(urls):
                    logging.warning(f"Ada {len(urls) - len(urls_valid)} entry gak valid di {child_url}, entry itu di-skip")

                all_property_urls.extend(urls_valid)
                logging.info(f"[{i+1}/{len(child_sitemaps)}] {len(urls_valid)} listing valid (total: {len(all_property_urls)})")

            except Exception as e:
                logging.warning(f"Gagal fetch {child_url}: {e}")
            time.sleep(0.5)

    except KeyboardInterrupt:
        logging.warning("Dihentikan manual saat fetch sitemap. Menyimpan yang berhasil sejauh ini...")

    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(all_property_urls, f)
    logging.info(f"Semua URL tersimpan di {cache_file} ({len(all_property_urls)} URL)")

    return all_property_urls


# ======================
# TAHAP 2: Scrape detail listing (JSON-LD Product + Breadcrumb, khusus 99.co)
# ======================

def extract_number_flexible(patterns, text):
    """Coba beberapa pola regex berurutan, pakai yang pertama ketemu."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


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

    description = product.get("description", "")

    # --- lokasi dari breadcrumb ---
    provinsi, kota, kecamatan = None, None, None
    if breadcrumb:
        items = breadcrumb.get("itemListElement", [])
        names = [item.get("name") for item in items if item.get("name")]
        if len(names) > 2:
            provinsi = names[2]
        if len(names) > 3:
            kota = names[3]
        if len(names) > 4:
            kecamatan = names[4]

    # --- fallback lokasi dari teks deskripsi ---
    if provinsi is None:
        m = re.search(r"provinsi\s*:?\s*([A-Za-z\s]+?)(?:\n|$)", description, re.IGNORECASE)
        if m:
            provinsi = m.group(1).strip()

    if kota is None:
        m = re.search(r"kota\s*:?\s*([A-Za-z\s]+?)(?:\n|$)", description, re.IGNORECASE)
        if m:
            kota = m.group(1).strip()

    # --- luas tanah & bangunan ---
    luas_tanah = extract_number_flexible([
        r"LT\s*:?\s*(\d+)",
        r"luas\s*tanah\s*:?\s*(\d+)",
    ], description)

    luas_bangunan = extract_number_flexible([
        r"LB\s*:?\s*(\d+)",
        r"luas\s*bangunan\s*:?\s*(\d+)",
        r"(\d+)\s*sqm\s*floor\s*area",
    ], description)

    # --- kamar tidur & mandi ---
    kamar_tidur = extract_number_flexible([
        r"KT\s*:?\s*(\d+)",
        r"kamar\s*tidur\s*:?\s*(\d+)",
        r"(\d+)\s*kamar\s*tidur",
        r"(\d+)\s*bedroom",
        r"(\d+)\s*BR\b",
    ], description)

    kamar_mandi = extract_number_flexible([
        r"KM\s*:?\s*(\d+)",
        r"kamar\s*mandi\s*:?\s*(\d+)",
        r"(\d+)\s*kamar\s*mandi",
        r"(\d+)\s*bathroom",
    ], description)

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


def scrape_99co_detail(url):
    res = requests.get(url, headers=headers, timeout=8)
    soup = BeautifulSoup(res.text, "html.parser")
    return extract_99co_listing(soup)


# ======================
# MAIN
# ======================

def main():
    index_url = "https://www.99.co/id/sitemap-v1/sitemap-ldp-jual.xml"
    all_urls = get_all_property_urls(index_url)

    all_urls_unique = list(set(all_urls))
    print(f"Total URL (sebelum dedup): {len(all_urls)}")
    print(f"Total URL (setelah dedup): {len(all_urls_unique)}")

    urls_tersisa_all = all_urls_unique

    output_file = "C:/Project/Deep_Learning_Project/Project-Property/data/raw/properti_raw_v1.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    hasil = []
    urls_sudah_discrape = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            hasil = json.load(f)
        urls_sudah_discrape = {item["url"] for item in hasil}
        logging.info(f"Melanjutkan dari progress sebelumnya: {len(hasil)} listing sudah ada")

    urls_tersisa = [u for u in urls_tersisa_all if u not in urls_sudah_discrape]
    logging.info(f"Sisa yang perlu discrape: {len(urls_tersisa)}")

    try:
        for i, url in enumerate(urls_tersisa):
            try:
                data = scrape_99co_detail(url)

                if data is None:
                    logging.warning(f"[{i+1}/{len(urls_tersisa)}] Di-skip (no listing data): {url}")
                else:
                    hasil.append(data)
                    logging.info(f"[{i+1}/{len(urls_tersisa)}] Berhasil: {url}")

            except Exception as e:
                logging.warning(f"Gagal scrape {url}: {e}")

            if (i + 1) % 50 == 0:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(hasil, f, indent=2, ensure_ascii=False)
                logging.info(f"Checkpoint tersimpan ({len(hasil)} total listing)")

            time.sleep(1.5)

    except KeyboardInterrupt:
        logging.warning("Dihentikan manual (Ctrl+C). Menyimpan progress sebelum keluar...")

    finally:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(hasil, f, indent=2, ensure_ascii=False)
        logging.info(f"Selesai, total {len(hasil)} listing tersimpan.")


if __name__ == "__main__":
    main()