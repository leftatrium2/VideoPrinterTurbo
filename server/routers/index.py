from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.database import database
from models.model import VptTask

router = APIRouter()


@router.get("/")
async def root(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(VptTask).where(VptTask.is_deleted == 0))
    tasks = result.scalars().all()
    if not tasks:
        return {"message": "No task found"}
    return tasks
