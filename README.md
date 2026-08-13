# 505-capstone-ml — Prediction API

Purpose-built prediction API and training utilities for the 505 capstone project.

Overview
--------
`505-capstone-ml` provides a lightweight, production-minded HTTP API for model inference, plus training and model management utilities used during development and evaluation. The codebase separates application concerns (API, routing, schemas) from ML concerns (features, training, serialization) so components can be tested and deployed independently.

Key features
------------
- Clean FastAPI-based prediction endpoint for serving model inferences
- Reusable feature engineering pipeline in the `ml` package
- Training entrypoint that produces versioned artifacts under `saved_models/`
- Minimal external dependencies for easy deployment and reproducibility

Repository layout
---------------
- `app/` — HTTP application and route wiring (FastAPI)
  - `app/main.py` — application entrypoint
  - `app/api/router.py` — route registration
  - `app/api/endpoints/prediction.py` — prediction endpoint
- `ml/` — model and data logic
  - `ml/features.py` — feature transformations
  - `ml/train.py` — training script (CLI entrypoint)
  - `ml/model_loader.py` — serialization / deserialization helpers
- `schemas/` — request/response Pydantic schemas
- `services/` — inference wrapper and business logic
- `saved_models/` — serialized artifacts produced by training (metadata present)
- `requirements.txt` — runtime dependencies

Quick start (development)
-------------------------
1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run locally (development server):

```powershell
uvicorn app.main:app --reload --port 8000
```

The API root will be available at `http://localhost:8000/`.

API (inference)
---------------
POST `/api/prediction`

Accepts a JSON payload matching the Pydantic model in `schemas/prediction.py`. Example request:

```json
{
  "feature_1": 3.4,
  "feature_2": "category",
  "feature_3": 12
}
```

Example response:

```json
{
  "prediction": 0.72,
  "label": "positive",
  "confidence": 0.87
}
```

Training
--------
To train and produce a model artifact run:

```powershell
python -m ml.train
```

Inspect `ml/train.py` for dataset paths and hyperparameter configuration. Artifacts are written to `saved_models/` and loaded by `ml/model_loader.py`.

Deployment
----------
- For serverless (Vercel) review `api/index.py` and `vercel.json` for handler rules.
- For containerized deployments use Uvicorn/Gunicorn and run the `app.main` ASGI app.

Development notes
-----------------
- Keep feature engineering deterministic and covered by unit tests in `ml/features.py`.
- Add tests for `services/prediction.py` to validate inference behavior.
- Update `requirements.txt` when adding or upgrading dependencies.

Contributing
------------
1. Open an issue for non-trivial changes or feature requests.
2. Submit a pull request with a clear description and tests where appropriate.

Acknowledgements
----------------
This repository was created for the 505 capstone project (505-capstone-ml). If you want, I can add a small example client script, CI workflow, or a `Makefile` for common tasks.

