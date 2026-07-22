"""
shp_to_geojson.py
Konversi CilacapFix.shp → cilacap.geojson untuk dipakai Leaflet.js
Jalankan sekali: python shp_to_geojson.py
"""
import os
import json
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

SHP_PATH = os.path.join(PROJECT_DIR, 'Cilacap dalam angka', 'file_shp', 'CilacapFix.shp')
OUTPUT_PATH = os.path.join(PROJECT_DIR, 'user', 'cilacap.geojson')

# Kemungkinan nama kolom kecamatan dari DBF
POSSIBLE_NAME_COLS = [
    'KECAMATAN', 'kecamatan', 'WADMKC', 'NAMOBJ', 'NAMA', 'nama',
    'NAME', 'name', 'KEC', 'kec', 'NM_KEC', 'nm_kec', 'KECAMATAN_'
]


def find_name_column(columns):
    """Deteksi otomatis kolom nama kecamatan."""
    for col in POSSIBLE_NAME_COLS:
        if col in columns:
            return col
    # Fallback: cari kolom yang mengandung 'kec' atau 'nam'
    for col in columns:
        if 'kec' in col.lower() or 'nam' in col.lower():
            return col
    return columns[0] if columns else None


def convert():
    try:
        import geopandas as gpd
    except ImportError:
        print("ERROR: geopandas belum diinstal.")
        print("Jalankan: pip install geopandas")
        sys.exit(1)

    if not os.path.exists(SHP_PATH):
        print(f"ERROR: File SHP tidak ditemukan di:\n  {SHP_PATH}")
        sys.exit(1)

    print(f"Membaca SHP dari: {SHP_PATH}")
    gdf = gpd.read_file(SHP_PATH)

    print(f"\nTotal fitur: {len(gdf)}")
    print(f"Kolom yang tersedia: {list(gdf.columns)}")
    print(f"CRS asli: {gdf.crs}")
    print("\nSampel data:")
    print(gdf.drop(columns='geometry').head())

    # Deteksi nama kolom kecamatan
    non_geom_cols = [c for c in gdf.columns if c != 'geometry']
    name_col = find_name_column(non_geom_cols)
    print(f"\nKolom nama kecamatan terdeteksi: '{name_col}'")

    # Konversi ke WGS84 (EPSG:4326) agar Leaflet.js bisa membacanya
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        print("Mengkonversi proyeksi ke WGS84 (EPSG:4326)...")
        gdf = gdf.to_crs(epsg=4326)

    # Tambahkan properti standar NAMA_KECAMATAN
    if name_col:
        gdf['NAMA_KECAMATAN'] = gdf[name_col].astype(str).str.strip().str.title()

    # Tulis GeoJSON
    gdf.to_file(OUTPUT_PATH, driver='GeoJSON')
    print(f"\nGeoJSON berhasil disimpan ke:\n  {OUTPUT_PATH}")

    # Tampilkan nama-nama kecamatan yang terdeteksi
    if name_col:
        print("\nDaftar nama kecamatan dalam GeoJSON:")
        for i, nama in enumerate(sorted(gdf['NAMA_KECAMATAN'].tolist()), 1):
            print(f"  {i:2d}. {nama}")


if __name__ == '__main__':
    convert()
