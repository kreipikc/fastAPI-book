from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from app.users.auth import get_password_hash, create_access_token, create_refresh_token
from app.users.dependencies import get_current_user, refresh_access_token
from app.users.schemas import SUser, SUserAuth
from app.users.service import UserRepository


router = APIRouter(prefix="/auth", tags=["Auth 🙎🏻‍♂️"])


@router.post("/register", summary="User registration")
async def register_user(user_data: SUser):
    user = await UserRepository.find_one_or_none(user_data.email)
    if user:
        raise HTTPException(status_code=409, detail='Пользователь уже существует')
    user_data.password = get_password_hash(user_data.password)
    await UserRepository.add_user(user_data)
    return {'message': 'Вы успешно зарегистрированы!'}


@router.post("/login", summary="Login for user")
async def auth_user(response: Response, user_data: SUserAuth):
    check = await UserRepository.authenticate_user(email=user_data.email, password=user_data.password)
    if check is None:
        raise HTTPException(status_code=401, detail='Неверная почта или пароль')

    access_token = create_access_token({"sub": str(check.id)})
    refresh_token = create_refresh_token({"sub": str(check.id)})

    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    response.set_cookie(key="users_refresh_token", value=refresh_token, httponly=True)

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/refresh", summary="Refresh access token")
async def refresh_token_endpoint(response: Response, new_token: dict = Depends(refresh_access_token)):
    response.set_cookie(key="users_access_token", value=new_token["access_token"], httponly=True)
    return new_token


@router.post("/logout", summary="Logout account")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    response.delete_cookie(key="users_refresh_token")
    return {"message": "Пользователь успешно вышел из системы"}


@router.get("/me", summary="Information about you")
async def get_me(user_data: SUser = Depends(get_current_user)):
    return user_data