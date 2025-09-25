# pages/main_page.py
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://automationintesting.online"


class MainPage:
    def __init__(self, page: Page):
        self.page = page

        # ---------------- CONTACT ----------------
        self.name_input = self.page.locator("#name")
        self.email_input = self.page.locator("#email")
        self.phone_input = self.page.locator("#phone")
        self.subject_input = self.page.locator("#subject")
        self.description_input = self.page.locator("#description")
        self.submit_button = self.page.locator("#contact button:has-text('Submit')")
        self.success_alert = self.page.locator("h3:has-text('Thanks for getting in touch')")

        # ---------------- LOGIN ----------------
        self.login_username_input = self.page.locator("#username")
        self.login_password_input = self.page.locator("#password")
        self.login_button = self.page.locator("button[type='submit']")

        # ---------------- NAVBAR / NAVIGATION ----------------
        self.brand_link   = self.page.get_by_role("link", name="Shady Meadows B&B")
        self.nav_rooms    = self.page.get_by_role("link", name="Rooms")
        self.nav_booking  = self.page.get_by_role("link", name="Booking")
        self.nav_amen     = self.page.get_by_role("link", name="Amenities")
        self.nav_location = self.page.get_by_role("link", name="Location")
        self.nav_contact  = self.page.get_by_role("link", name="Contact")
        self.nav_admin    = self.page.get_by_role("link", name="Admin")
        # hamburger (се појавува на мобилен)
        self.nav_toggler  = self.page.locator("button.navbar-toggler, button:has(svg)")

    # ============================ NAVIGATION ============================

    def goto_home(self) -> None:
        self.page.goto(f"{BASE_URL}")
        self.page.wait_for_load_state("domcontentloaded")

    def goto_booking(self) -> None:
        self.page.goto(f"{BASE_URL}/#/booking")
        self.page.wait_for_load_state("domcontentloaded")

    def goto_contact(self) -> None:
        self.page.goto(f"{BASE_URL}/#/contact")
        self.page.wait_for_load_state("domcontentloaded")

    def goto_admin(self) -> None:
        self.page.goto(f"{BASE_URL}/admin")
        self.page.wait_for_load_state("domcontentloaded")

    def open_nav(self, item: str) -> None:
        """Click на линк од горното мени по име ('Rooms','Booking','Amenities','Location','Contact','Admin')."""
        mapping = {
            "Rooms": self.nav_rooms,
            "Booking": self.nav_booking,
            "Amenities": self.nav_amen,
            "Location": self.nav_location,
            "Contact": self.nav_contact,
            "Admin": self.nav_admin,
        }
        loc = mapping[item]
        # ако сме на мал viewport — отвори хамбургер
        try:
            if self.nav_toggler.is_visible():
                self.nav_toggler.click()
        except Exception:
            pass
        loc.click()

    def wait_any(self, selectors: list[str], timeout: int = 15000) -> None:
        """Чека првиот што ќе се појави од група селектори (робусно за SPA/различни наслови)."""
        last = None
        slice_timeout = max(int(timeout / max(len(selectors), 1)), 2000)
        for s in selectors:
            try:
                self.page.locator(s).first.wait_for(timeout=slice_timeout, state="visible")
                return
            except Exception as e:
                last = e
        raise RuntimeError(f"None of expected selectors appeared. Last: {last}")

    # ============================= CONTACT =============================

    def fill_contact_form(self, name: str, email: str, phone: str, subject: str, description: str) -> None:
        self.name_input.fill(name)
        self.email_input.fill(email)
        self.phone_input.fill(phone)
        self.subject_input.fill(subject)
        self.description_input.fill(description)

    def submit_contact_form(self) -> None:
        self.submit_button.click()

    def wait_success_contact(self, timeout: int = 20000) -> str:
        self.success_alert.wait_for(state="visible", timeout=timeout)
        return self.success_alert.inner_text()

    # ============================== LOGIN ==============================

    def login(self, username: str, password: str) -> None:
        self.login_username_input.fill(username)
        self.login_password_input.fill(password)
        self.login_button.click()

    # ============================ BOOKING FLOW =========================
    # Ако ги користиш booking тестовите – остави ги следниве методи.
    # Ако не – можеш да ги игнорираш. (Ги вклучувам за комплетност.)

    def _get_check_inputs(self):
        wrapper = self.page.locator("section#booking form").first
        inputs = wrapper.locator("input.form-control")
        inputs.first.wait_for(timeout=15000)
        return inputs.nth(0), inputs.nth(1)

    def set_dates(self, checkin_ddmmyyyy: str, checkout_ddmmyyyy: str) -> None:
        ci, co = self._get_check_inputs()
        ci.click()
        ci.fill(checkin_ddmmyyyy)
        co.click()
        co.fill(checkout_ddmmyyyy)

    def click_check_availability(self) -> None:
        self.page.locator("section#booking button:has-text('Check Availability')").click()

    def _wait_rooms_section(self, timeout: int = 30000) -> None:
        try:
            self.page.get_by_role("heading", name="Our Rooms").first.wait_for(timeout=timeout)
        except Exception:
            self.page.locator("section#rooms").first.wait_for(timeout=timeout)
        self.page.locator("section#rooms").first.scroll_into_view_if_needed()

    def click_first_book_now(self, timeout: int = 30000) -> None:
        self._wait_rooms_section(timeout=timeout)
        book_now = self.page.locator(
            "section#rooms a.btn.btn-primary:has-text('Book now'), "
            "section#rooms a:has-text('Book now'), "
            "a.btn.btn-primary:has-text('Book now'), "
            "a:has-text('Book now')"
        ).first
        book_now.wait_for(state="visible", timeout=timeout)
        book_now.scroll_into_view_if_needed()
        book_now.click()
        self.page.wait_for_url("**/reservation/**", timeout=timeout)

    def maybe_click_sidebar_reserve_now(self, timeout: int = 15000) -> None:
        if self.page.locator("#doReservation").first.is_visible(timeout=1000):
            return
        sidebar_reserve = self.page.locator("button:has-text('Reserve Now')").first
        sidebar_reserve.wait_for(state="visible", timeout=timeout)
        sidebar_reserve.scroll_into_view_if_needed()
        sidebar_reserve.click()
        self.page.locator("#doReservation").wait_for(timeout=timeout)

    @property
    def firstname_input(self):
        return self.page.locator("input[name='firstname'], input.room-firstname")

    @property
    def lastname_input(self):
        return self.page.locator("input[name='lastname'], input.room-lastname")

    @property
    def booking_email_input(self):
        return self.page.locator("input[name='email'], input.room-email")

    @property
    def booking_phone_input(self):
        return self.page.locator("input[name='phone'], input.room-phone")

    def wait_booking_form(self, timeout: int = 15000) -> None:
        self.firstname_input.first.wait_for(timeout=timeout)
        self.lastname_input.first.wait_for(timeout=timeout)
        self.booking_email_input.first.wait_for(timeout=timeout)
        self.booking_phone_input.first.wait_for(timeout=timeout)

    def fill_booking_form(self, firstname: str, lastname: str, email: str, phone: str) -> None:
        self.firstname_input.fill(firstname)
        self.lastname_input.fill(lastname)
        self.booking_email_input.fill(email)
        self.booking_phone_input.fill(phone)

    def click_final_reserve(self, timeout: int = 20000) -> None:
        self.page.locator("#doReservation").wait_for(timeout=timeout)
        self.page.locator("#doReservation").scroll_into_view_if_needed()
        self.page.locator("#doReservation").click()

    def wait_booking_confirmed(self, timeout: int = 25000) -> None:
        self.page.get_by_role("heading", name="Booking Confirmed").first.wait_for(timeout=timeout)
