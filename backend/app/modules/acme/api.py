# app/modules/acme/api.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from app.core.pojo.response import BaseResponse
from app.core.db.database import get_engine
from app.modules.acme import schemas
from app.modules.acme.services import (
    DNSAuthService, ApplicationService,
    CertificateService, ExecutionService
)

router = APIRouter(prefix="/ssl", tags=["SSL证书管理"])


# ========== DNS授权管理 ==========

@router.post("/dns-auth", response_model=BaseResponse[schemas.DNSAuthRead])
async def create_dns_auth(
        data: schemas.DNSAuthCreate,
        engine=Depends(get_engine)
):
    """创建DNS授权"""
    try:
        service = DNSAuthService(engine)
        result = service.create(data)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(400, str(e))


@router.put("/dns-auth/{id}", response_model=BaseResponse[schemas.DNSAuthRead])
async def update_dns_auth(
        id: int,
        data: schemas.DNSAuthUpdate,
        engine=Depends(get_engine)
):
    """更新DNS授权"""
    try:
        service = DNSAuthService(engine)
        result = service.update(id, data)
        if not result:
            return BaseResponse.error(404, f"DNS授权 ID:{id} 不存在")
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(400, str(e))


@router.delete("/dns-auth/{id}", response_model=BaseResponse)
async def delete_dns_auth(
        id: int,
        engine=Depends(get_engine)
):
    """删除DNS授权"""
    try:
        service = DNSAuthService(engine)
        success = service.delete(id)
        if not success:
            return BaseResponse.error(404, f"DNS授权 ID:{id} 不存在")
        return BaseResponse.success(message="删除成功")
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.post("/dns-auth/batch/delete", response_model=BaseResponse)
async def batch_delete_dns_auth(
        request: schemas.BatchOperationRequest,
        engine=Depends(get_engine)
):
    """批量删除DNS授权"""
    try:
        service = DNSAuthService(engine)
        count = service.batch_delete(request.ids)
        return BaseResponse.success(message=f"成功删除 {count} 个授权")
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/dns-auth/{id}", response_model=BaseResponse[schemas.DNSAuthReadSensitive])
async def get_dns_auth(
        id: int,
        engine=Depends(get_engine)
):
    """获取DNS授权详情"""
    service = DNSAuthService(engine)
    result = service.get_by_id(id)
    if not result:
        return BaseResponse.error(404, f"DNS授权 ID:{id} 不存在")

    # 脱敏处理
    sensitive = schemas.DNSAuthReadSensitive.from_orm(result)
    return BaseResponse.success(sensitive)


@router.get("/dns-auth", response_model=BaseResponse[schemas.DNSAuthListResponse])
async def list_dns_auth(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        provider: Optional[str] = Query(None, pattern="^(tencent|aliyun|cloudflare)$"),
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        engine=Depends(get_engine)
):
    """获取DNS授权列表"""
    service = DNSAuthService(engine)
    result = service.get_list(
        page=page,
        page_size=page_size,
        provider=provider,
        is_active=is_active,
        search=search
    )
    return BaseResponse.success(result)


@router.get("/dns-auth/stats/summary", response_model=BaseResponse[schemas.DNSAuthStats])
async def get_dns_auth_stats(engine=Depends(get_engine)):
    """获取DNS授权统计信息"""
    service = DNSAuthService(engine)
    stats = service.get_stats()
    return BaseResponse.success(stats)


# ========== 证书申请管理 ==========

@router.post("/applications", response_model=BaseResponse[schemas.ApplicationRead])
async def create_application(
        data: schemas.ApplicationCreate,
        engine=Depends(get_engine)
):
    """创建证书申请"""
    try:
        service = ApplicationService(engine)
        result = service.create(data)
        return BaseResponse.success(result)
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.put("/applications/{id}", response_model=BaseResponse[schemas.ApplicationRead])
async def update_application(
        id: int,
        data: schemas.ApplicationUpdate,
        engine=Depends(get_engine)
):
    """更新证书申请"""
    try:
        service = ApplicationService(engine)
        result = service.update(id, data)
        if not result:
            return BaseResponse.error(404, f"申请 ID:{id} 不存在")
        return BaseResponse.success(result)
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.delete("/applications/{id}", response_model=BaseResponse)
async def delete_application(
        id: int,
        engine=Depends(get_engine)
):
    """删除证书申请"""
    try:
        service = ApplicationService(engine)
        success = service.delete(id)
        if not success:
            return BaseResponse.error(404, f"申请 ID:{id} 不存在")
        return BaseResponse.success(message="删除成功")
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/applications/{id}", response_model=BaseResponse[schemas.ApplicationRead])
async def get_application(
        id: int,
        engine=Depends(get_engine)
):
    """获取证书申请详情"""
    service = ApplicationService(engine)
    result = service.get_by_id(id)
    if not result:
        return BaseResponse.error(404, f"申请 ID:{id} 不存在")
    return BaseResponse.success(result)


@router.get("/applications", response_model=BaseResponse[schemas.ApplicationListResponse])
async def list_applications(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        status: Optional[str] = Query(None, pattern="^(pending|processing|completed|failed)$"),
        dns_auth_id: Optional[int] = None,
        auto_renew: Optional[bool] = None,
        engine=Depends(get_engine)
):
    """获取证书申请列表"""
    service = ApplicationService(engine)
    result = service.get_list(
        page=page,
        page_size=page_size,
        status=status,
        dns_auth_id=dns_auth_id,
        auto_renew=auto_renew
    )
    return BaseResponse.success(result)


@router.post("/applications/execute", response_model=BaseResponse)
async def execute_application(
        request: Optional[schemas.ExecuteRequest] = None,
        engine=Depends(get_engine)
):
    """手动执行证书申请"""
    try:
        service = ApplicationService(engine)
        triggered_by = request.triggered_by if request else "manual"
        id = request.application_id if request else None
        result = service.execute(id, triggered_by)
        return BaseResponse.success(result, message="执行成功")
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/applications/stats/summary", response_model=BaseResponse[schemas.ApplicationStats])
async def get_application_stats(engine=Depends(get_engine)):
    """获取证书申请统计信息"""
    service = ApplicationService(engine)
    stats = service.get_stats()
    return BaseResponse.success(stats)


# ========== 证书管理 ==========

@router.get("/certificates/{id}", response_model=BaseResponse[schemas.CertificateDetail])
async def get_certificate(
        id: int,
        engine=Depends(get_engine)
):
    """获取证书详情"""
    service = CertificateService(engine)
    result = service.get_by_id(id)
    if not result:
        return BaseResponse.error(404, f"证书 ID:{id} 不存在")
    return BaseResponse.success(result)


@router.get("/certificates", response_model=BaseResponse[schemas.CertificateListResponse])
async def list_certificates(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        is_active: Optional[bool] = None,
        application_id: Optional[int] = None,
        algorithm: Optional[str] = Query(None, pattern="^(RSA|ECC)$"),
        engine=Depends(get_engine)
):
    """获取证书列表"""
    service = CertificateService(engine)
    result = service.get_list(
        page=page,
        page_size=page_size,
        is_active=is_active,
        application_id=application_id,
        algorithm=algorithm
    )
    return BaseResponse.success(result)


@router.post("/certificates/{id}/download", response_model=BaseResponse)
async def download_certificate(
        id: int,
        downloaded_by: Optional[str] = None,
        engine=Depends(get_engine)
):
    """下载证书"""
    try:
        service = CertificateService(engine)
        result = service.download(id, downloaded_by)
        return BaseResponse.success(result)
    except ValueError as e:
        return BaseResponse.error(404, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/certificates/{id}/downloads/count", response_model=BaseResponse[int])
async def get_certificate_download_count(
        id: int,
        engine=Depends(get_engine)
):
    """获取证书下载次数"""
    service = CertificateService(engine)
    count = service.get_download_count(id)
    return BaseResponse.success(count)


@router.get("/certificates/stats/summary", response_model=BaseResponse[schemas.CertificateStats])
async def get_certificate_stats(engine=Depends(get_engine)):
    """获取证书统计信息"""
    service = CertificateService(engine)
    stats = service.get_stats()
    return BaseResponse.success(stats)


# ========== 执行历史 ==========

@router.get("/applications/{application_id}/executions", response_model=BaseResponse[List[schemas.ExecutionRead]])
async def list_application_executions(
        application_id: int,
        engine=Depends(get_engine)
):
    """获取申请的执行历史"""
    service = ExecutionService(engine)
    results = service.get_by_application(application_id)
    return BaseResponse.success(results)


@router.get("/applications/{application_id}/executions/latest", response_model=BaseResponse[Optional[schemas.ExecutionRead]])
async def get_latest_execution(
        application_id: int,
        engine=Depends(get_engine)
):
    """获取申请的最新执行记录"""
    service = ExecutionService(engine)
    result = service.get_latest_by_application(application_id)
    return BaseResponse.success(result)
