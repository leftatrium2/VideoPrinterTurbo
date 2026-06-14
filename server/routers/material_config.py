from fastapi import APIRouter

router = APIRouter(
    prefix="/material_config",
    tags=["material配置模块"]
)


@router.get("/")
def get_material_config():
    return {"get_material_config": "get_material_config"}
