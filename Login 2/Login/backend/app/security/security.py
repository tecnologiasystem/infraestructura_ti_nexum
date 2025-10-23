from datetime import datetime, timedelta
from jose import jwt
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from config import SECRET_KEY, ALGORITHM
from datetime import datetime, timedelta, time


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data: dict):
    to_encode = data.copy()

    ahora = datetime.now()
    expiracion = datetime.combine(ahora.date(), time(18, 0))  # 6:00 PM hora local

    if ahora >= expiracion:
        expiracion = datetime.combine(ahora.date() + timedelta(days=1), time(18, 0))

    to_encode.update({"exp": expiracion})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

def require_role(allowed_roles: list):
    def role_checker(user: dict = Depends(get_current_user)):
        user_role = user.get("rol")

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para acceder a este recurso.",
            )
        return user
    return role_checker
