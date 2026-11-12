"""Dependency-free Python client for the Transmitly API."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class TransmitlyError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.details = details or {}


class Transmitly:
    def __init__(self, api_key: str, base_url: str = "https://transmitly.io", timeout: float = 15.0):
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> Any:
        url = self.base_url + path
        if query:
            clean = {k: v for k, v in query.items() if v is not None and v != ""}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Accept", "application/json")
        req.add_header("Authorization", "Bearer " + self.api_key)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as err:
            raw = err.read()
            try:
                payload = json.loads(raw)
            except ValueError:
                payload = {}
            api = payload.get("error") or {}
            raise TransmitlyError(err.code, api.get("code", ""), api.get("message", str(err)), api.get("details")) from err

    # email
    def send_email(self, *, from_: str, to: str | list[str], subject: str, html: str | None = None,
                   text: str | None = None, reply_to: str | None = None, stream: str | None = None,
                   tags: dict[str, str] | None = None, headers: dict[str, str] | None = None,
                   idempotency_key: str | None = None) -> dict[str, Any]:
        if not html and not text:
            raise ValueError("html or text is required")
        body: dict[str, Any] = {"from": from_, "to": to, "subject": subject}
        for key, value in (("html", html), ("text", text), ("reply_to", reply_to),
                           ("stream", stream), ("tags", tags), ("headers", headers)):
            if value is not None:
                body[key] = value
        # urllib cannot set a custom idempotency header through Request.add_header
        # after creation? It can; use a direct request below.
        data = json.dumps(body).encode()
        req = urllib.request.Request(self.base_url + "/v1/emails", data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", "Bearer " + self.api_key)
        if idempotency_key:
            req.add_header("Idempotency-Key", idempotency_key)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as err:
            raw = err.read()
            try:
                payload = json.loads(raw)
            except ValueError:
                payload = {}
            api = payload.get("error") or {}
            raise TransmitlyError(err.code, api.get("code", ""), api.get("message", str(err)), api.get("details")) from err

    def get_email(self, message_id: str) -> dict[str, Any]:
        return self._request("GET", "/v1/emails/" + urllib.parse.quote(message_id))

    def list_messages(self, **params: Any) -> dict[str, Any]:
        return self._request("GET", "/v1/messages", query=params)

    # domains and suppression
    def list_domains(self) -> dict[str, Any]:
        return self._request("GET", "/v1/domains")

    def create_domain(self, domain: str) -> dict[str, Any]:
        return self._request("POST", "/v1/domains", body={"domain": domain})

    def verify_domain(self, domain_id: str) -> dict[str, Any]:
        return self._request("POST", "/v1/domains/" + urllib.parse.quote(domain_id) + "/verify")

    def list_suppressions(self, **params: Any) -> dict[str, Any]:
        return self._request("GET", "/v1/suppressions", query=params)

    def add_suppression(self, email: str, reason: str | None = None, note: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"email": email}
        if reason:
            body["reason"] = reason
        if note:
            body["note"] = note
        return self._request("POST", "/v1/suppressions", body=body)

    # webhooks and inbound
    def list_webhooks(self) -> dict[str, Any]:
        return self._request("GET", "/v1/webhooks")

    def create_webhook(self, url: str, events: list[str], domain_ids: list[str] | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"url": url, "events": events}
        if domain_ids:
            body["domain_ids"] = domain_ids
        return self._request("POST", "/v1/webhooks", body=body)

    def list_inbound_routes(self) -> dict[str, Any]:
        return self._request("GET", "/v1/inbound/routes")

    def create_inbound_route(self, address: str, action: str, destination: str | None = None,
                             note: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"address": address, "action": action}
        if destination:
            body["destination"] = destination
        if note:
            body["note"] = note
        return self._request("POST", "/v1/inbound/routes", body=body)

    def usage(self, **params: Any) -> dict[str, Any]:
        return self._request("GET", "/v1/usage", query=params)

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/v1/health")
