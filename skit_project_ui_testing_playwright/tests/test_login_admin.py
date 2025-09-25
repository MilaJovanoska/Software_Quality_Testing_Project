# tests/test_login_admin.py
# =============================================================================
# UI тестови за LOGIN на:
#     https://automationintesting.online/admin
#
# Покриено:
#  1) Smoke: полиња + копче постојат
#  2) Happy path: валидни креденцијали (admin/password)
#  3) Негативни: празни полиња, погрешен username, погрешна лозинка
#  4) Безбедност: едноставен SQLi не смее да помине
#  5) Робустност: многу долги креденцијали → очекуваме грешка, не login
# =============================================================================

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from pages.main_page import MainPage


# ------------------------------ Helpers --------------------------------------

def expect_login_success(page, timeout: int = 15000) -> None:
    """
    Чека индикатор дека сме внатре во админ (dashboard/менито).
    Пробаваме низа селектори за поголема робусност.
    """
    candidates = [
        ".reservations",                      # најчесто присутно по успешен login
        "text=Reservations",                  # текст fallback
        "a:has-text('Rooms')",                # линк во менито
        "a:has-text('Branding')",             # линк во менито
    ]
    last_err = None
    slice_timeout = max(timeout // len(candidates), 2000)
    for sel in candidates:
        try:
            page.wait_for_selector(sel, timeout=slice_timeout)
            return
        except Exception as e:
            last_err = e
    raise PlaywrightTimeoutError(
        f"Admin UI not detected via any success selector. Last: {last_err}"
    )


def expect_login_error(page, timeout: int = 7000) -> None:
    """
    Чека визуелен сигнал за неуспешен login.
    ВАЖНО: не мешај CSS и 'text=' во еден селектор — пробуваме последователно.
    """
    css_candidates = [
        ".alert-danger",
        ".alert",
        "[role='alert']",
    ]
    text_candidates = ["invalid", "unauthorized", "error", "wrong", "fail"]

    # делиме време отприлика 40/60
    css_timeout = max(int(timeout * 0.4 / max(len(css_candidates), 1)), 1000)
    text_timeout = max(int(timeout * 0.6 / max(len(text_candidates), 1)), 800)

    last_err = None

    # 1) CSS alerts
    for sel in css_candidates:
        try:
            page.wait_for_selector(sel, timeout=css_timeout)
            return
        except Exception as e:
            last_err = e

    # 2) Текстови (case-insensitive)
    for t in text_candidates:
        try:
            page.get_by_text(t, exact=False).first.wait_for(timeout=text_timeout)
            return
        except Exception as e:
            last_err = e

    raise PlaywrightTimeoutError(
        f"Login error UI not detected. Last: {last_err}"
    )


# ------------------------------- Tests ---------------------------------------

@pytest.mark.login
def test_login_smoke_fields_present(page):
    """
    Smoke: проверка дека страната се вчитува и елементите постојат/видливи.
    """
    main = MainPage(page)
    main.goto_admin()

    main.login_username_input.wait_for(timeout=5000)
    main.login_password_input.wait_for(timeout=5000)
    main.login_button.wait_for(timeout=5000)

    assert main.login_username_input.is_visible()
    assert main.login_password_input.is_visible()
    assert main.login_button.is_visible()


@pytest.mark.login
def test_login_positive(page):
    """
    Happy-path: валидни креденцијали → треба да видиме админ UI.
    """
    main = MainPage(page)
    main.goto_admin()

    main.login("admin", "password")
    expect_login_success(page, timeout=15000)


@pytest.mark.login
def test_login_blank_fields(page):
    """
    Празни полиња: submit без username/password → треба да видиме грешка.
    """
    main = MainPage(page)
    main.goto_admin()

    main.login("", "")
    expect_login_error(page)


@pytest.mark.login
def test_login_invalid_username(page):
    """
    Погрешно корисничко име: wronguser/password → грешка.
    """
    main = MainPage(page)
    main.goto_admin()

    main.login("wronguser", "password")
    expect_login_error(page)


@pytest.mark.login
def test_login_invalid_password(page):
    """
    Погрешна лозинка: admin/wrongpass → грешка.
    """
    main = MainPage(page)
    main.goto_admin()

    main.login("admin", "wrongpass")
    expect_login_error(page)


@pytest.mark.login
def test_login_sql_injection(page):
    """
    Едноставен SQLi обид: не смее да помине.
    """
    main = MainPage(page)
    main.goto_admin()

    payload = "' OR '1'='1"
    main.login(payload, payload)
    expect_login_error(page)


@pytest.mark.login
def test_login_long_credentials(page):
    """
    Робустност: многу долги креденцијали → очекуваме грешка, не login.
    """
    main = MainPage(page)
    main.goto_admin()

    long_text = "a" * 300
    main.login(long_text, long_text)
    expect_login_error(page)


# --------------------------- NEW TESTS (added) -------------------------------

@pytest.mark.login
def test_login_username_case_sensitivity(page):
    """
    ЦЕЛ:
        - Да провериме дека системот прави разлика меѓу 'admin' и 'Admin'
          (односно дека корисничкото име е case-sensitive).
    ЗОШТО:
        - Во многу системи username се третира case-insensitive, но за админ
          често е пожелно да биде case-sensitive (безбедносна конзистентност).
    ЧЕКОРИ:
        1) Отвораме /admin.
        2) Внесуваме 'Admin' (голема почетна буква) и точна лозинка 'password'.
        3) Сабмит.
    ОЧЕКУВАЊЕ:
        - Да добиеме индикатор за грешка (неуспешен login),
          бидејќи очекуваме валидно е само 'admin'.
    """
    main = MainPage(page)
    main.goto_admin()

    main.login("Admin", "password")  # само првата буква е голема
    expect_login_error(page)


@pytest.mark.login
def test_login_password_case_sensitivity(page):
    """
    ЦЕЛ:
        - Да провериме дека лозинката е *case-sensitive*.
    ЗОШТО:
        - Лозинките секогаш треба да прават разлика меѓу големи/мали букви.
    ЧЕКОРИ:
        1) Отвораме /admin.
        2) Внесуваме валиден username 'admin' и лозинка 'Password'
           (голема 'P' наместо правилното 'password').
        3) Сабмит.
    ОЧЕКУВАЊЕ:
        - Да добиеме индикатор за грешка (неуспешен login).
    """
    main = MainPage(page)
    main.goto_admin()

    main.login("admin", "Password")  # погрешен case во лозинка
    expect_login_error(page)


@pytest.mark.login
def test_login_submit_with_enter_key(page):
    """
    ЦЕЛ:
        - Да провериме UX-поведението: сабмит преку копче ENTER (без клик на 'Submit').
    ЗОШТО:
        - Многу корисници по навика притискаат Enter по внес на лозинка,
          па формата треба да се сабмитира.
    ЧЕКОРИ:
        1) Отвораме /admin.
        2) Пополнуваме 'admin' / 'password'.
        3) Во полето за лозинка притискаме Enter (key press) наместо да кликнеме на копче.
    ОЧЕКУВАЊЕ:
        - Успешен login (го гледаме админ интерфејсот).
    """
    main = MainPage(page)
    main.goto_admin()

    # рачно пополнување, без повик на main.login, за да тестираме ENTER submit
    main.login_username_input.fill("admin")
    main.login_password_input.fill("password")
    main.login_password_input.press("Enter")

    expect_login_success(page, timeout=15000)

# --------------------------- EXTRA TESTS (whitespace & throttle) -------------


@pytest.mark.login
def test_login_username_whitespace_behavior_documented(page):
    """
    ЦЕЛ:
        - Да ја документираме реалната логика на демото околу
          водечки/завршни празни места во КОРИСНИЧКОТО ИМЕ (username).
    ЗОШТО:
        - Некои системи trim-ираат username (очекувано ОК), други бараат строго
          совпаѓање (очекувано GRЕШКА). Демото може да се смени низ време.
    ЧЕКОРИ:
        1) Внесуваме username со празни места: "  admin  " и точна лозинка "password".
        2) Сабмит.
    ОЧЕКУВАЊЕ:
        - Тестот е „документарен“: прифаќаме и едното и другото однесување,
          но тврдиме дека барем едно од следново важи:
            a) Успешен login (ако има trimming), ИЛИ
            б) Прикажана грешка (ако нема trimming).
    ЗАБЕЛЕШКА:
        - Ако сакаш строго правило, смени ја логиката: очекувај успех или грешка
          според политиката на твојот продукт.
    """
    main = MainPage(page)
    main.goto_admin()

    main.login("  admin  ", "password")

    try:
        # ако има trimming → ќе успее за < 6s
        expect_login_success(page, timeout=6000)
        # ако стигне тука, значи системот trim-ира → документриано е како „валидно“
    except PlaywrightTimeoutError:
        # во спротивно очекуваме грешка
        expect_login_error(page, timeout=6000)


@pytest.mark.login
def test_login_password_whitespace_strict_fails(page):
    """
    ЦЕЛ:
        - Да потврдиме дека ЛОЗИНКАТА е *строго* case/char sensitive и НЕ се trim-ира.
    ЗОШТО:
        - Безбедносна практика: лозинки не се нормализираат (ни trimming, ни lowercasing).
    ЧЕКОРИ:
        1) Внесуваме валиден username 'admin' и лозинка со празни места: '  password  '.
        2) Сабмит.
    ОЧЕКУВАЊЕ:
        - Грешка (неуспешен login).
    """
    main = MainPage(page)
    main.goto_admin()

    main.login("admin", "  password  ")
    expect_login_error(page)


@pytest.mark.login
def test_login_multiple_failed_then_success(page):
    """
    ЦЕЛ:
        - „Throttle/lockout“ санитарна проверка: повеќе брзи неуспешни обиди
          не треба да го „скршат“ UI, и веднаш потоа валиден обид треба да помине.
    ЗОШТО:
        - Корисници често трипат грешат, па потоа се сетуваат на точната лозинка.
          Сакаме да видиме стабилност и одсуство на „мека“ блокада.
    ЧЕКОРИ:
        1) Двапати по ред admin/wrongpass → секојпат очекуваме грешка.
        2) Потоа admin/password → очекуваме успешен login.
    ОЧЕКУВАЊЕ:
        - Првите два обиди → грешка.
        - Третиот (валиден) → успех (админ UI видлив).
    """
    main = MainPage(page)
    main.goto_admin()

    # два брзи неуспешни обиди
    for _ in range(2):
        main.login("admin", "wrongpass")
        expect_login_error(page, timeout=5000)

    # веднаш потоа валиден обид
    main.login("admin", "password")
    expect_login_success(page, timeout=15000)
