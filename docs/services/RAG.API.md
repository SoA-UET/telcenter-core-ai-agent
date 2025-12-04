# RAG API

## RabbitMQ API

This is currently the only way
to talk to this service.

### Queues

```py
request_queue_name = "telcenter_rag_text_requests"
response_queue_name = "telcenter_rag_text_responses"
```

### Request Body Format

```json
{
  "method": "one of the supported method names",
  "params": ["This could be a list", "or a dict"],
  "id": "this must always be present. it could be number or string"
}
```

A list of supported methods can be seen
[in this file](./rag_telcenter/realizations/server.py),
class `RAGRPCServer`. The `params` align with
the params of the methods of that class.

So if `params` is list, it is passed to
the method as `*args`. If it is a dict,
it is passed as `**kwargs`.

### Response Body Format

```json
{
  "id": "the id in the request body",
  "result": {
    "status": "success or error",
    "content": "the return value of the called method"
  }
}
```

IDs are not required to be unique.
But it would help to detect which
responses correspond to a given
request. So it is recommended
to generate UUIDv4 or something
like that as IDs.

### Some examples

#### 1. Calling `update_dataframe`

Request body:

```json
{
  "method": "update_dataframe",
  "params": {
    "source": "Viettel",
    "df": [
      {
        "Mã dịch vụ": "SD70",
        "Thời gian thanh toán": "Trả trước",
        "Các dịch vụ tiên quyết": "",
        "Giá (VNĐ)": 70000,
        "Chu kỳ (ngày)": 30,
        "4G tốc độ tiêu chuẩn/ngày": 1,
        "4G tốc độ cao/ngày": 0,
        "4G tốc độ tiêu chuẩn/chu kỳ": 30,
        "4G tốc độ cao/chu kỳ": 0,
        "Gọi nội mạng": "",
        "Gọi ngoại mạng": "",
        "Tin nhắn": "",
        "Chi tiết": "",
        "Tự động gia hạn": "Có",
        "Cú pháp đăng ký": "SD70 DK8 gửi 290"
      },
      {
        "Mã dịch vụ": "V90B",
        "Thời gian thanh toán": "Trả trước",
        "Các dịch vụ tiên quyết": "",
        "Giá (VNĐ)": 90000,
        "Chu kỳ (ngày)": 30,
        "4G tốc độ tiêu chuẩn/ngày": 0,
        "4G tốc độ cao/ngày": 1,
        "4G tốc độ tiêu chuẩn/chu kỳ": 0,
        "4G tốc độ cao/chu kỳ": 30,
        "Gọi nội mạng": "Miễn phí các cuộc gọi dưới 10 phút",
        "Gọi ngoại mạng": "Miễn phí 30 phút gọi",
        "Tin nhắn": "",
        "Chi tiết": "",
        "Tự động gia hạn": "Có",
        "Cú pháp đăng ký": "V90B HN4 gửi 290"
      }
    ]
  },
  "id": "1234"
}
```

Response body on success:

```json
{
  "id": "1234",
  "result": {
    "status": "success",
    "content": "OK"
  }
}
```

#### 2. Calling `query_vectordb`

Request body:

```json
{
  "method": "query_vectordb",
  "params": ["Cho hỏi gói SD 70 có giá bao nhiêu?"],
  "id": "12346"
}
```

Response body on success:

```json
{
  "id": "12346",
  "result": {
    "status": "success",
    "content": "D\u01b0\u1edbi \u0111\u00e2y li\u1ec7t k\u00ea m\u1ed9t s\u1ed1 th\u00f4ng tin li\u00ean quan. H\u00e3y s\u1eed d\u1ee5ng th\u00f4ng tin n\u00e0y \u0111\u1ec3 tr\u1ea3 l\u1eddi c\u00e2u h\u1ecfi c\u1ee7a ng\u01b0\u1eddi d\u00f9ng m\u1ed9t c\u00e1ch ch\u00ednh x\u00e1c v\u00e0 ng\u1eafn g\u1ecdn.\nN\u1ebfu kh\u00f4ng t\u00ecm th\u1ea5y th\u00f4ng tin li\u00ean quan, c\u1ea7n hi\u1ec3u r\u1eb1ng b\u1ea1n kh\u00f4ng th\u1ec3 tr\u1ea3 l\u1eddi c\u00e2u h\u1ecfi n\u00e0y.\n\nNh\u00e0 m\u1ea1ng: Viettel ; t\u00ean g\u00f3i c\u01b0\u1edbc: SD70 ;\nM\u00e3 d\u1ecbch v\u1ee5: SD70 . Th\u1eddi gian thanh to\u00e1n: Tr\u1ea3 tr\u01b0\u1edbc . C\u00e1c d\u1ecbch v\u1ee5 ti\u00ean quy\u1ebft:  . Gi\u00e1 (VN\u0110): 70000 . Chu k\u1ef3 (ng\u00e0y): 30 . 4G t\u1ed1c \u0111\u1ed9 ti\u00eau chu\u1ea9n/ng\u00e0y: 1 . 4G t\u1ed1c \u0111\u1ed9 cao/ng\u00e0y: 0 . 4G t\u1ed1c \u0111\u1ed9 ti\u00eau chu\u1ea9n/chu k\u1ef3: 30 . 4G t\u1ed1c \u0111\u1ed9 cao/chu k\u1ef3: 0 . G\u1ecdi n\u1ed9i m\u1ea1ng:  . G\u1ecdi ngo\u1ea1i m\u1ea1ng:  . Tin nh\u1eafn:  . Chi ti\u1ebft:  . T\u1ef1 \u0111\u1ed9ng gia h\u1ea1n: C\u00f3 . C\u00fa ph\u00e1p \u0111\u0103ng k\u00fd: SD70 DK8 g\u1eedi 290\n---\nNh\u00e0 m\u1ea1ng: Viettel ; t\u00ean g\u00f3i c\u01b0\u1edbc: V90B ;\nM\u00e3 d\u1ecbch v\u1ee5: V90B . Th\u1eddi gian thanh to\u00e1n: Tr\u1ea3 tr\u01b0\u1edbc . C\u00e1c d\u1ecbch v\u1ee5 ti\u00ean quy\u1ebft:  . Gi\u00e1 (VN\u0110): 90000 . Chu k\u1ef3 (ng\u00e0y): 30 . 4G t\u1ed1c \u0111\u1ed9 ti\u00eau chu\u1ea9n/ng\u00e0y: 0 . 4G t\u1ed1c \u0111\u1ed9 cao/ng\u00e0y: 1 . 4G t\u1ed1c \u0111\u1ed9 ti\u00eau chu\u1ea9n/chu k\u1ef3: 0 . 4G t\u1ed1c \u0111\u1ed9 cao/chu k\u1ef3: 30 . G\u1ecdi n\u1ed9i m\u1ea1ng: Mi\u1ec5n ph\u00ed c\u00e1c cu\u1ed9c g\u1ecdi d\u01b0\u1edbi 10 ph\u00fat . G\u1ecdi ngo\u1ea1i m\u1ea1ng: Mi\u1ec5n ph\u00ed 30 ph\u00fat g\u1ecdi . Tin nh\u1eafn:  . Chi ti\u1ebft:  . T\u1ef1 \u0111\u1ed9ng gia h\u1ea1n: C\u00f3 . C\u00fa ph\u00e1p \u0111\u0103ng k\u00fd: V90B HN4 g\u1eedi 290"
  }
}
```

Demangled content:

    Dưới đây liệt kê một số thông tin liên quan. Hãy sử dụng thông tin này để trả lời câu hỏi của người dùng một cách chính xác và ngắn gọn.
    Nếu không tìm thấy thông tin liên quan, cần hiểu rằng bạn không thể trả lời câu hỏi này.

    Nhà mạng: Viettel ; tên gói cước: SD70 ;
    Mã dịch vụ: SD70 . Thời gian thanh toán: Trả trước . Các dịch vụ tiên quyết:  . Giá (VNĐ): 70000 . Chu kỳ (ngày): 30 . 4G tốc độ tiêu chuẩn/ngày: 1 . 4G tốc độ cao/ngày: 0 . 4G tốc độ tiêu chuẩn/chu kỳ: 30 . 4G tốc độ cao/chu kỳ: 0 . Gọi nội mạng:  . Gọi ngoại mạng:  . Tin nhắn:  . Chi tiết:  . Tự động gia hạn: Có . Cú pháp đăng ký: SD70 DK8 gửi 290
    ---
    Nhà mạng: Viettel ; tên gói cước: V90B ;
    Mã dịch vụ: V90B . Thời gian thanh toán: Trả trước . Các dịch vụ tiên quyết:  . Giá (VNĐ): 90000 . Chu kỳ (ngày): 30 . 4G tốc độ tiêu chuẩn/ngày: 0 . 4G tốc độ cao/ngày: 1 . 4G tốc độ tiêu chuẩn/chu kỳ: 0 . 4G tốc độ cao/chu kỳ: 30 . Gọi nội mạng: Miễn phí các cuộc gọi dưới 10 phút . Gọi ngoại mạng: Miễn phí 30 phút gọi . Tin nhắn:  . Chi tiết:  . Tự động gia hạn: Có . Cú pháp đăng ký: V90B HN4 gửi 290

#### 3. Calling `query_reasoning`

Request body:

```json
{
"method": "query_reasoning",
"params": [
    "",
    "Cho hỏi gói VB90 có giá bao nhiêu?"
],
"id": "12347"
}
```

Response body on success:

```json
{
  "id": "12347",
  "result": {
    "status": "success",
    "content": "\n\u0110\u00e3 x\u00e1c \u0111\u1ecbnh \u0111\u01b0\u1ee3c ng\u1eef c\u1ea3nh ph\u00f9 h\u1ee3p. C\u00e1c g\u00f3i c\u01b0\u1edbc m\u00e0 ng\u01b0\u1eddi d\u00f9ng mong mu\u1ed1n l\u00e0: T\u1ea5t c\u1ea3 c\u00e1c g\u00f3i c\u01b0\u1edbc th\u1ecfa \u0111i\u1ec1u ki\u1ec7n: M\u00e3 d\u1ecbch v\u1ee5 = \"VB90\"\nC\u1ee5 th\u1ec3, d\u01b0\u1edbi \u0111\u00e2y l\u00e0 t\u1ea5t c\u1ea3 c\u00e1c g\u00f3i c\u01b0\u1edbc ph\u00f9 h\u1ee3p v\u1edbi y\u00eau c\u1ea7u c\u1ee7a ng\u01b0\u1eddi d\u00f9ng. Kh\u00f4ng c\u00f2n g\u00f3i c\u01b0\u1edbc n\u00e0o kh\u00e1c.\n\n\nM\u00e3 d\u1ecbch v\u1ee5: V90B\nGi\u00e1 (VN\u0110): 90000.0\n---\n\n---\nM\u00e3 d\u1ecbch v\u1ee5: SD70\nGi\u00e1 (VN\u0110): 70000.0\n---\n\n"
  }
}
```

Demangled content:


  Đã xác định được ngữ cảnh phù hợp. Các gói cước mà người dùng mong muốn là: Tất cả các gói cước thỏa điều kiện: Mã dịch vụ = "VB90"
  Cụ thể, dưới đây là tất cả các gói cước phù hợp với yêu cầu của người dùng. Không còn gói cước nào khác.


  Mã dịch vụ: V90B
  Giá (VNĐ): 90000.0
  ---

  ---
  Mã dịch vụ: SD70
  Giá (VNĐ): 70000.0
  ---


As you can see, it managed to
link the typo `VB90` in the request
to the package with actual name `V90B`.
