# tests/test_navigation.py
import pytest
from pages.main_page import MainPage


@pytest.mark.nav
def test_top_nav_links_navigate(page):
    """
    Цел:
      - Потврда дека секој линк од NAVBAR те носи на соодветна секција/страница.
    Како:
      1) HOME
      2) Клик на секој линк преку main.open_nav(...) (scoped на <nav>, не footer).
      3) Чекање ориентирачки елемент за рутата со main.wait_any(...).
    Очекување:
      - Да се појави клучен елемент за секоја дестинација.
    """
    main = MainPage(page)
    main.goto_home()

    # Rooms
    main.open_nav("Rooms")
    main.wait_any([
        "section#rooms",
        "h2:has-text('Our Rooms')",
        "section#rooms a:has-text('Book now')"
    ])

    # Booking
    main.open_nav("Booking")
    main.wait_any([
        "section#booking",
        "button:has-text('Check Availability')"
    ])

    # Amenities
    main.open_nav("Amenities")
    main.wait_any([
        "h2:has-text('Amenities')",
        "text=Amenities"
    ])

    # Location
    main.open_nav("Location")
    main.wait_any([
        "h2:has-text('Location')",
        "text=Location"
    ])

    # Contact
    main.open_nav("Contact")
    main.wait_any([
        "#contact form",
        "button:has-text('Submit')",
        "h2:has-text('Contact')"
    ])


@pytest.mark.nav
def test_brand_click_returns_home(page):
    """
    Цел:
      - Клик на бренд-логото враќа на почетна.
    Очекување:
      - Да видиме booking секција или 'Check Availability' копче.
    """
    main = MainPage(page)
    main.goto_contact()  # од друга страница
    main.brand_link.click()
    main.wait_any(["section#booking", "button:has-text('Check Availability')"])


@pytest.mark.nav
def test_rooms_book_now_opens_reservation(page):
    """
    Цел:
      - Од Rooms → 'Book now' отвора /reservation/... (не од footer, туку од секцијата).
    Како:
      1) Rooms преку NAV.
      2) Чекај да се вчита 'section#rooms'.
      3) Кликни 'Book now' токму во 'section#rooms' (scoped).
      4) Потврди URL содржи '/reservation/'.
    """
    main = MainPage(page)
    main.goto_home()
    main.open_nav("Rooms")

    # Осигурај се дека секцијата е присутна
    rooms = page.locator("section#rooms").first
    rooms.wait_for(timeout=20000)

    # Клик на 'Book now' САМО во секцијата (не во footer)
    bn = rooms.get_by_role("link", name="Book now").first
    bn.scroll_into_view_if_needed()
    bn.click()

    page.wait_for_url("**/reservation/**", timeout=20000)
