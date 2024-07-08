from dataclasses import dataclass
from typing import Optional
import threading
import queue
import time

q = queue.Queue()


@dataclass(order=True)
class Command:
    action: str
    key: str
    value: Optional[str] = None


def worker():
    expire_dict = {}
    dict = {}

    while True:
        command = q.get()

        deleted = False
        now = time.time()
        if command.key in expire_dict and command.key in dict and expire_dict[command.key] < now:
            del dict[command.key]
            deleted = True

        if command.action == 'SET' and not deleted:
            dict[command.key] = command.value
        elif command.action == 'GET':
            if not deleted and command.key in dict:
                print(f'GET {command.key} => {dict[command.key]}')
            else:
                print(f'GET {command.key} => None')
        elif command.action == 'EXPIRE' and not deleted:
            expire_dict[command.key] = int(command.value)


threading.Thread(target=worker, daemon=True).start()

while True:
    line = input('> ')

    if len(line.split()) < 2:
        print("invalid command")
        continue

    commands = line.split()
    action = commands[0]

    if action == 'GET' and len(commands) >= 2:
        key = commands[1]
        command = Command(action, key)
        q.put(command)
    elif action == 'SET' and len(commands) >= 3:
        key = commands[1]
        value = commands[2]
        command = Command(action, key, value)
        q.put(command)
    elif action == 'EXPIRE' and len(commands) >= 3:
        key = commands[1]
        seconds = commands[2]
        try:
            int(seconds)
        except:
            continue

        command = Command(action, key, str(int(time.time()) + int(seconds)))
        q.put(command)
