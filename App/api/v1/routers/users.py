from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ....repositories.repository import get_user, create_user, get_user_by_email, update_user, delete_user
from ....schemas import UserCreate, UserResponse, Login, Token
from ....core.auth import verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from ....core.dependencies import get_current_user
from ....core.database import get_db
import traceback

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # simple uniqueness check
        existing = get_user_by_email(db, user.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        return create_user(db, user)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating user: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Swagger's OAuth2 password flow sends form-encoded fields (username/password),
    # so accept OAuth2PasswordRequestForm here to be compatible with the docs "Authorize" button.
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user_endpoint(user_id: int, user: UserCreate, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    updated_user = update_user(db, user_id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    deleted = delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return

