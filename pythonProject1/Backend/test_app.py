import unittest
from Backend.app import app
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import app
import time
import psycopg2


class FlaskAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Запуск Flask-приложения в тестовом режиме
        app.config['TESTING'] = True
        cls.app = app.test_client()
        cls.app_context = app.app_context()
        cls.app_context.push()

        # Настройка Selenium WebDriver (используем Chrome)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Для запуска без GUI
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(10)
        cls.base_url = "http://localhost:5000"

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        cls.app_context.pop()

    def test_home_page(self):
        self.driver.get(self.base_url)
        self.assertIn("Добро пожаловать на наш сайт для просмотра курсов!", self.driver.page_source)


        # Проверка наличия навигационных ссылок
        nav_links = self.driver.find_elements(By.TAG_NAME, 'a')
        self.assertEqual(len(nav_links), 3)

        # Проверка корректности ссылки "О нас"
        about_link = self.driver.find_element(By.LINK_TEXT, 'О нас')
        about_link.click()
        self.assertIn("О нашем сайте", self.driver.page_source)

    def test_login_functionality(self):
        self.driver.get(f"{self.base_url}/login")

        # Находим элементы формы
        username_field = self.driver.find_element(By.ID, 'username')
        password_field = self.driver.find_element(By.ID, 'password')
        submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')

        # Тест с неверными учетными данными
        username_field.send_keys('wrong_user')
        password_field.send_keys('wrong_pass')
        submit_button.click()

        # Проверяем сообщение об ошибке
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        self.assertIn("Неверное имя пользователя или пароль", self.driver.page_source)

        # Возвращаемся на страницу входа
        self.driver.get(f"{self.base_url}/login")

        # Тест с верными учетными данными
        username_field = self.driver.find_element(By.ID, 'username')
        password_field = self.driver.find_element(By.ID, 'password')
        submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')

        username_field.send_keys('admin')
        password_field.send_keys('password123')
        submit_button.click()

        # Проверяем успешный вход
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        self.assertIn("Вы вошли как: admin", self.driver.page_source.replace("<strong>", "").replace("</strong>", ""))

    def test_navigation(self):
        self.driver.get(self.base_url)

        # Переход на страницу "О нас"
        about_link = self.driver.find_element(By.LINK_TEXT, 'О нас')
        about_link.click()
        self.assertIn("О нашем сайте", self.driver.page_source)

        # Возврат на главную страницу
        home_link = self.driver.find_element(By.LINK_TEXT, 'Вернуться на главную')
        home_link.click()
        self.assertIn("Добро пожаловать на наш сайт для просмотра курсов!", self.driver.page_source)


class CourseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

        # Соединение с базой данных для тестов
        self.conn = psycopg2.connect(
            host='localhost',
            database='courses',
            user='postgres',
            password='123'
        )
        self.cur = self.conn.cursor()

    def tearDown(self):
        # Очищаем таблицу после каждого теста
        self.cur.execute('DELETE FROM courses;')
        self.conn.commit()
        self.cur.close()
        self.conn.close()

    def test_add_course(self):
        response = self.client.post('/courses', json={
            "name": "Python Basics",
            "description": "Learn Python"
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'Python Basics')

    def test_get_courses(self):
        self.client.post('/courses', json={
            "name": "Python Basics",
            "description": "Learn Python"
        })
        response = self.client.get('/courses')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreater(len(data), 0)

    def test_delete_course(self):
        response = self.client.post('/courses', json={
            "name": "Python Basics",
            "description": "Learn Python"
        })
        course_id = response.get_json()['id']

        response = self.client.delete(f'/courses/{course_id}')
        self.assertEqual(response.status_code, 204)

        response = self.client.get(f'/courses/{course_id}')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
