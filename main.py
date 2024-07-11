from dataclasses import dataclass
from typing import Optional, Union
from fastapi import FastAPI
from pydantic import BaseModel

import threading
import queue
import time

command_q = queue.Queue()


@dataclass(order=True)
class Command:
    action: str
    key: str
    value: Optional[str] = None
    return_q: Optional[queue.Queue] = None


@dataclass(order=True)
class CommandResponse:
    action: str
    key: str
    value: Optional[str] = None


class SetCommandRequest(BaseModel):
    key: str
    value: str


class ExpireCommandRequest(BaseModel):
    key: str
    expire: int


def worker():
    expire_store = {}
    store = {}

    while True:
        command = command_q.get()

        deleted = False
        now = time.time()
        if command.key in expire_store and command.key in store and expire_store[command.key] < now:
            del store[command.key]
            del expire_store[command.key]
            deleted = True

        if command.action == 'SET' and not deleted:
            store[command.key] = command.value
            response = CommandResponse(action='SET', key=command.key, value=command.value)
            command.return_q.put(response)
        elif command.action == 'GET':
            if not deleted and command.key in store:
                response = CommandResponse(action='GET', key=command.key, value=store[command.key])
                command.return_q.put(response)
            else:
                response = CommandResponse(action='GET', key=command.key, value=None)
                command.return_q.put(response)
        elif command.action == 'EXPIRE' and not deleted:
            expire_store[command.key] = int(command.value)
            response = CommandResponse(action='EXPIRE', key=command.key, value=command.value)
            command.return_q.put(response)


threading.Thread(target=worker, daemon=True).start()

app = FastAPI()


@app.get("/{key}")
async def get_value(key: str):
    return_q = queue.Queue()

    get_command = Command(action='GET', key=key, return_q=return_q)

    command_q.put(get_command)

    response = return_q.get(timeout=3)

    return response.value


@app.post("/")
async def set_value(set_request: SetCommandRequest):
    return_q = queue.Queue()

    set_command = Command(action='SET', key=set_request.key, value=set_request.value, return_q=return_q)

    command_q.put(set_command)

    response = return_q.get(timeout=3)

    return response


@app.put("/expire")
async def expire_key(expire_request: ExpireCommandRequest):
    return_q = queue.Queue()

    expire_command = Command(action='EXPIRE', key=expire_request.key, value=expire_request.expire, return_q=return_q)

    command_q.put(expire_command)

    response = return_q.get(timeout=3)

    return response
