# PhoBERT-TelecomGate API

Suppose base URL is `http://localhost:8136/v1` (also specify it
as the default in `.env.example`):

```sh
curl http://localhost:8136/v1/infer --http1.1 -X POST -H 'Content-Type: text/plain' -d 'Xin chào các bạn yêu quý! Chúng tôi rất trân trọng tình cảm của các bạn...
Hôm nay mọi người có vui không ạ?
Hãy cho phép tôi được giới thiệu bản thân nhé!'
```

which should output `false`. Or:

```sh
curl http://localhost:8136/v1/infer --http1.1 -X POST -H 'Content-Type: text/plain' -d 'Bên em có những dịch vụ viễn thông nào?'
```

which should output `true`. Or:

```sh
curl -s --write-out "\n\n<<< HTTP Code: %{http_code} >>>\n" http://localhost:8136/v1/infer --http1.1 -X POST
```

which should output:

    No input text?

    <<< HTTP Code: 400 >>>

The protocol is, you expect to get 200 and response
body being either `false` or `true`; or some
other HTTP status code, in which case the response body
contains the error message.
