from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserCreate, UserResponse
from app.security import (
    get_current_user,
    get_current_user_optional,
    require_role,
    hash_password,
    verify_password,
    create_access_token,
)

router = APIRouter(tags=["auth"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value,
        "name": user.name,
    }


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Two modes:
      1. Bootstrap: if no users exist yet, anyone can create the first
         ADMIN account (there is no other way to get an admin in).
      2. Normal: caller must be authenticated as ADMIN or PROPERTY_MANAGER.
         A PROPERTY_MANAGER may only create TENANT accounts (this is how
         "create/manage tenants" from the spec is implemented).
    """

    any_user_exists = db.query(User).first() is not None

    if not any_user_exists:
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The first account created in the system must be an ADMIN",
            )
    else:
        if current_user is None or current_user.role not in (
            UserRole.ADMIN,
            UserRole.PROPERTY_MANAGER,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to create users",
            )

        if current_user.role == UserRole.PROPERTY_MANAGER and user.role != UserRole.TENANT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Property managers can only create tenant accounts",
            )

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    new_user = User(
        name=user.name,
        email=user.email,
        role=user.role,
        password_hash=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/users", response_model=list[UserResponse])
def get_users(
    role: UserRole | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PROPERTY_MANAGER)),
):
    """
    ADMIN sees everyone. PROPERTY_MANAGER is restricted to TENANT
    accounts (they need this to pick a tenant when creating a lease),
    optionally filtered further by ?role=.
    """

    query = db.query(User)

    if current_user.role == UserRole.PROPERTY_MANAGER:
        query = query.filter(User.role == UserRole.TENANT)

    if role is not None:
        query = query.filter(User.role == role)

    return query.all()


@router.get("/users/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.TENANT and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user
