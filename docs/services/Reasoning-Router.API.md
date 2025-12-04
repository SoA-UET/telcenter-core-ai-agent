# PhoBERT-TelecomGate API

Suppose base URL is `http://localhost:8237/v1` (also specify it
as the default in `.env.example`):

```sh
curl http://localhost:8237/v1/infer --http1.1 -X POST -H 'Content-Type: text/plain' -d 'Gói SD-70 có ưu đãi gì không'
```

which should output `lookup_only`. Or:

```sh
curl http://localhost:8237/v1/infer --http1.1 -X POST -H 'Content-Type: text/plain' -d 'Gói nào rẻ nhất vậy'
```

which should output `reasoning_needed`. Or:

```sh
curl -s --write-out "\n\n<<< HTTP Code: %{http_code} >>>\n" http://localhost:8237/v1/infer --http1.1 -X POST
```

which should output:

    No input text?

    <<< HTTP Code: 400 >>>

The protocol is, you expect to get 200 and response
body being either `lookup_only` or `reasoning_needed`; or some
other HTTP status code, in which case the response body
contains the error message.
