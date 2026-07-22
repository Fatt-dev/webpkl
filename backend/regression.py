"""
regression.py
Modul analisis regresi linier berganda menggunakan statsmodels OLS.
"""
import numpy as np
import statsmodels.api as sm
import pandas as pd

KECAMATAN_NAMES = [
    "Dayeuhluhur", "Wanareja", "Majenang", "Cimanggu", "Karangpucung",
    "Cipari", "Sidareja", "Kedungreja", "Patimuan", "Gandrungmangu",
    "Bantarsari", "Kawunganten", "Kampung Laut", "Jeruklegi", "Kesugihan",
    "Adipala", "Maos", "Sampang", "Kroya", "Binangun",
    "Nusawungu", "Cilacap Selatan", "Cilacap Tengah", "Cilacap Utara"
]


def get_values(kecamatan_data, tahun, tema, variabel):
    """Ambil array nilai 24 kecamatan dari nested JSON."""
    try:
        vals = kecamatan_data[str(tahun)][tema][variabel]
        result = []
        for v in vals:
            if v is None or v == "" or v == "-":
                result.append(None)
            else:
                try:
                    result.append(float(v))
                except (ValueError, TypeError):
                    result.append(None)
        # Pastikan panjangnya 24
        while len(result) < 24:
            result.append(None)
        return result[:24]
    except (KeyError, TypeError):
        return [None] * 24


def build_equation(intercept, koef_list, x_names):
    """Bangun string persamaan regresi."""
    parts = [f"{intercept:.4f}"]
    for koef, name in zip(koef_list, x_names):
        sign = "+" if koef >= 0 else "-"
        parts.append(f" {sign} {abs(koef):.4f}·{name}")
    return "Ŷ = " + "".join(parts)


def run_regression(params, kecamatan_data):
    """
    params = {
        'y': {'tahun': '2025', 'tema': 'Pertanian', 'variabel': 'Produksi Padi'},
        'x': [
            {'tahun': '2025', 'tema': 'Pertanian', 'variabel': 'Luas Tanam'},
            ...
        ]
    }
    """
    y_info = params.get('y', {})
    x_info_list = params.get('x', [])

    if not y_info or not x_info_list:
        return {'error': 'Parameter y dan x wajib diisi.'}

    # Kumpulkan data Y
    y_vals = get_values(kecamatan_data, y_info['tahun'], y_info['tema'], y_info['variabel'])

    # Kumpulkan data X
    x_vals_list = []
    x_names = []
    for xi in x_info_list:
        vals = get_values(kecamatan_data, xi['tahun'], xi['tema'], xi['variabel'])
        x_vals_list.append(vals)
        x_names.append(xi['variabel'])

    # Bangun DataFrame
    df = pd.DataFrame({'Y': y_vals, 'kecamatan': KECAMATAN_NAMES})
    for i, (xv, xn) in enumerate(zip(x_vals_list, x_names)):
        df[f'X{i+1}'] = xv

    # Hapus baris dengan nilai None/NaN
    df_clean = df.dropna()

    if len(df_clean) < len(x_info_list) + 2:
        return {
            'error': f'Data valid tidak cukup ({len(df_clean)} obs). '
                     f'Minimal {len(x_info_list) + 2} pengamatan diperlukan.'
        }

    Y = df_clean['Y'].values
    X_cols = [f'X{i+1}' for i in range(len(x_info_list))]
    X = df_clean[X_cols].values
    X_const = sm.add_constant(X, has_constant='add')

    try:
        model = sm.OLS(Y, X_const).fit()
    except Exception as e:
        return {'error': f'Gagal menghitung regresi: {str(e)}'}

    y_pred = model.predict(X_const)
    residuals = Y - y_pred
    rmse = float(np.sqrt(np.mean(residuals ** 2)))

    # Koefisien
    param_names = ['Intercept'] + x_names
    koefisien = []
    for i, name in enumerate(param_names):
        koefisien.append({
            'variabel': name,
            'koefisien': round(float(model.params[i]), 4),
            'std_error': round(float(model.bse[i]), 4),
            't_stat': round(float(model.tvalues[i]), 4),
            'p_value': round(float(model.pvalues[i]), 4),
            'signif': _sig_stars(float(model.pvalues[i]))
        })

    # Scatter data aktual vs prediksi
    scatter = []
    for j, (_, row) in enumerate(df_clean.iterrows()):
        scatter.append({
            'kecamatan': row['kecamatan'],
            'aktual': round(float(row['Y']), 4),
            'prediksi': round(float(y_pred[j]), 4)
        })

    persamaan = build_equation(
        model.params[0],
        model.params[1:],
        x_names
    )

    return {
        'r2': round(float(model.rsquared), 4),
        'adj_r2': round(float(model.rsquared_adj), 4),
        'rmse': round(rmse, 4),
        'prob_f': round(float(model.f_pvalue), 6),
        'f_stat': round(float(model.fvalue), 4),
        'n_obs': int(model.nobs),
        'koefisien': koefisien,
        'scatter': scatter,
        'persamaan': persamaan,
        'y_label': y_info['variabel']
    }


def _sig_stars(p):
    if p < 0.001:
        return '***'
    elif p < 0.01:
        return '**'
    elif p < 0.05:
        return '*'
    elif p < 0.1:
        return '.'
    return ''
