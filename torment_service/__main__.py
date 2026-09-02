"""Entry point for: python -m torment_service"""
import uvicorn

from .app import app, configure_app_public_runtime_from_host_environment

if __name__ == "__main__":
    # Host proof configuration is optional for legacy compatibility and is
    # deliberately not a backend-mode setting.  The read-only B5 resolver in
    # public_runtime remains the sole LEGACY/NATIVE/REFUSED authority.
    configure_app_public_runtime_from_host_environment()
    uvicorn.run(app, host="127.0.0.1", port=8787)
