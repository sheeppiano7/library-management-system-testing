import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

class LibraryPage:
    def __init__(self, driver, base):
        self.driver, self.base = driver, base
        self.wait = WebDriverWait(driver, 10)

    def open(self, path):
        self.driver.get(self.base + path)
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        return self

    def fill(self, name, value):
        element = self.wait.until(EC.visibility_of_element_located((By.NAME, name)))
        element.clear()
        element.send_keys(str(value))
        return self

    def select(self, name, value):
        Select(self.driver.find_element(By.NAME, name)).select_by_value(str(value))
        return self

    def submit(self):
        old = self.driver.find_element(By.TAG_NAME, 'body')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        self.wait.until(lambda d: d.find_element(By.TAG_NAME, 'body').id != old.id)
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        return self

    def login(self, role, password=None):
        env_name = 'BOOK_' + role.upper() + '_PASSWORD'
        value = password or os.environ.get(env_name)
        if not value:
            raise RuntimeError('Set '+env_name+' for UI tests')
        return self.open('/login').fill('username',role).fill('password',value).submit()

    @property
    def text(self):
        return self.driver.find_element(By.TAG_NAME, 'body').text

    def borrow(self, book_id, reader_id):
        return self.open('/borrows/add').select('book_id',book_id).select('reader_id',reader_id).submit()
