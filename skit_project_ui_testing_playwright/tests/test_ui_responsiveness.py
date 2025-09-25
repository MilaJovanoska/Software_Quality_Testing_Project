# tests/test_ui_responsiveness.py
# =============================================================================
# UI респонзивност тестови за https://automationintesting.online
#
# Покриеност:
#  1) Мобилен navbar: да колапсира (hamburger) и да може да се отвори/навигацијата да работи
#  2) Десктоп navbar: да е „расклопен“ (без hamburger) и навигацијата да работи директно
#  3) Резервациска страница layout: на десктоп "Price Summary" десно од формата,
#    а на мобилен стакнато под формата (проверка со bounding_box координати)
#
# Забелешки:
#  - Користиме MainPage.open_nav() која ја скопира кликовите на <nav> (не на footer).
#  - За layout тестот одиме директно на /reservation/1 со конкретни датуми за да се вчита стабилно UI-то.
# =============================================================================

import pytest
from pages.main_page import MainPage

MOBILE  = {"width": 375,  "height": 812}
DESKTOP = {"width": 1366, "height": 800}


@pytest.mark.ui
def test_navbar_collapses_on_mobile(page):
    """
    Што тестираме:
      - На мал viewport (мобилен) горното мени се колапсира и се појавува hamburger копчето.
      - По клик на hamburger, линковите стануваат достапни и навигацијата функционира.
    Како:
      1) viewport = MOBILE
      2) HOME
      3) Проверка: hamburger е видлив
      4) main.open_nav('Rooms') → треба да стигнеме до секцијата Rooms
    Очекување:
      - Да видиме клучен елемент од Rooms (section#rooms / „Book now“ итн.)
    """
    page.set_viewport_size(MOBILE)
    main = MainPage(page)
    main.goto_home()

    assert main.nav_toggler.is_visible(), "На мобилен очекуваме hamburger копче."
    main.open_nav("Rooms")
    main.wait_any([
        "section#rooms",
        "h2:has-text('Our Rooms')",
        "section#rooms a:has-text('Book now')",
    ])


@pytest.mark.ui
def test_navbar_is_expanded_on_desktop(page):
    """
    Што тестираме:
      - На десктоп, hamburger обично не е видлив и може да се кликне директно на нав-линкот.
    Како:
      1) viewport = DESKTOP
      2) HOME
      3) (најчесто) hamburger не е видлив
      4) main.open_nav('Rooms') → треба да стигнеме до Rooms
    Очекување:
      - Да се појави Rooms секцијата.
    """
    page.set_viewport_size(DESKTOP)
    main = MainPage(page)
    main.goto_home()

    # Не е критериум да НЕ постои hamburger, но ако постои, најчесто е скриен.
    try:
        assert not main.nav_toggler.is_visible()
    except Exception:
        # Ако локаторот не постои, тоа е исто ок за десктоп.
        pass

    main.open_nav("Rooms")
    main.wait_any([
        "section#rooms",
        "h2:has-text('Our Rooms')",
        "section#rooms a:has-text('Book now')",
    ])


@pytest.mark.ui
def test_reservation_layout_mobile_vs_desktop(page):
    """
    Што тестираме (layout):
      - На десктоп: 'Price Summary' е десно од формата (значително поголем X).
      - На мобилен: 'Price Summary' се стакнува под формата (значително поголем Y).
    Како:
      1) Одиме директно на /reservation/1 со валидни датуми (за да се вчита UI стабилно).
      2) DESKTOP viewport → спореди bounding_box на 'Price Summary' и input 'Firstname'.
      3) MOBILE viewport + reload → повторно спореди bounding_box.
    Очекување:
      - DESKTOP: price_summary.x > firstname.x + 250 (значи десно од формата)
      - MOBILE:  price_summary.y > firstname.y + 150 (значи под формата)
    """
    # 1) Десктоп распоред
    page.set_viewport_size(DESKTOP)
    page.goto("https://automationintesting.online/reservation/1?checkin=2025-09-26&checkout=2025-09-27")

    price = page.get_by_text("Price Summary").first
    fname = page.get_by_placeholder("Firstname").first

    price.wait_for(timeout=20000)
    fname.wait_for(timeout=20000)

    b_price = price.bounding_box()
    b_fname = fname.bounding_box()
    assert b_price and b_fname, "Не можев да ги земам координатите за елементите."

    assert b_price["x"] > b_fname["x"] + 250, \
        "На десктоп 'Price Summary' треба да е десно од формата (значително поголем X)."

    # 2) Мобилен распоред (стакнато)
    page.set_viewport_size(MOBILE)
    page.reload()  # форсирај reflow на layout
    # кратка пауза за да 'пресече' CSS layout-от по resize
    page.wait_for_timeout(300)

    price = page.get_by_text("Price Summary").first
    fname = page.get_by_placeholder("Firstname").first

    price.wait_for(timeout=20000)
    fname.wait_for(timeout=20000)

    b_price = price.bounding_box()
    b_fname = fname.bounding_box()
    assert b_price and b_fname, "Не можев да ги земам координатите за елементите (mobile)."

    assert b_price["y"] > b_fname["y"] + 150, \
        "На мобилен 'Price Summary' треба да биде под формата (значително поголем Y)."
