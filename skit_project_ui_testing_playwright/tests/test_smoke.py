def test_open_home(page):
    page.goto("https://automationintesting.online")
    assert "Restful" in page.title()

