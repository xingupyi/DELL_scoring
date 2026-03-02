from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .db import get_db, init_db
from .schemas import ScoreRequest, ScoreResponse
from .services.scoring import score_message


app = FastAPI(title="Distress Scoring MVP")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.post("/score", response_model=ScoreResponse)
async def score_endpoint(payload: ScoreRequest, db: Session = Depends(get_db)) -> ScoreResponse:
    try:
        return await score_message(payload, db)
    except Exception as exc:
        # The scoring service will raise HTTPException for known error cases (e.g. 502).
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(status_code=500, detail="Internal server error") from exc


__all__ = ["app"]

