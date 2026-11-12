# Transmitly Python SDK

```python
from transmitly import Transmitly

tx = Transmitly("txk_...")
accepted = tx.send_email(
    from_="Notify <notify@mail.acme.com>",
    to=["ada@example.net"],
    subject="Your workspace is ready",
    html="<p>Welcome.</p>",
    reply_to="support@acme.com",
)
```

No third-party dependencies. Non-2xx responses raise `TransmitlyError` with
`status`, `code`, `message` and `details`. Domain, webhook and inbound
management require an API key with the `admin` scope.

```bash
pip install ./sdk/python
```
