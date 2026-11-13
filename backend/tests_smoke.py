"""Lightweight smoke checks for the RailNexus backend."""
from fastapi.testclient import TestClient
from app.main import app


def run():
    with TestClient(app) as client:
        checks = [
            ('/health', 'GET', 200),
            ('/api/v1/trains', 'GET', 200),
            ('/api/v1/trains/12627/eta', 'GET', 200),
            ('/api/v1/stations/KSR/platforms', 'GET', 200),
            ('/api/v1/trains/12627/seats', 'GET', 200),
            ('/api/v1/network/summary', 'GET', 200),
            ('/api/v1/demo/scenarios', 'GET', 200),
        ]
        for path, method, expected in checks:
            r = getattr(client, method.lower())(path)
            assert r.status_code == expected, (path, r.status_code, r.text)
        r = client.post('/api/v1/demo/scenario/signal')
        assert r.status_code == 200
        assert r.json()['state']['signal_delay'] == 15
        r = client.post('/api/v1/platforms/decision', json={'train_number':'12627','station_id':'KSR'})
        assert r.status_code == 200
    print('RailNexus smoke checks: PASS')


if __name__ == '__main__':
    run()
