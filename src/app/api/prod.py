from typing import List

from fastapi import APIRouter, HTTPException, Path

from app.api import crud
from app.api.models import ProdSchema, ProdDB,OrderSchema

from datetime import datetime, timedelta
from typing import List

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import PyJWTError
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError
from starlette.status import HTTP_401_UNAUTHORIZED

from fastapi_permissions import (
    Allow,
    Authenticated,
    Deny,
    Everyone,
    configure_permissions,
    list_permissions,
)
router = APIRouter()
app = FastAPI()

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

fake_users_db = {
    "bob": {
        "username": "bob",
        "full_name": "Bobby Bob",
        "email": "bob@example.com",
        "hashed_password": pwd_context.hash("secret"),

        "principals": ["user:bob", "role:admin"],

    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Chains",
        "email": "alicechains@example.com",
        "hashed_password": pwd_context.hash("secret"),

        "principals": ["user:alice"],

    },
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None


class User(BaseModel):
    username: str
    email: str = None
    full_name: str = None
    principals: List[str] = []


class UserInDB(User):
    hashed_password: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def get_item(item_id: int):
    if item_id in fake_items_db:
        item_dict = fake_items_db[item_id]
        return Item(**item_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(*, data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except (PyJWTError, ValidationError):
        raise credentials_exception
    user = get_user(fake_users_db, username=username)
    if user is None:
        raise credentials_exception
    return user


fake_items_db = {
    1: {"name": "Stilton", "owner": "bob"},
    2: {"name": "Danish Blue", "owner": "alice"},
}


class Item(BaseModel):
    name: str
    owner: str

    def __acl__(self):
        return [
            (Allow, Authenticated, "view"),
            (Allow, "role:admin", "use"),
            (Allow, f"user:{self.owner}", "use"),
        ]


class ItemListResource:
    __acl__ = [(Allow, Authenticated, "view")]


NewItemAcl = [(Deny, "user:bob", "create"), (Allow, Authenticated, "create")]


def get_active_principals(user: User = Depends(get_current_user)):
    if user:
        # user is logged in
        principals = [Everyone, Authenticated]
        principals.extend(getattr(user, "principals", []))
    else:
        # user is not logged in
        principals = [Everyone]
    return principals


Permission = configure_permissions(get_active_principals)


@app.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = authenticate_user(
        fake_users_db, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=400, detail="Incorrect username or password"
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user





@router.post("/", response_model=ProdDB, status_code=201)
async def create_prod(payload: ProdSchema, acls: list = Permission("create", NewItemAcl)):
    note_id = await crud.post(payload)

    response_object = {
        "id": note_id,
        "title": payload.title,
        "description": payload.description,
    }
    return response_object


@router.get("/{id}/", response_model=ProdDB)
async def read_prod(id: int = Path(..., gt=0), ):
    prod = await crud.get(id)
    if not prod:
        raise HTTPException(status_code=404, detail="Note not found")
    return prod


@router.get("/", response_model=List[ProdDB])
async def read_all():
    prod=await crud.get_product_count
    if not prod >0:
        raise HTTPException(status_code=403)
    return await crud.get_all()


@router.get("/order/{id}/", response_model=OrderSchema)
async def read_prod(id: int = Path(..., gt=0), ):
    order = await crud.get(id)
    if not order:
        raise HTTPException(status_code=403)
    return order
