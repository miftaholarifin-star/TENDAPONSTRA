# Catatan Teknis Lampiran HKI

## Identitas ciptaan

Nama program: TENDAPONSTRA

Judul: TENDAPONSTRA: Platform Sistem Pemantauan Mobilitas Berbasis Telemetri IoT LoRaWAN dan Real-Time Risk Classification untuk Manajemen Keselamatan Penyandang Disabilitas Netra

Versi: 1.0.0

Tahun: 2026

## Batas implementasi repositori

Repositori memuat engine klasifikasi risiko, validasi payload, basis data SQLite, REST API, dashboard simulasi, dan unit test. Integrasi perangkat fisik, gateway LoRaWAN, Antares, GPS, serta pengiriman notifikasi eksternal memerlukan konfigurasi dan kredensial operasional. Kredensial tidak boleh disimpan dalam repositori.

## Artefak orisinal yang direpresentasikan

1. Struktur modul pemantauan berbasis telemetri.
2. Pipeline validasi dan pemrosesan payload.
3. Logika klasifikasi risiko dengan mekanisme prioritas.
4. Struktur penyimpanan rekaman sensor dan kejadian risiko.
5. Endpoint API pemantauan.
6. Rancangan antarmuka dashboard.
7. Skenario pengujian fungsi inti.

## Ketertelusuran kebutuhan

| Kebutuhan lampiran | Implementasi repositori |
|---|---|
| Akuisisi dan validasi data | `backend/app/models.py`, `backend/app/risk_engine.py` |
| Risk Classification Engine | `backend/app/risk_engine.py` |
| Penyimpanan riwayat | `backend/app/database.py` |
| Dashboard pemantauan | `frontend/` |
| Early warning | Status DANGER disimpan sebagai `risk_events`; adapter kanal eksternal belum diaktifkan |
| Pengujian | `backend/tests/` |

## Catatan penting

Publikasi GitHub membuktikan keberadaan dan struktur program pada suatu versi. Publikasi tersebut tidak menggantikan dokumen pencatatan ciptaan, identitas pencipta, surat pengalihan hak, atau berkas lain yang dipersyaratkan DJKI.

