# tests/test_booking_flow.py
import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from pages.main_page import MainPage


# Формат на датуми на сајтот: DD/MM/YYYY
CHECKIN  = "25/09/2025"
CHECKOUT = "26/09/2025"


def _reach_booking_form(main: MainPage):
    """
    Common step:
    1) /#/booking → set dates → Check Availability
    2) 'Our Rooms' → Book now
    3) (ако треба) sidebar 'Reserve Now'
    4) чекaј ја формата
    """
    main.goto_booking()
    main.set_dates(CHECKIN, CHECKOUT)
    main.click_check_availability()
    main.click_first_book_now()
    main.maybe_click_sidebar_reserve_now()
    main.wait_booking_form()


@pytest.mark.booking
def test_booking_happy_path_navigation_to_form(page):
    """
    Проверка дека со валидни датуми можеме да стигнеме до формата:
    Check Availability → Our Rooms → Book now → (Reserve Now) → појавена форма.
    """
    main = MainPage(page)
    _reach_booking_form(main)

    # минимална потврда – првото поле е видливо
    assert main.firstname_input.is_visible()


@pytest.mark.booking
def test_booking_submit_valid_data_posts_to_backend(page):
    """
    Позитивен flow:
      - Пополнување на формата со валидни податоци
      - Клик на финалното 'Reserve Now' (#doReservation)
      - Очекуваме панел 'Booking Confirmed'
    """
    main = MainPage(page)
    _reach_booking_form(main)

    main.fill_booking_form(
        firstname="Мила",
        lastname="Тестова",
        email="mila.tester@example.com",
        phone="+38971234567",
    )
    main.click_final_reserve()
    main.wait_booking_confirmed()  # не фрла Timeout ако е успешно


@pytest.mark.booking
def test_booking_invalid_email_shows_validation_error_no_success(page):
    """
    Негативен случај:
      - Невалиден е-пошта формат во формата
      - Очекување: да НЕ се појави 'Booking Confirmed'
    """
    main = MainPage(page)
    _reach_booking_form(main)

    main.fill_booking_form(
        firstname="Мила",
        lastname="Тестова",
        email="bad@",          # невалиден формат
        phone="+38971234567",
    )
    main.click_final_reserve()

    # Намерно чекаме кратко за success, треба да фрли Timeout
    with pytest.raises(PlaywrightTimeoutError):
        page.get_by_role("heading", name="Booking Confirmed").first.wait_for(timeout=5000)
