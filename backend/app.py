"""
app.py — Flask Backend Server
Cilacap Dalam Angka — Sistem Informasi Statistik Kabupaten Cilacap
Jalankan: python app.py
Server tersedia di: http://localhost:5000
"""
import os
import json
import uuid
from flask import Flask, send_from_directory, request, jsonify, abort, session, redirect, url_for, render_template_string
from flask_cors import CORS

# ─────────────────────────────────────────────
# Konfigurasi Path
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # backend/
PROJECT_DIR = os.path.dirname(BASE_DIR)                  # web_pkl/
DATA_DIR = os.path.join(BASE_DIR, 'data')
ADMIN_DIR = os.path.join(PROJECT_DIR, 'admin')
USER_DIR = os.path.join(PROJECT_DIR, 'user')
GEOJSON_PATH = os.path.join(USER_DIR, 'cilacap.geojson')

# ─────────────────────────────────────────────
# Inisialisasi Flask
# ─────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  # Izinkan semua origin (untuk development)

# Secret key untuk enkripsi session cookie
app.secret_key = os.environ.get('SECRET_KEY', 'cda-bps-cilacap-secret-2024-xk9')

# Password admin dari environment variable Railway
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')


# ─────────────────────────────────────────────
# Utility JSON
# ─────────────────────────────────────────────
def read_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {} if filename != 'runtun_waktu.json' else []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# Halaman Statis (Admin & User)
# ─────────────────────────────────────────────
@app.route('/')
@app.route('/user/')
def user_page():
    return send_from_directory(USER_DIR, 'index.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect('/admin')
        else:
            return redirect('/admin/login?error=1')
    # Kalau sudah login, langsung ke admin
    if session.get('admin_logged_in'):
        return redirect('/admin')
    return send_from_directory(ADMIN_DIR, 'login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')


@app.route('/admin/')
@app.route('/admin')
def admin_page():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    return send_from_directory(ADMIN_DIR, 'index.html')


@app.route('/admin/<path:filename>')
def admin_static(filename):
    return send_from_directory(ADMIN_DIR, filename)


@app.route('/user/<path:filename>')
def user_static(filename):
    return send_from_directory(USER_DIR, filename)


@app.route('/logo_bps/<path:filename>')
def logo_bps_static(filename):
    return send_from_directory(os.path.join(PROJECT_DIR, 'logo_bps'), filename)


@app.route('/wallpaper/<path:filename>')
def wallpaper_static(filename):
    return send_from_directory(os.path.join(PROJECT_DIR, 'wallpaper'), filename)


# ─────────────────────────────────────────────
# API: Data Indikator Utama
# ─────────────────────────────────────────────
@app.route('/api/indikator', methods=['GET'])
def get_indikator():
    tahun = request.args.get('tahun')
    data = read_json('indikator.json')
    if tahun:
        return jsonify(data.get(str(tahun), {}))
    return jsonify(data)


@app.route('/api/indikator', methods=['POST'])
def save_indikator():
    body = request.get_json(force=True)
    tahun = str(body.pop('tahun', '')).strip()
    if not tahun:
        return jsonify({'error': 'Tahun wajib diisi'}), 400
    data = read_json('indikator.json')
    data[tahun] = body
    write_json('indikator.json', data)
    return jsonify({'success': True, 'tahun': tahun})


# ─────────────────────────────────────────────
# API: Data Runtun Waktu
# ─────────────────────────────────────────────
@app.route('/api/runtun', methods=['GET'])
def get_runtun():
    data = read_json('runtun_waktu.json')
    if not isinstance(data, list):
        data = []
    # Opsional: filter berdasarkan nama
    nama = request.args.get('nama')
    if nama:
        data = [d for d in data if d.get('nama', '').lower() == nama.lower()]
    return jsonify(data)


@app.route('/api/runtun', methods=['POST'])
def add_runtun():
    body = request.get_json(force=True)
    if not body.get('nama') or body.get('tahun') is None or body.get('nilai') is None:
        return jsonify({'error': 'nama, tahun, dan nilai wajib diisi'}), 400
    data = read_json('runtun_waktu.json')
    if not isinstance(data, list):
        data = []
    body['id'] = str(uuid.uuid4())
    body['nama'] = str(body['nama']).strip()
    body['tahun'] = str(body['tahun']).strip()
    body['nilai'] = float(body['nilai'])
    data.append(body)
    write_json('runtun_waktu.json', data)
    return jsonify(body), 201


@app.route('/api/runtun/<item_id>', methods=['PUT'])
def update_runtun(item_id):
    body = request.get_json(force=True)
    data = read_json('runtun_waktu.json')
    if not isinstance(data, list):
        return jsonify({'error': 'Data tidak valid'}), 500
    for i, item in enumerate(data):
        if item.get('id') == item_id:
            updated = {**item}
            if 'nama' in body:
                updated['nama'] = str(body['nama']).strip()
            if 'tahun' in body:
                updated['tahun'] = str(body['tahun']).strip()
            if 'nilai' in body:
                updated['nilai'] = float(body['nilai'])
            data[i] = updated
            write_json('runtun_waktu.json', data)
            return jsonify({'success': True, 'data': updated})
    return jsonify({'error': 'Data tidak ditemukan'}), 404


@app.route('/api/runtun/<item_id>', methods=['DELETE'])
def delete_runtun(item_id):
    data = read_json('runtun_waktu.json')
    if not isinstance(data, list):
        return jsonify({'error': 'Data tidak valid'}), 500
    original_len = len(data)
    data = [item for item in data if item.get('id') != item_id]
    if len(data) == original_len:
        return jsonify({'error': 'Data tidak ditemukan'}), 404
    write_json('runtun_waktu.json', data)
    return jsonify({'success': True})


# ─────────────────────────────────────────────
# API: Data Kecamatan
# ─────────────────────────────────────────────
@app.route('/api/kecamatan', methods=['GET'])
def get_kecamatan():
    tahun = request.args.get('tahun')
    tema = request.args.get('tema')
    data = read_json('kecamatan.json')
    if tahun and tema:
        return jsonify(data.get(str(tahun), {}).get(tema, {}))
    elif tahun:
        return jsonify(data.get(str(tahun), {}))
    return jsonify(data)


@app.route('/api/kecamatan/meta', methods=['GET'])
def get_kecamatan_meta():
    """Mengembalikan daftar {tahun: [tema1, tema2, ...]} yang tersedia."""
    data = read_json('kecamatan.json')
    meta = {}
    for tahun, temas in data.items():
        meta[tahun] = list(temas.keys())
    return jsonify(meta)


@app.route('/api/kecamatan', methods=['POST'])
def save_kecamatan():
    body = request.get_json(force=True)
    tahun = str(body.get('tahun', '')).strip()
    tema = str(body.get('tema', '')).strip()
    variabel = str(body.get('variabel', '')).strip()
    nilai = body.get('nilai', [])
    if not tahun or not tema or not variabel:
        return jsonify({'error': 'tahun, tema, dan variabel wajib diisi'}), 400
    if not isinstance(nilai, list) or len(nilai) != 24:
        return jsonify({'error': 'nilai harus berupa array dengan tepat 24 elemen'}), 400
    data = read_json('kecamatan.json')
    if tahun not in data:
        data[tahun] = {}
    if tema not in data[tahun]:
        data[tahun][tema] = {}
    data[tahun][tema][variabel] = nilai
    write_json('kecamatan.json', data)
    return jsonify({'success': True})


@app.route('/api/kecamatan', methods=['DELETE'])
def delete_kecamatan():
    tahun = request.args.get('tahun')
    tema = request.args.get('tema')
    variabel = request.args.get('variabel')
    data = read_json('kecamatan.json')
    try:
        if variabel:
            del data[tahun][tema][variabel]
        elif tema:
            del data[tahun][tema]
        elif tahun:
            del data[tahun]
        write_json('kecamatan.json', data)
        return jsonify({'success': True})
    except KeyError:
        return jsonify({'error': 'Data tidak ditemukan'}), 404


# ─────────────────────────────────────────────
# API: GeoJSON Kecamatan Cilacap
# ─────────────────────────────────────────────
@app.route('/api/geojson', methods=['GET'])
def get_geojson():
    if not os.path.exists(GEOJSON_PATH):
        return jsonify({
            'error': 'GeoJSON belum tersedia. Jalankan: python backend/shp_to_geojson.py'
        }), 404
    with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)


# ─────────────────────────────────────────────
# API: Regresi Berganda
# ─────────────────────────────────────────────
@app.route('/api/regresi', methods=['POST'])
def run_regresi():
    from regression import run_regression
    body = request.get_json(force=True)
    kecamatan_data = read_json('kecamatan.json')
    result = run_regression(body, kecamatan_data)
    return jsonify(result)


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────
@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok', 'message': 'Cilacap Dalam Angka API berjalan'})


# ─────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint tidak ditemukan'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': f'Kesalahan server: {str(e)}'}), 500


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)


