# Property-Project

**Catatan etika scraping:** proyek ini murni untuk tujuan edukasi/portofolio pribadi, 
bukan untuk redistribusi data atau tujuan komersial. Scraping dilakukan dengan 
menghormati `robots.txt` dan menerapkan rate limiting.

## Deskripsi

Proyek end-to-end data science yang membangun dataset properti dari nol lewat web scraping, 
lalu menerapkan pendekatan **descriptive → predictive → prescriptive analytics** untuk 
menghasilkan rekomendasi keputusan pembelian properti, bukan sekadar prediksi harga.

## Ringkasan

Alih-alih menggunakan dataset siap pakai, proyek ini membangun data sendiri dari listing 
properti publik di Rumah123, mencakup kota Bandung, Cimahi, Semarang, dan Surabaya. Tujuannya 
mendemonstrasikan keseluruhan pipeline data science: mulai dari pengumpulan data mentah 
yang tidak terstruktur, hingga model yang bisa memberi rekomendasi actionable.

**Alur analisis:**
1. **Descriptive** — memahami pola harga & karakteristik pasar properti
2. **Predictive** — membangun model estimasi harga berdasarkan spesifikasi properti
3. **Prescriptive** — memberi rekomendasi (mis. deteksi listing under/overpriced, 
   rekomendasi properti sesuai budget & kriteria)

## Sumber Data

Data diambil dari listing publik [Rumah123](https://www.rumah123.com) melalui sitemap resmi 
mereka, mengikuti aturan `robots.txt` situs (hanya mengakses halaman yang diizinkan, 
menghindari parameter query yang di-*disallow*, dan menerapkan jeda antar request).

## File Structure:

Property-Project
|- scrapper
   |- scrapper.py
|- data
   |- raw
      |- versioning raw data
   |- processed
      |- clean data
|- notebook
   |- cleaning
   |- descriptive
   |- predictive
   |- prescriptive

| Atribut | Keterangan |
|---|---|
| Sumber | Rumah123.com (sitemap XML resmi) |
| Kota (keywords) | Bandung, Cimahi, Semarang, Surabaya |

## Tech Stack (Library)



## Hasil Utama


## Batasan & Pengembangan Lanjutan


## Lisensi

