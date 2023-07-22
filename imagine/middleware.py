import time
import json
from json import JSONDecodeError
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from fastapi import FastAPI, Response, Request
from starlette.types import Message
from imagine.db_manager import db
from auth.views.auth import get_current_user


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
        response, response_dict = await self._log_response(call_next, request)
        request_dict = await self._log_request(request)
        user_dict, user_id = self._log_user(request)

        self._create_log(request_dict, response_dict, user_dict, user_id)

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
            user_data = get_current_user(token)
        except:
            return {}, None
        user_dict = user_data.dict()
        if "password" in user_dict:
            user_dict.pop("password")
        return user_dict, user_data.id

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

    async def _log_response(self, call_next, request: Request) -> Response:
        start_time = time.perf_counter()

        response: Response = await call_next(request)

        finish_time = time.perf_counter()

        execution_time = finish_time - start_time

        response_logging = {
            "status_code": response.status_code,
            "time_taken": f"{execution_time:0.4f}s",
        }

        resp_body = [section async for section in response.__dict__["body_iterator"]]
        response.__setattr__("body_iterator", AsyncIteratorWrapper(resp_body))

        try:
            resp_body = json.loads(resp_body[0].decode())
        except:
            resp_body = str(resp_body)

        response_logging["body"] = resp_body

        return response, response_logging

    def _create_log(self, request_log, response_log, user_log, user_id):
        try:
            db.execute_sp(
                "imfun_create_log",
                f"{user_id}::int8" if user_id else "NULL::int8",
                f"'{json.dumps(request_log)}'::jsonb",
                f"'{json.dumps(response_log)}'::jsonb",
                f"'{json.dumps(user_log)}'::jsonb",
            )
        except Exception as e:
            print(e, flush=True)
