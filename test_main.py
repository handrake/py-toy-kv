from fastapi.testclient import TestClient
from main import app

import random

client = TestClient(app)


def test_set_main():
    k, v = "1", "2"
    r1 = client.post(
        "/",
        json={"key": k, "value": v}
    )
    assert r1.status_code == 200

    r2 = client.get("{}".format(k))

    json = r2.json()

    assert json['value'] == str(v)


def test_set_100_main():
    result_dict = {}
    for i in range(100):
        k, v = random.randint(1, 100), random.randint(1, 100)
        result_dict[str(k)] = str(v)
        r1 = client.post(
            "/",
            json={"key": str(k), "value": str(v)}
        )
        assert r1.status_code == 200

    for k, v in result_dict.items():
        r2 = client.get("{}".format(k))
        json = r2.json()

        assert json['value'] == str(v)
