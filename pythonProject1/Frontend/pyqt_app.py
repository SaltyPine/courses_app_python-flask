import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QLineEdit

class CourseApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Course Management')
        self.setGeometry(100, 100, 600, 400)

        # Инициализация данных пагинации
        self.page = 1
        self.per_page = 10
        self.total_pages = 1

        # Главный Layout
        self.layout = QVBoxLayout()

        # Таблица для отображения курсов
        self.course_table = QTableWidget(self)
        self.course_table.setColumnCount(3)
        self.course_table.setHorizontalHeaderLabels(['ID', 'Name', 'Description'])
        self.layout.addWidget(self.course_table)

        # Контейнер для кнопок и полей ввода
        self.button_layout = QHBoxLayout()

        # Поля для ввода данных
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText('Enter course name')
        self.description_input = QLineEdit(self)
        self.description_input.setPlaceholderText('Enter course description')

        # Поля для фильтрации
        self.filter_name_input = QLineEdit(self)
        self.filter_name_input.setPlaceholderText('Filter by name')
        self.filter_description_input = QLineEdit(self)
        self.filter_description_input.setPlaceholderText('Filter by description')

        # Кнопка для добавления курса
        self.add_button = QPushButton('Add Course', self)
        self.add_button.clicked.connect(self.add_course)

        # Кнопка для фильтрации курсов
        self.filter_button = QPushButton('Filter', self)
        self.filter_button.clicked.connect(self.filter_courses)

        # Кнопки пагинации
        self.prev_button = QPushButton('Previous', self)
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button = QPushButton('Next', self)
        self.next_button.clicked.connect(self.next_page)

        # Добавляем кнопки и поля ввода в layout
        self.button_layout.addWidget(self.name_input)
        self.button_layout.addWidget(self.description_input)
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.filter_name_input)
        self.button_layout.addWidget(self.filter_description_input)
        self.button_layout.addWidget(self.filter_button)
        self.button_layout.addWidget(self.prev_button)
        self.button_layout.addWidget(self.next_button)

        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

        # Загружаем курсы при старте
        self.load_courses()

    def load_courses(self):
        """Загружает все курсы с сервера и отображает их в таблице с пагинацией."""
        filter_name = self.filter_name_input.text()
        filter_description = self.filter_description_input.text()

        # Формирование параметров запроса для пагинации и фильтрации
        params = {
            'page': self.page,
            'per_page': self.per_page,
            'filter_name': filter_name,
            'filter_description': filter_description
        }

        response = requests.get("http://127.0.0.1:5000/courses", params=params)

        if response.status_code == 200:
            data = response.json()

            self.course_table.setRowCount(len(data['courses']))
            for row, course in enumerate(data['courses']):
                self.course_table.setItem(row, 0, QTableWidgetItem(str(course['id'])))
                self.course_table.setItem(row, 1, QTableWidgetItem(course['name']))
                self.course_table.setItem(row, 2, QTableWidgetItem(course['description']))

            # Обновляем информацию о пагинации
            self.total_pages = data.get('total_pages', 1)  # Используем get(), чтобы избежать ошибки при отсутствии поля
            self.update_pagination_buttons()

    def add_course(self):
        """Добавляет новый курс через API."""
        name = self.name_input.text()
        description = self.description_input.text()

        if name and description:
            response = requests.post("http://127.0.0.1:5000/courses", json={
                "name": name,
                "description": description
            })

            if response.status_code == 201:
                self.load_courses()  # Обновляем список курсов
                self.name_input.clear()  # Очищаем поля ввода
                self.description_input.clear()
                print("Course added successfully")
            else:
                print("Failed to add course")
        else:
            print("Please enter both name and description")

    def filter_courses(self):
        """Применяет фильтрацию по имени и описанию."""
        self.page = 1  # Сбросим на первую страницу при фильтрации
        self.load_courses()

    def prev_page(self):
        """Переходит на предыдущую страницу."""
        if self.page > 1:
            self.page -= 1
            self.load_courses()

    def next_page(self):
        """Переходит на следующую страницу."""
        if self.page < self.total_pages:
            self.page += 1
            self.load_courses()

    def update_pagination_buttons(self):
        """Обновляет доступность кнопок пагинации."""
        self.prev_button.setEnabled(self.page > 1)
        self.next_button.setEnabled(self.page < self.total_pages)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CourseApp()
    window.show()
    sys.exit(app.exec_())
