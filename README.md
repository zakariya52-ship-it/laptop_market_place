# Production-Grade Laptop Price Predictor

An end-to-end laptop price prediction application with a decoupled offline machine
learning pipeline, a FastAPI inference service, and a React/Vite web interface.
The training workflow prepares the source data and produces a serialized
scikit-learn pipeline. The backend loads that existing artifact once at startup
and exposes validated prediction endpoints; the frontend communicates with the
backend over HTTP and does not contain model or training logic.

## Architecture

The project is organized around three runtime and ownership boundaries:

1. **Offline ML pipeline** — cleans the laptop dataset, engineers features, trains
   the configured regressor, evaluates it, and writes the model artifact and
   metrics report.
2. **FastAPI backend** — validates inference requests, loads
   `backend/artifacts/price_regressor.joblib` during application startup, and
   serves health and prediction endpoints.
3. **React/Vite frontend** — collects laptop specifications and sends prediction
   requests to the backend through `frontend/web/src/api.js`.

The model artifact contains the fitted preprocessing and regression stages, so
the inference service can apply the same transformations used during training.

## Tech Stack

### Machine learning and backend

The Python dependencies are declared in the repository-level
[`requirements.txt`](./requirements.txt):

- **Python 3.11** — the base runtime used by the backend Docker image.
- **FastAPI** and **Uvicorn** — HTTP API framework and ASGI server.
- **Pydantic** and **pydantic-settings** — request validation and application
  configuration.
- **CatBoost** — configured primary regression algorithm.
- **scikit-learn** — pipelines, preprocessing, train/test splitting, metrics,
  and the configured Random Forest fallback.
- **pandas** and **NumPy** — tabular data processing and numerical operations.
- **joblib** — model serialization and loading.
- **PyYAML** and **python-dotenv** — YAML model configuration and environment
  loading.
- **HTTPX** and **pytest** — backend/integration testing.
- **Streamlit** and **requests** — retained dependencies from the Python
  environment; the current browser UI is the React application under
  `frontend/web`.

### Frontend

The React/Vite dependencies are declared in
[`frontend/web/package.json`](./frontend/web/package.json):

- **React 18.3.1** and **React DOM 18.3.1** — UI runtime.
- **lucide-react 0.468.0** — interface icons.
- **Vite 6.0.5** — frontend development server and production bundler.
- **@vitejs/plugin-react 4.3.4** — Vite React integration.
- **Vitest 2.1.8** — frontend test runner.

The available npm scripts are:

```text
npm run dev    # Start the Vite development server
npm run build  # Create the production bundle in dist/
npm run test   # Run the Vitest suite once
```

### Infrastructure

- **Docker** packages the FastAPI service and its model/runtime dependencies.
- **Nginx Alpine** serves the compiled frontend assets.
- **Docker Compose** builds and runs the backend and frontend services on a
  shared `laptop-predictor` network.

## Project Structure

```text
laptop_price_predictor_project/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── health.py       # Health and model-readiness endpoint
│   │   │   │   └── predict.py      # Artifact loading and prediction endpoint
│   │   │   └── router.py           # Versioned API router
│   │   ├── core/config.py          # Backend settings and model path resolution
│   │   ├── schemas/                # Pydantic request/response models
│   │   └── main.py                 # FastAPI app and startup lifespan
│   ├── artifacts/
│   │   └── price_regressor.joblib  # Existing fitted prediction pipeline
│   └── Dockerfile
├── frontend/
│   ├── utils/                      # Existing Python client utilities
│   └── web/
│       ├── src/
│       │   ├── api.js              # Backend URL and HTTP prediction client
│       │   ├── knownValues.js      # Values accepted by the form/API
│       │   ├── main.jsx            # React application
│       │   └── styles.css
│       ├── package.json
│       ├── vite.config.js
│       └── Dockerfile
├── ml_pipeline/
│   ├── config/config.yaml          # Cleaning, feature, preprocessing, and model config
│   ├── data/
│   │   ├── raw/                   # laptop_scrap_data.csv
│   │   └── processed/             # cleaned_laptop_data.csv
│   ├── reports/
│   │   └── evaluation_metrics.json
│   └── src/
│       ├── data_loader.py         # Cleaning and processed-data generation
│       ├── feature_engineering.py # Transformers and ColumnTransformer
│       ├── train.py               # Training, evaluation, and joblib persistence
│       └── evaluate.py            # MAE/R² evaluation helpers
├── catboost_info/                 # CatBoost training information
├── tests/                         # Python unit and integration tests
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

Generated directories such as `frontend/web/node_modules/` and
`frontend/web/dist/` are development/build outputs and are not required in the
source tree when using Docker.

## Setup and Installation with Docker

### Prerequisites

- Docker Desktop with the Linux container engine running.
- Docker Compose v2 (`docker compose`).

From the repository root, build and start both services:

```powershell
docker compose up --build
```

The services are exposed at:

- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **OpenAPI schema:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

The backend image is built from the repository root so it can include the
`backend/`, `ml_pipeline/`, and `catboost_info/` directories required to
deserialize the existing joblib pipeline. The frontend image builds the Vite
bundle and serves it from Nginx on container port 80, mapped to host port 3000.

To stop the services:

```powershell
docker compose down
```

The frontend bundle is built with `VITE_BACKEND_URL=http://localhost:8000`,
which is the address available to a browser running on the host. The Compose
network is named `laptop-predictor` and connects both containers for service
isolation and backend-to-frontend infrastructure connectivity.

## Local Development

### Python environment

From the repository root in PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The backend settings have defaults for local inference, including port 8000 and
the model path `backend/artifacts/price_regressor.joblib`. Start the API from
the repository root so the package imports and relative artifact path resolve
consistently:

```powershell
.\venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

The application also reads the root `.env` file when present. The tracked
`.env.example` documents `BACKEND_URL`, `MODEL_PATH`, `HOST`, and `PORT` for
backend configuration. The offline ML modules additionally require these
pipeline paths when they are imported:

```powershell
$env:RAW_DATA_PATH = "ml_pipeline/data/raw/laptop_scrap_data.csv"
$env:PROCESSED_DATA_PATH = "ml_pipeline/data/processed/cleaned_laptop_data.csv"
$env:MODEL_PATH = "backend/artifacts/price_regressor.joblib"
$env:METRICS_REPORT_PATH = "ml_pipeline/reports/evaluation_metrics.json"
$env:CONFIG_YAML_PATH = "ml_pipeline/config/config.yaml"
```

### React/Vite frontend

In a second terminal, from the repository root:

```powershell
cd frontend\web
npm install
npm run dev
```

Vite will print the local development URL, normally
[http://localhost:5173](http://localhost:5173). The frontend API client defaults
to `http://localhost:8000`; to override it for a different backend:

```powershell
$env:VITE_BACKEND_URL = "http://localhost:8000"
npm run dev
```

Run the frontend tests with:

```powershell
npm run test
```

## API Endpoints

The FastAPI application mounts its versioned router at `/api/v1`.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Returns the API name, documentation path, and API prefix. |
| `GET` | `/api/v1/health` | Returns `{"status":"ok","model_loaded":true}` when the service is healthy and the artifact is loaded. |
| `POST` | `/api/v1/predict` | Validates a laptop specification and returns a predicted USD price. |
| `GET` | `/docs` | Interactive Swagger UI generated by FastAPI. |
| `GET` | `/openapi.json` | OpenAPI schema for the application. |

### Prediction request

`POST /api/v1/predict` accepts JSON with these fields:

```json
{
  "company": "lenovo",
  "type_name": "lenovo_thinkpad_t14_gen_5",
  "inches": 14,
  "screen_resolution": "1920_x_1200",
  "cpu": "intel_core_i7-1165g7",
  "gpu": "intel_iris_xe_graphics_g7_(96eu)",
  "os": "windows",
  "touch_screen": 0,
  "ips": 0,
  "x_res": 1920,
  "y_res": 1200,
  "ppi": 161,
  "dedicated_gpu": 0,
  "ram_gb": 16,
  "weight_kg": 1.35,
  "ssd": 512,
  "hhd": 0,
  "storage_type": "ssd_only",
  "total_storage_gb": 512,
  "storage_category": "standard_(512gb-1tb)"
}
```

Categorical values are normalized and checked against known values derived from
the training data. Numeric fields have bounds enforced by the Pydantic schema,
and `total_storage_gb` must equal `ssd + hhd`. A successful response has this
shape:

```json
{
  "predicted_price": 1249.99,
  "currency": "USD"
}
```

Invalid request payloads are returned as HTTP 400 responses with a descriptive
`detail` message. Prediction failures are returned as HTTP 500 responses, and
the service returns HTTP 503 if a request arrives before a model is available.

## Machine Learning Architecture

### Data and cleaning

The source dataset is
`ml_pipeline/data/raw/laptop_scrap_data.csv`. Running the data loader:

1. Parses RAM and storage values such as `16GB RAM`, `512GB`, and `1 TB`.
2. Converts numeric columns and normalizes categorical text to lowercase,
   underscore-separated values.
3. Removes index columns, rows without the `Price` target, duplicates, and
   excluded storage categories.
4. Applies configured winsorization features when a numeric column exceeds the
   configured outlier-rate threshold.
5. Writes `ml_pipeline/data/processed/cleaned_laptop_data.csv`.

### Feature engineering and preprocessing

The training pipeline creates derived features including GPU brand, CPU brand,
storage performance, premium-tier and AI-ready flags, and laptop series. It
then:

- Drops configured raw columns that should not reach the model.
- Fills missing numeric values with medians learned from the training data.
- Ensures all configured model columns exist.
- Standardizes numerical features with `StandardScaler`.
- One-hot encodes categorical features with unknown categories ignored.

### Training and artifact consumption

The configured target is `Price`. Training uses an 80/20 train/test split with
`random_state: 42` and the configured CatBoost regressor:

- 800 iterations
- learning rate `0.08`
- depth `6`
- RMSE loss
- CatBoost random seed `42`

If CatBoost cannot be initialized, the implementation is configured to fall
back to a Random Forest regressor with 300 estimators, maximum depth 12, and
random state 42. Training reports mean absolute error (MAE) and R², writes
`ml_pipeline/reports/evaluation_metrics.json`, and serializes the complete
pipeline with joblib.

The existing inference artifact is
`backend/artifacts/price_regressor.joblib`. FastAPI loads it once in the
application lifespan, normalizes the incoming request into the raw feature
schema, invokes the fitted pipeline, clamps negative predictions to zero, and
returns the price rounded to two decimal places. Training is never triggered by
the API or by a prediction request.

To run the offline workflow after setting the ML path variables shown above:

```powershell
.\venv\Scripts\Activate.ps1
python -m ml_pipeline.src.train
```

This command runs the data pipeline before fitting and persisting the model,
because `train.py` invokes `run_data_pipeline()` in its module entrypoint.

## Testing

Python tests are located under `tests/` and cover backend configuration,
schemas, routing, health and prediction behavior, model loading, pipeline data
loading, feature engineering, evaluation, training, and the frontend API
client utilities. Run them from the repository root:

```powershell
.\venv\Scripts\Activate.ps1
python -m pytest
```

The React/Vite tests are run separately from `frontend/web`:

```powershell
cd frontend\web
npm run test
```

## Configuration Notes

- Keep `.env` local; it is excluded by `.gitignore`.
- The current `.env.example` uses `backend/models/price_regressor.joblib`, but
  the artifact present in this workspace is
  `backend/artifacts/price_regressor.joblib`. Use the artifact path shown in
  the local-development commands when configuring this checkout.
- The ML pipeline's `ml_pipeline/src/config.py` requires
  `RAW_DATA_PATH`, `PROCESSED_DATA_PATH`, `MODEL_PATH`,
  `METRICS_REPORT_PATH`, and `CONFIG_YAML_PATH` at import time. The local
  commands above export those values explicitly. The current Compose files do
  not pass these five variables into the backend container, so a Docker
  deployment that starts the current artifact-loading path may require a
  Compose environment update before it can be considered production-ready.
- Do not replace or delete the existing serialized artifact unless intentionally
  retraining and validating the resulting model.
- Keep `backend/artifacts/price_regressor.joblib`,
  `ml_pipeline/config/config.yaml`, and the pipeline source available together:
  the backend provides compatibility aliases for the legacy serialized `src`
  module names used by the current artifact.
- The backend uses permissive CORS settings for the current application
  integration. Restrict `allow_origins` before deploying behind a public
  domain.