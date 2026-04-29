from fastapi import APIRouter

from app.api.routes import analysis, auth, dashboard, fire, hotspots, imports, sync, users, weather


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(imports.router, prefix="/import", tags=["数据导入"])
api_router.include_router(fire.router, prefix="/fire", tags=["火点数据"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["数据分析"])
api_router.include_router(weather.router, prefix="/weather", tags=["天气服务"])
api_router.include_router(hotspots.router, prefix="/hotspots", tags=["热点区域"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["数据大屏"])
api_router.include_router(sync.router, prefix="/sync", tags=["数据同步"])
