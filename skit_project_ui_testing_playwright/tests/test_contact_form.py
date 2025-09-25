# tests/test_contact_form.py
# =============================================================================
# UI тестови за "Contact" формата на:
#     https://automationintesting.online/#/contact
#
# Овој фајл е структуриран според следниве принципи:
# - Page Object Model (POM): Сите селектори и “мали” акции се во pages/MainPage.
# - AAA (Arrange-Act-Assert) стил: секој тест прво подготвува (Arrange),
#   потоа дејствува (Act), и на крај тврди (Assert).
# - Стабилност: Чекањата ги правиме преку `wait_for_*`/`locator.wait_for`
#   наместо произволни sleep-ови; timeout-ите се малку пошироки (20s) поради
#   повремена бавност на демо-страницата.
# - Јасни податоци: Централизиран “VALID” payload за доследност.
#
# Обем на покриеност:
#  1) Happy path (валидни податоци → success alert)
#  2) Негативни случаи:
#     - e-mail формати (со should_pass за `mila@domain` бидејќи демото го прифаќа)
#     - телефон (премалку/предолго/букви)
#     - должини на subject/message
#     - празни полиња
#     - секое задолжително поле поединечно празно
#  3) Робустност / корисничко однесување:
#     - двоен submit (да не прати двапати)
#     - trim/whitespace (leading/trailing spaces)
#     - case-insensitive е-пошта
#     - basic XSS guard (да не се крене JS alert)
#
# Напомени:
# - Овие се **UI** тестови и не гарантираат серверска логика; затоа некои
#   “гранични” формати можат да бидат прифатени од демото (пример: mila@domain).
# - Ако демото е бавно, зголемете timeout на 25000 ms.
# =============================================================================

from typing import Optional, Dict
import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from pages.main_page import MainPage


# -----------------------------------------------------------------------------
# Централизиран валиден payload за сите тестови
#  - Вака одржуваме конзистентност и на едно место ги менуваме вредностите.
#  - Вредностите се “реалистични” (не само ‘a’ * 2000), што олеснува читање.
# -----------------------------------------------------------------------------
VALID: Dict[str, str] = {
    "name": "Мила Тестова",
    "email": "mila.tester@example.com",
    "phone": "+38971234567",
    "subject": "Прашање за сместување",
    "description": (
        "Ова е тест порака со доволна должина за да помине валидаторот. "
        "Содржи повеќе зборови и реченици за да симулира реален кориснички внес."
    ),
}


def _submit(main: MainPage, override: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Helper (реупотреблив чекор за Arrange+Act):

    Што:
        - Гради payload (VALID + override), ги пополнува полињата во формата и прави Submit.
    Зошто:
        - Во сите тестови имаме ист образец за пополнување и сабмитирање.
          Со ова избегнуваме дуплиран код и грешки.
    Како:
        - Копираме VALID, дополнително ги заменуваме клучевите од `override`,
          повикуваме main.fill_contact_form(**data), па main.submit_contact_form().
    Очекување:
        - Враќа подготвен payload за евентуални понатамошни проверки во тестот.
    """
    data = VALID.copy()
    if override:
        data.update(override)
    main.fill_contact_form(**data)
    main.submit_contact_form()
    return data


# ============================== HAPPY PATH ===================================

@pytest.mark.contact
def test_contact_happy_path(page):
    """
    Што тестираме:
        - Стандардно, позитивно сценарио со валидни податоци.
    Зошто:
        - За да потврдиме дека “нормалниот” корисник без грешки ја добива
          очекуваната success порака после успешна поднесена форма.
    Како:
        1) Одиме на /#/contact.
        2) Пополнуваме валидни полиња (централизирани во VALID).
        3) Submit.
        4) Чекаме success alert.
    Очекување:
        - Да се појави “Thanks for getting in touch”.
    Забелешки:
        - Timeout 20s бидејќи демо-то знае да е бавно; при реални апликации
          намалете го според перформанси/SLAs.
    """
    main = MainPage(page)
    main.goto_contact()

    _submit(main)
    text = main.wait_success_contact(timeout=20000)
    assert "Thanks for getting in touch" in text


# ============================== E-MAIL ========================================

@pytest.mark.contact
@pytest.mark.parametrize(
    "email,should_pass",
    [
        pytest.param("mila@", False, id="mila@"),
        pytest.param("mila@domain", True, id="mila@domain (accepted-by-demo)"),
        pytest.param("mila@domain..com", False, id="double-dot"),
        pytest.param("mila domain.com", False, id="space-in-email"),
        pytest.param("@domain.com", False, id="no-local-part"),
    ],
)
def test_contact_emails_validation(page, email, should_pass):
    """
    Што тестираме:
        - Валидација на различни формати на e-mail (позитивни/негативни).
    Зошто:
        - Е-mail е честа точка за грешки; сакаме да видиме како Front/UI+Demo реагира.
    Како:
        1) Пополнуваме валидни полиња, освен e-mail кој варира.
        2) Submit.
        3) Ако should_pass=True → чекаме success; инаку очекуваме timeout (нема success).
    Очекување:
        - Точно однесување според `should_pass`.
    Забелешки:
        - Демото го прифаќа `mila@domain` → затоа го третираме како валиден.
    """
    main = MainPage(page)
    main.goto_contact()

    _submit(main, {"email": email})

    if should_pass:
        txt = main.wait_success_contact(timeout=20000)
        assert "Thanks for getting in touch" in txt
    else:
        with pytest.raises(PlaywrightTimeoutError):
            page.wait_for_selector("h3:has-text('Thanks for getting in touch')", timeout=5000)


@pytest.mark.contact
def test_contact_email_case_insensitive(page):
    """
    Што тестираме:
        - Дека е-пошта со големи букви се третира исто како и со мали (case-insensitive).
    Зошто:
        - Корисниците често внесуваат комбинации на големи/мали.
    Како:
        1) Го земаме VALID email и го претвораме во UPPERCASE.
        2) Submit.
        3) Чекаме success alert.
    Очекување:
        - Успешна поднесена форма (success alert видлив).
    """
    main = MainPage(page)
    main.goto_contact()

    upper = VALID["email"].upper()
    _submit(main, {"email": upper})
    txt = main.wait_success_contact(timeout=20000)
    assert "Thanks for getting in touch" in txt


# ============================== PHONE =========================================

@pytest.mark.contact
@pytest.mark.parametrize(
    "phone",
    [
        pytest.param("12345", id="too-short"),
        pytest.param("1234567890123456789012", id="too-long"),
        pytest.param("abc123", id="letters"),
        pytest.param("+389 71-ABV-123", id="letters-with-formatting"),
    ],
)
def test_contact_invalid_phone(page, phone):
    """
    Што тестираме:
        - Неважечки формат/должина на телефон (прекраток, предолг, со букви).
    Зошто:
        - Телефоните често имаат локални формати; тука проверуваме груба валидација.
    Како:
        1) Пополнуваме валидни полиња, освен телефон кој варира.
        2) Submit.
        3) Очекуваме да НЕ се појави success (timeout).
    Очекување:
        - Нема success alert.
    """
    main = MainPage(page)
    main.goto_contact()

    _submit(main, {"phone": phone})
    with pytest.raises(PlaywrightTimeoutError):
        page.wait_for_selector("h3:has-text('Thanks for getting in touch')", timeout=5000)


# ====================== SUBJECT / MESSAGE LENGTHS =============================

@pytest.mark.contact
@pytest.mark.parametrize(
    "subject,message,should_pass",
    [
        pytest.param("ab", "ова е доволно долга порака " * 3, False, id="subject-too-short"),
        pytest.param("Тема валидна", "кратко", False, id="message-too-short"),
        pytest.param("Валидна тема" * 3, "валидна порака со доволна должина", True, id="both-valid"),
    ],
)
def test_contact_subject_message_lengths(page, subject, message, should_pass):
    """
    Што тестираме:
        - Гранични случаи за должина на subject и description.
    Зошто:
        - Дизајнот обично бара минимална должина за да се избегнат празни/безвредни пораки.
    Како:
        1) Пополнуваме валидни полиња со варијации за subject/description.
        2) Submit.
        3) Ако should_pass=True → success; инаку → timeout.
    Очекување:
        - Поведение согласно `should_pass`.
    """
    main = MainPage(page)
    main.goto_contact()

    _submit(main, {"subject": subject, "description": message})

    if should_pass:
        txt = main.wait_success_contact(timeout=20000)
        assert "Thanks for getting in touch" in txt
    else:
        with pytest.raises(PlaywrightTimeoutError):
            page.wait_for_selector("h3:has-text('Thanks for getting in touch')", timeout=5000)


# ============================== EMPTY / REQUIRED ==============================

@pytest.mark.contact
def test_contact_empty_fields(page):
    """
    Што тестираме:
        - Сабмитирање без да се пополни било што.
    Зошто:
        - Очекувано е формата да не се прифати кога сè е празно.
    Како:
        1) Одиме на /#/contact.
        2) Submit веднаш.
        3) Чекаме success → очекуваме timeout (да НE се појави).
    Очекување:
        - Нема success alert.
    """
    main = MainPage(page)
    main.goto_contact()

    main.submit_contact_form()
    with pytest.raises(PlaywrightTimeoutError):
        page.wait_for_selector("h3:has-text('Thanks for getting in touch')", timeout=5000)


@pytest.mark.contact
@pytest.mark.parametrize(
    "missing_field",
    ["name", "email", "phone", "subject", "description"],
    ids=["no-name", "no-email", "no-phone", "no-subject", "no-description"],
)
def test_contact_required_field_missing(page, missing_field):
    """
    Што тестираме:
        - Секое задолжително поле поединечно празно (останатите валидни).
    Зошто:
        - Да осигуриме дека секое поле е навистина задолжително од UI перспектива.
    Како:
        1) Креираме копија од VALID.
        2) Го празниме само `missing_field`.
        3) Submit.
        4) Очекуваме да НЕ се појави success (timeout).
    Очекување:
        - Нема success alert.
    """
    main = MainPage(page)
    main.goto_contact()

    data = VALID.copy()
    data[missing_field] = ""
    _submit(main, data)

    with pytest.raises(PlaywrightTimeoutError):
        page.wait_for_selector("h3:has-text('Thanks for getting in touch')", timeout=5000)


# ============================== ROBUSTNESS ====================================

@pytest.mark.contact
def test_contact_multiple_fast_submits(page):
    """
    Што тестираме:
        - Брзи два клика на Submit по ред (анти-спам, двоклик).
    Зошто:
        - Корисниците често двојно кликаат од нетрпение.
          Не сакаме двојни пораки или двојно создавање записи.
    Како:
        1) Submit со валидни податоци.
        2) Кратка пауза (DOM стабилизација).
        3) Обид за уште еден Submit → може да фрли Timeout бидејќи копчето се детачира.
        4) На крај проверуваме дека има САМО една success порака.
    Очекување:
        - Не се случува двојна поднесена форма; success картичката е единствена.
    """
    main = MainPage(page)
    main.goto_contact()

    _submit(main)
    page.wait_for_timeout(120)  # кратко време за DOM промена (success картичка)

    try:
        main.submit_contact_form()
    except PlaywrightTimeoutError:
        # ОК: копчето се менува/исчезнува по првиот submit.
        pass

    success = page.locator("h3:has-text('Thanks for getting in touch')")
    success.first.wait_for(timeout=20000)
    assert success.count() == 1


@pytest.mark.contact
def test_contact_trim_whitespace(page):
    """
    Што тестираме:
        - Внесување со празни места пред/по вредностите (leading/trailing spaces)
          и проверка дали формата сепак минува (често системите го 'trim'-аат внесот).
    Зошто:
        - Реални корисници неретко copy/paste-ираат и оставаат празни места.
    Како:
        1) Во секое поле ставаме валидна вредност со дополнителни spaces.
        2) Submit.
        3) Чекаме success.
    Очекување:
        - Success alert видлив.
    """
    main = MainPage(page)
    main.goto_contact()

    _submit(
        main,
        {
            "name": "   Мила Тестова   ",
            "email": "   mila.tester@example.com   ",
            "phone": "  +38971234567  ",
            "subject": "   Тест trim   ",
            "description": "   Порака со празни места околу текстот.   ",
        },
    )
    txt = main.wait_success_contact(timeout=20000)
    assert "Thanks for getting in touch" in txt


@pytest.mark.contact
def test_contact_description_xss_alert_not_triggered(page):
    """
    Што тестираме:
        - Основна безбедносна проверка за XSS: внесување на <script>alert('XSS')</script>
          во текстуалното поле 'description'.
    Зошто:
        - Иако ова е UI ниво, сакаме да се увериме дека barем не се крева JS alert
          (односно дека содржината е ескејпирана или игнорирана на клиентска страна).
    Како:
        1) Слушаме `page.on("dialog", ...)` за евентуален alert/confirm/prompt.
        2) Submit со опасна содржина.
        3) Кратко чекаме (1.5s) да видиме дали ќе се крене дијалог.
    Очекување:
        - НИЕДЕН дијалог да не се појави (len(dialogs) == 0).
    Забелешки:
        - Ова не е целосен security тест; за backend XSS треба API/интеграциони проверки.
    """
    main = MainPage(page)
    main.goto_contact()

    dialogs = []

    def _on_dialog(d):
        dialogs.append(d)
        d.dismiss()

    page.on("dialog", _on_dialog)

    _submit(main, {"description": '<script>alert("XSS")</script> Ова е текст по скриптата.'})

    # кратко чекање за евентуален дијалог
    page.wait_for_timeout(1500)
    assert len(dialogs) == 0, "Се појави JS alert → можен XSS!"
