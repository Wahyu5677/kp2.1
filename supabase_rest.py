import requests


class SupabaseRESTClient:
    def __init__(self, url: str, service_role_key: str):
        self.url = url.rstrip("/")
        self.key = service_role_key

    def _headers(self):
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    def select(
        self,
        table: str,
        filters: dict | None = None,
        columns: str = "*",
        order: str | None = None,
        limit: int | None = None,
    ):
        endpoint = f"{self.url}/rest/v1/{table}"
        params = {"select": columns}
        if filters:
            params.update(filters)
        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = limit

        resp = requests.get(endpoint, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def select_one_by_filters(self, table: str, filters: dict, columns: str = "*"):
        data = self.select(table=table, filters=filters, columns=columns, limit=1)
        return data[0] if data else None

    def insert(self, table: str, payload: dict):
        endpoint = f"{self.url}/rest/v1/{table}"
        resp = requests.post(
            endpoint,
            headers={**self._headers(), "Prefer": "return=representation"},
            json=[payload],
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None

    def update(self, table: str, filters: dict, payload: dict):
        endpoint = f"{self.url}/rest/v1/{table}"
        resp = requests.patch(
            endpoint,
            headers={**self._headers(), "Prefer": "return=representation"},
            params=filters,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None

    def delete_by_filter(self, table: str, filter_qs: dict):
        endpoint = f"{self.url}/rest/v1/{table}"
        resp = requests.delete(endpoint, headers=self._headers(), params=filter_qs, timeout=30)
        resp.raise_for_status()
        return resp.json() if resp.text else None
