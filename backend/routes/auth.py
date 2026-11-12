from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt
from jose import JWTError, jwt

from config import settings
from database import get_db
from models.db_models import User
from models.user import Token, TokenData, UserCreate, UserInDB, UserLogin, UserOut, UserPreferences

router = APIRouter()

# Bearer token security scheme (auto_error=False allows optional auth)
security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hashes a plain text password with bcrypt directly."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        email: Optional[str] = payload.get("email")
        if user_id is None:
            return None
        return TokenData(user_id=user_id, email=email)
    except JWTError:
        return None


def _user_to_dict(user: User) -> dict:
    """Serializes a User ORM object to the dict shape the rest of the app expects."""
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "password_hash": user.password_hash,
        "preferences": user.preferences or {},
        "is_admin": user.is_admin,
        "created_at": user.created_at,
    }


async def _fetch_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return None
    result = await db.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Dependency that extracts and validates the currently authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise credentials_exception

    token_data = verify_token(credentials.credentials)
    if not token_data or not token_data.user_id:
        raise credentials_exception

    user = await _fetch_user_by_id(db, token_data.user_id)
    if user is None:
        raise credentials_exception

    return _user_to_dict(user)


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> Optional[dict]:
    """Dependency that returns the current user if authenticated, or None if guest."""
    if not credentials:
        return None
    token_data = verify_token(credentials.credentials)
    if not token_data or not token_data.user_id:
        return None

    user = await _fetch_user_by_id(db, token_data.user_id)
    if user is None:
        return None
    return _user_to_dict(user)


async def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency that enforces admin privileges."""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action",
        )
    return current_user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new user, hashes password, and returns a JWT access token."""
    email_clean = user_in.email.strip().lower()

    existing = await db.execute(select(User).where(User.email == email_clean))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )

    hashed_pw = hash_password(user_in.password)
    new_user = User(
        name=user_in.name.strip(),
        email=email_clean,
        password_hash=hashed_pw,
        preferences=user_in.preferences.model_dump() if user_in.preferences else {},
        is_admin=False,
        created_at=datetime.utcnow(),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": email_clean}
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Verifies credentials and returns a JWT access token."""
    email_clean = credentials.email.strip().lower()
    result = await db.execute(select(User).where(User.email == email_clean))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": email_clean}
    )
    return Token(access_token=access_token, token_type="bearer")


@router.put("/preferences", response_model=UserOut, response_model_by_alias=False)
async def update_preferences(
    preferences: UserPreferences,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates taste preferences for the current user."""
    user = await _fetch_user_by_id(db, current_user["id"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.preferences = preferences.model_dump()
    await db.commit()
    await db.refresh(user)
    return _user_to_dict(user)


@router.get("/me", response_model=UserOut, response_model_by_alias=False)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Returns profile details for the currently logged-in user."""
    return current_user
