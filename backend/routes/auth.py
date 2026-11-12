from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt
from jose import JWTError, jwt

from config import settings
from database import get_db
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


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db=Depends(get_db),
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

    try:
        user_obj_id = ObjectId(token_data.user_id)
        user = await db.users.find_one({"_id": user_obj_id})
    except Exception:
        user = await db.users.find_one({"_id": token_data.user_id})

    if user is None:
        raise credentials_exception

    user["id"] = str(user["_id"])
    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db=Depends(get_db),
) -> Optional[dict]:
    """Dependency that returns the current user if authenticated, or None if guest."""
    if not credentials:
        return None
    token_data = verify_token(credentials.credentials)
    if not token_data or not token_data.user_id:
        return None

    try:
        try:
            user_obj_id = ObjectId(token_data.user_id)
            user = await db.users.find_one({"_id": user_obj_id})
        except Exception:
            user = await db.users.find_one({"_id": token_data.user_id})

        if user:
            user["id"] = str(user["_id"])
            return user
    except Exception:
        pass
    return None


async def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency that enforces admin privileges."""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action",
        )
    return current_user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db=Depends(get_db)):
    """Registers a new user, hashes password, and returns a JWT access token."""
    email_clean = user_in.email.strip().lower()

    existing_user = await db.users.find_one({"email": email_clean})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )

    hashed_pw = hash_password(user_in.password)
    user_dict = {
        "name": user_in.name.strip(),
        "email": email_clean,
        "password_hash": hashed_pw,
        "preferences": user_in.preferences.model_dump() if user_in.preferences else {},
        "is_admin": False,
        "created_at": datetime.utcnow(),
    }

    result = await db.users.insert_one(user_dict)
    new_user_id = str(result.inserted_id)

    access_token = create_access_token(
        data={"sub": new_user_id, "email": email_clean}
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db=Depends(get_db)):
    """Verifies credentials and returns a JWT access token."""
    email_clean = credentials.email.strip().lower()
    user = await db.users.find_one({"email": email_clean})

    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = str(user["_id"])
    access_token = create_access_token(
        data={"sub": user_id, "email": email_clean}
    )
    return Token(access_token=access_token, token_type="bearer")


@router.put("/preferences", response_model=UserOut, response_model_by_alias=False)
async def update_preferences(
    preferences: UserPreferences,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Updates taste preferences for the current user."""
    user_id = current_user["id"]
    try:
        obj_id = ObjectId(user_id)
        query = {"_id": obj_id}
    except Exception:
        query = {"_id": user_id}

    await db.users.update_one(query, {"$set": {"preferences": preferences.model_dump()}})
    updated = await db.users.find_one(query)
    updated["id"] = str(updated["_id"])
    return updated


@router.get("/me", response_model=UserOut, response_model_by_alias=False)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Returns profile details for the currently logged-in user."""
    return current_user
