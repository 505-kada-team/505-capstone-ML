# Ringkasan Perubahan (untuk deploy ke Vercel)

Tujuan, flow, dan skema API **tidak berubah**:
- Endpoint `POST /predict-assortment` tetap menerima `PlanRequest` dan
  mengembalikan `List[MenuRecommendation]` — persis sama.
- Fitur yang dipakai model tetap 5 kolom yang sama, dengan nilai yang
  dihitung dengan cara yang sama persis (`plan_duration`, `start_month`,
  `is_promo`, `menu_selling_price`, `ingredient_count`).
 - Model diganti menjadi `RandomForestRegressor` (lebih ringan untuk
   inference) dengan hyperparameter yang sesuai.
- Training tetap ambil data dari MongoDB collection `productionplans` /
  `menus` dengan query & logika yang sama.

Yang diubah hanyalah **bagaimana dependency di-package**, supaya ukuran
function di Vercel jauh lebih kecil:

## 1. Pisah "training" vs "inference"
`train.py` (butuh MongoDB, pandas, scikit-learn) **tidak pernah didorong ke
Vercel**. Yang di-deploy hanya kode inferensi (baca request → hitung fitur
→ load model → prediksi). Ini paling besar dampaknya karena `pymongo`,
`pandas`, `scikit-learn`, dan `joblib` sama sekali tidak dibutuhkan saat
serving prediksi.

- `requirements.txt` → dependency untuk **deploy** (ringan):
  `fastapi`, `pydantic`, `pydantic-settings`, `scikit-learn`, `joblib`, `numpy`.
- `requirements-train.txt` → dependency untuk **training lokal/CI** saja
  (`-r requirements.txt` + `pandas`, `scikit-learn`, `pymongo`, `joblib`).

## 2. Model disimpan sebagai joblib-pickled scikit-learn estimator
Sekarang model dilatih sebagai `RandomForestRegressor` dan disimpan
sebagai `model.joblib` menggunakan `joblib.dump()`. Pada saat deploy,
service memuat kembali model dengan `joblib.load()` sehingga `scikit-learn`
dan `joblib` harus tersedia di runtime.

## 3. Hilangkan pandas dari jalur inferensi
`features.py` sebelumnya mengembalikan `pandas.DataFrame`. Sekarang
`build_feature_rows()` mengembalikan `list[list[float]]` biasa dengan
urutan kolom yang sama (`FEATURE_COLUMNS`), lalu langsung dipakai oleh
estimator scikit-learn di `services/prediction.py` melalui `model.predict(rows)`.
Nilai fitur dan urutannya sama persis — hanya
tipe datanya yang lebih ringan (pandas adalah salah satu dependency
terberat, puluhan MB, dan tidak dibutuhkan hanya untuk membangun 5 angka
per menu).

`pymongo`/`bson` juga sudah tidak pernah dipakai di jalur inferensi —
memang sejak awal hanya dipakai `train.py`.

## 4. File baru untuk menjalankan di Vercel
- `app/main.py` — merakit `FastAPI()` + `api_router` menjadi satu objek
  `app` (sebelumnya file ini belum ada di kode yang diberikan, tapi
  dirujuk oleh modul lain via `app.core...`, `app.ml...`, dst).
- `api/index.py` — entrypoint yang dibaca Vercel Python runtime
  (`@vercel/python`), cukup meng-import `app` dari `app.main`.
- `vercel.json` — build config: build `api/index.py` dan arahkan semua
  route ke situ.
- `.vercelignore` — memastikan `train.py`, `requirements-train.txt`, dan
  model lama `.joblib` tidak ikut ter-bundle ke function.

## Cara pakai

1. **Training tetap dilakukan lokal / CI**, bukan di Vercel:
   ```bash
   pip install -r requirements-train.txt
   python -m app.ml.train
   ```
  Ini akan menghasilkan `saved_models/model.joblib` dan
  `saved_models/metadata.json`.

2. Commit `saved_models/model.joblib` (+ `metadata.json`) ke repo yang akan
  di-deploy.

3. Deploy:
   ```bash
   vercel deploy
   ```
   Vercel akan otomatis mendeteksi `api/index.py` sebagai ASGI app
   (FastAPI) berkat `vercel.json`.

4. Endpoint yang aktif tetap sama: `POST /predict-assortment`.

## Catatan ukuran package

- Per Juli 2026, batas *unzipped* untuk Python Serverless Function di
  Vercel adalah **500 MB** (naik dari 250 MB sebelumnya), dengan opsi
  "large Functions" hingga 5 GB via Fluid Compute jika suatu saat masih
  kurang. Dengan hanya `fastapi + pydantic + scikit-learn + joblib + numpy`
  (tanpa `pandas`/`pymongo`), ukuran bundle akan jauh di bawah limit ini.

- Jika suatu saat ingin lebih ringan lagi (opsional): estimator tree-based
  (seperti RandomForest) dengan 5 fitur dapat diekspor menjadi kode Python
  murni (mis. menggunakan `m2cgen`) sehingga deploy tidak membutuhkan
  `scikit-learn`. Representasi hasil generate adalah kode `.py` yang
  mereplikasi logic keputusan pohon; hasil prediksi tetap identik.
