from fastapi import FastAPI
from app.routers.users import router as users_router
import uvicorn


app = FastAPI()

app.include_router(users_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)


