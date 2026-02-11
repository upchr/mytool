import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
import os

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "toolsplus-default-secret-key-please-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 2  # 2小时

def create_jwt_token(data:dict) -> str:
    """创建 JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_jwt_token(token: str) -> dict:
    """验证 JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")

def create_access_token(user_id: int = 1) -> str:
    """创建管理员访问 token"""
    data = {"user_id": user_id, "type": "admin", "scope": "full"}
    return create_jwt_token(data)
