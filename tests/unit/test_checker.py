from functions.indeed_downloader import indeed_downloader


def test_stock_checker():
    data = indeed_downloader.lambda_handler(None, "")
    assert 0 <= data["stock_price"] > 0 <= 100
