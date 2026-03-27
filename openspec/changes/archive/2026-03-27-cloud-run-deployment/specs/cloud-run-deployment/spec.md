## ADDED Requirements

### Requirement: Docker image build

The system SHALL package the Flask application, CLIP model, and all Python dependencies into a Docker image using the `Dockerfile` at the repository root.

The Dockerfile SHALL pre-download the CLIP ViT-B/32 model at build time so that cold starts do not trigger model downloads at request time.

#### Scenario: Successful image build

- **WHEN** `docker build` is executed against the repository root
- **THEN** a runnable image SHALL be produced with all dependencies installed and the CLIP model pre-downloaded

---

### Requirement: Continuous deployment via GitHub Actions

The system SHALL automatically build and deploy the Docker image to GCP Cloud Run on every push to the `main` branch via a GitHub Actions workflow at `.github/workflows/deploy.yml`.

The workflow SHALL push the image to GCP Artifact Registry (`asia-east1-docker.pkg.dev/loo-bah-png-project/loo-bah-png/`) and deploy to Cloud Run service `loo-bah-png` in region `asia-east1`.

GCP authentication SHALL use a Service Account JSON key stored in the GitHub repository secret `GCP_SA_KEY`.

#### Scenario: Push to main triggers deployment

- **WHEN** a commit is pushed to the `main` branch
- **THEN** GitHub Actions SHALL build the image, push it to Artifact Registry, and deploy the new revision to Cloud Run

---

### Requirement: Cloud Run service configuration

The Cloud Run service SHALL be configured with 4 GiB memory, 2 vCPUs, and `--no-cpu-throttling` to support CLIP model preloading at startup and background thread execution after request completion.

The three required environment variables (`ANTHROPIC_API_KEY`, `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`) SHALL be injected via Cloud Run environment variable configuration, not baked into the image.

#### Scenario: Container starts successfully

- **WHEN** a new Cloud Run revision is deployed
- **THEN** the container SHALL start, preload the CLIP model, and begin listening on port 8080 within the startup timeout

#### Scenario: Environment variables available at runtime

- **WHEN** the application reads `os.environ["ANTHROPIC_API_KEY"]`, `os.environ["LINE_CHANNEL_SECRET"]`, or `os.environ["LINE_CHANNEL_ACCESS_TOKEN"]`
- **THEN** the correct values SHALL be returned without error

---

### Requirement: CLIP model preloading at startup

The application SHALL call `clip_model.get_model()` at module load time in `app.py` so that the CLIP model is fully loaded before the first request is processed.

#### Scenario: First request after cold start does not wait for model load

- **WHEN** the container completes startup and receives its first request
- **THEN** the CLIP model SHALL already be loaded in memory and the request SHALL be processed without an additional model-loading delay
