import time
import re
import json
from json import JSONDecodeError
from uuid import UUID
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from fastapi import FastAPI, Response, Request
from starlette.types import Message
from imagine.db_manager import db, rd
from auth.views.auth import get_current_user
from decouple import config


class AsyncIteratorWrapper:
    def __init__(self, obj):
        self._it = iter(obj)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            value = next(self._it)
        except StopIteration:
            raise StopAsyncIteration
        return value


class LogsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI) -> None:
        super().__init__(app)
        self.app = app

    async def dispatch(self, request: Request, call_next) -> Response:
        await self.set_body(request)
        user_dict, user_id = self._log_user(request)
        url = self._url_convertion(request.url.path)
        method = request.method

        response, response_dict = await self._log_response(
            call_next, request, user_dict, url, method
        )
        request_dict = await self._log_request(request)

        self._create_log(request_dict, response_dict, user_dict, url, user_id)

        return response

    async def set_body(self, request: Request):
        """Avails the response body to be logged within a middleware as,
        it is generally not a standard practice.

           Arguments:
           - request: Request
           Returns:
           - receive_: Receive
        """
        receive_ = await request._receive()

        async def receive() -> Message:
            return receive_

        request._receive = receive

    def _log_user(self, request: Request) -> tuple[dict, int]:
        token = request.headers.get("Authorization", None)
        if not token:
            return {}, None

        token = token.split(" ")[1]
        try:
            payload = jwt.decode(token, config("SECRET_KEY"), algorithms=["HS256"])
            email: str = payload.get("email")
            if email is None:
                return {}, None
            if (cache_data := rd.get(f"user_data:{email}")) is not None:
                return cache_data, cache_data.get("id")
            else:
                user_data = db.execute_sp("imfun_get_user_data", f"'{email}'::varchar")
                return user_data, user_data.get("id")
        except Exception as e:
            return {}, None

    async def _log_request(self, request: Request) -> str:
        path = request.url.path
        if request.query_params:
            path += f"?{request.query_params}"

        request_logging = {
            "method": request.method,
            "path": path,
            "ip": request.client.host,
            "headers": dict(request.headers),
        }

        try:
            body = await request.json()
            if "password" in body:
                body = "Sensitive data"
            request_logging["body"] = body
        except JSONDecodeError:
            body = await request.body()
            if "password" in body.decode():
                body = "Sensitive data"
            else:
                body = body.decode()
            request_logging["body"] = body
        except Exception as e:
            request_logging["body"] = None

        return request_logging

    async def _log_response(
        self, call_next, request: Request, user_dict: dict, url: str, method: str
    ) -> Response:
        start_time = time.perf_counter()

        validate = self._validate_permission(user_dict, url, method)
        if not validate:
            resp_body = "Forbidden"
            response = Response(status_code=403, content=resp_body)
        else:
            response: Response = await call_next(request)
            resp_body = [
                section async for section in response.__dict__["body_iterator"]
            ]
            response.__setattr__("body_iterator", AsyncIteratorWrapper(resp_body))

            try:
                resp_body = json.loads(resp_body[0].decode())
            except:
                resp_body = str(resp_body)

        finish_time = time.perf_counter()

        execution_time = finish_time - start_time

        response_logging = {
            "status_code": response.status_code,
            "time_taken": f"{execution_time:0.4f}s",
        }
        response_logging["body"] = resp_body

        return response, response_logging

    def _create_log(self, request_log, response_log, user_log, url, user_id):
        try:
            db.execute_sp(
                "imfun_create_log",
                f"'{user_id}'::uuid" if user_id else "NULL::uuid",
                f"'{json.dumps(request_log)}'::jsonb",
                f"'{json.dumps(response_log)}'::jsonb",
                f"'{json.dumps(user_log)}'::jsonb",
                f"'{url}'::varchar",
            )
        except Exception as e:
            print(e, flush=True)

    def _valid_uuid(self, string):
        try:
            UUID(string)
            return True
        except ValueError:
            return False

    def _url_convertion(self, url: str) -> str:
        """Convert url to database format

        Args:
            url (str): Url to convert

        Returns:
            str: Converted url
        """

        url = re.split("[?]+", url)[0]
        url = re.split("[/]+", url)
        for i, item in enumerate(url):
            if item.isnumeric():
                url[i] = "#"
            elif self._valid_uuid(item):
                url[i] = "#"
        url = "/".join(url)
        return url

    def _validate_permission(self, user_dict: dict, url: str, method: str) -> bool:
        
        if url in ["/docs", "/redoc", "/openapi.json"]:
            return True
        
        user_group = user_dict.get("group", {}).get("id", None)

        rd_key = f"permission:{user_group}:{url}:{method}"
        
        rd_permission = rd.get(rd_key)
        
        if rd_permission is not None:
            return rd_permission == "True"

        permission = db.execute_sp(
            "imfun_get_user_permissions",
            f"{user_group}::int8" if user_group else "NULL::int8",
            f"'{url}'::varchar",
            f"'{method}'::varchar",
        )['permission']
        
        rd.create(rd_key, str(permission), 60)
        
        return permission
