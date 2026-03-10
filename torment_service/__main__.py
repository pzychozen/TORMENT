"""Entry point for: python -m torment_service"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("torment_service.app:app", host="127.0.0.1", port=8787)
