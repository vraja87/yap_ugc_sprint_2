import requests
import os

from http import HTTPStatus

from fastapi import HTTPException, Request


async def login_fullcheck_required(request: Request):
    auth = requests.get(
        f"""{os.getenv("AUTH_API_URL", "http://127.0.0.1/auth/api/v1/")}users/my_user""", headers=request.headers
    )
    if auth.status_code == HTTPStatus.OK:
        request.state.current_user = auth.json()
        return request
    else:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Token invalid!")
