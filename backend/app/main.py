from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import api_v2
from .config import Settings, settings
from .db import get_db


def create_app(cfg: Settings = settings) -> FastAPI:
    app = FastAPI(title='CRM RAH VZLA API', version='0.3.0-dev')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in cfg.cors_origins.split(',') if origin.strip()],
        allow_credentials=False,
        allow_methods=['GET', 'POST', 'PATCH', 'DELETE'],
        allow_headers=['Content-Type', 'Authorization'],
    )

    @app.get('/health')
    def health(db: Session = Depends(get_db)):
        db.execute(text('SELECT 1'))
        return {'status': 'ok'}

    app.include_router(api_v2.router)

    if cfg.enable_v1_demo:
        if cfg.v1_demo_organizacion_id is None:
            raise RuntimeError('ENABLE_V1_DEMO=true requiere V1_DEMO_ORGANIZACION_ID (organización DEMO)')
        from . import api_v1

        app.include_router(api_v1.router)

    return app


app = create_app()
