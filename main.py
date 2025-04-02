from fastapi import FastAPI
from models import Base
from apis import department, ehs,user, qa, gmo, maint_works
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(department.router)
app.include_router(user.router)
app.include_router(qa.router)
app.include_router(ehs.router)
app.include_router(gmo.router)
app.include_router(maint_works.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)