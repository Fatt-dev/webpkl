@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════╗
echo ║   CILACAP DALAM ANGKA — Setup dan Jalankan       ║
echo ╚══════════════════════════════════════════════════╝
echo.

:: Pindah ke direktori skrip ini
cd /d "%~dp0"

echo [1/3] Menginstall dependencies Python...
pip install flask flask-cors geopandas statsmodels pandas numpy shapely pyproj fiona
echo.

echo [2/3] Mengkonversi SHP ke GeoJSON...
python backend\shp_to_geojson.py
echo.

echo [3/3] Menjalankan server...
echo   Admin  : http://localhost:5000/admin/
echo   User   : http://localhost:5000/
echo   Tekan Ctrl+C untuk menghentikan
echo.
python backend\app.py
pause
