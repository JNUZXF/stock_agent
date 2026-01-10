# tests/integration/test_api/test_health.py
# 健康检查API集成测试

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthAPI:
    """健康检查API测试类"""
    
    async def test_health_check(self, test_client: AsyncClient):
        """测试健康检查端点"""
        response = await test_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert "dependencies" in data
    
    async def test_liveness(self, test_client: AsyncClient):
        """测试存活探针"""
        response = await test_client.get("/api/v1/health/liveness")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok"
    
    async def test_readiness(self, test_client: AsyncClient):
        """测试就绪探针"""
        response = await test_client.get("/api/v1/health/readiness")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
