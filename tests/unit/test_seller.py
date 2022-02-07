from functions.indeed_job_parser import indeed_job_parser


def test_stock_checker():
    stock_price = 25
    input_payload = {"stock_price": stock_price}

    data = indeed_job_parser.lambda_handler(input_payload, "")

    assert "id" in data
    assert "price" in data
    assert "type" in data
    assert "timestamp" in data
    assert "qty" in data

    assert data["type"] == "sell"
    assert data["price"] == str(stock_price)
