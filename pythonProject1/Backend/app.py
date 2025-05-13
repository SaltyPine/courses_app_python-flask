import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for, session

app = Flask(__name__)

app.secret_key = '123'

def get_db_connection():
    connection = psycopg2.connect(
        host='localhost',
        database='courses',
        user='postgres',
        password='123'
    )
    return connection

users = {
    'admin': 'password123',
    'user1': 'mypassword'
}


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username] == password:
            session['username'] = username  # сохраняем пользователя в сессию
            return redirect(url_for('courses_page'))
        else:
            return 'Неверное имя пользователя или пароль', 401

    return render_template('login.html')


@app.route('/courses_page', methods=['GET', 'POST'])
def courses_page():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    if request.method == 'POST':
        if username != 'admin':
            return 'Доступ запрещен', 403

        name = request.form['name']
        description = request.form['description']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO courses (name, description) VALUES (%s, %s);', (name, description))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return f'Ошибка: {e}', 500
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('courses_page'))

    # Обработка GET с фильтрацией и пагинацией
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_name = request.args.get('filter_name', '')
    filter_description = request.args.get('filter_description', '')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT id, name, description FROM courses WHERE name ILIKE %s AND description ILIKE %s LIMIT %s OFFSET %s;',
        ('%' + filter_name + '%', '%' + filter_description + '%', per_page, (page - 1) * per_page)
    )
    rows = cur.fetchall()

    cur.execute(
        'SELECT COUNT(*) FROM courses WHERE name ILIKE %s AND description ILIKE %s;',
        ('%' + filter_name + '%', '%' + filter_description + '%')
    )
    total_courses = cur.fetchone()[0]
    total_pages = (total_courses // per_page) + (1 if total_courses % per_page > 0 else 0)

    cur.close()
    conn.close()

    return render_template('courses.html',
                           username=username,
                           courses=[{'id': r[0], 'name': r[1], 'description': r[2]} for r in rows],
                           page=page,
                           total_pages=total_pages)


@app.route('/courses/<int:id>/delete', methods=['POST'])
def delete_course(id):
    if session.get('username') != 'admin':
        return 'Доступ запрещён', 403

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM courses WHERE id = %s;', (id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f'Ошибка при удалении: {e}', 500
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('courses_page'))


@app.route('/courses/<int:id>/edit', methods=['GET', 'POST'])
def edit_course_page(id):
    if session.get('username') != 'admin':
        return 'Доступ запрещён', 403

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        try:
            cur.execute('UPDATE courses SET name = %s, description = %s WHERE id = %s;', (name, description, id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return f'Ошибка при обновлении: {e}', 500
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('courses_page'))

    # GET-запрос — показать форму редактирования
    cur.execute('SELECT id, name, description FROM courses WHERE id = %s;', (id,))
    course = cur.fetchone()
    cur.close()
    conn.close()

    if not course:
        return 'Курс не найден', 404

    return render_template('edit_course.html', course={
        'id': course[0],
        'name': course[1],
        'description': course[2]
    })


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/courses', methods=['POST', 'GET'])
def courses_handler():
    if request.method == 'POST':
        course_data = request.get_json()
        name = course_data['name']
        description = course_data['description']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO courses (name, description) VALUES (%s, %s) RETURNING id;', (name, description))
            course_id = cur.fetchone()[0]
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")
            return jsonify({'error': 'Failed to add course'}), 500
        finally:
            cur.close()
            conn.close()

        return jsonify({'id': course_id, 'name': name, 'description': description}), 201

    # Пагинация и фильтрация
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    filter_name = request.args.get('filter_name', '')
    filter_description = request.args.get('filter_description', '')

    conn = get_db_connection()
    cur = conn.cursor()

    # Применяем фильтрацию
    query = 'SELECT id, name, description FROM courses WHERE name ILIKE %s AND description ILIKE %s LIMIT %s OFFSET %s'
    cur.execute(query, ('%' + filter_name + '%', '%' + filter_description + '%', per_page, (page - 1) * per_page))
    courses = cur.fetchall()

    # Получаем общее количество курсов для пагинации
    cur.execute('SELECT COUNT(*) FROM courses WHERE name ILIKE %s AND description ILIKE %s', ('%' + filter_name + '%', '%' + filter_description + '%'))
    total_courses = cur.fetchone()[0]
    total_pages = (total_courses // per_page) + (1 if total_courses % per_page > 0 else 0)

    cur.close()
    conn.close()

    return jsonify({
        'courses': [{'id': c[0], 'name': c[1], 'description': c[2]} for c in courses],
        'total_pages': total_pages  # Возвращаем количество страниц для пагинации
    })


@app.route('/courses/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def course_handler(id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT id, name, description FROM courses WHERE id = %s;', (id,))
    course = cur.fetchone()

    if not course:
        cur.close()
        conn.close()
        return '', 404

    if request.method == 'GET':
        cur.close()
        conn.close()
        return jsonify({'id': course[0], 'name': course[1], 'description': course[2]})

    if request.method == 'PUT':
        course_data = request.get_json()
        name = course_data['name']
        description = course_data['description']

        try:
            cur.execute('UPDATE courses SET name = %s, description = %s WHERE id = %s;',
                        (name, description, id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")
            return jsonify({'error': 'Failed to update course'}), 500
        finally:
            cur.close()
            conn.close()

        return jsonify({'id': id, 'name': name, 'description': description})

    if request.method == 'DELETE':
        try:
            cur.execute('DELETE FROM courses WHERE id = %s;', (id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")
            return jsonify({'error': 'Failed to delete course'}), 500
        finally:
            cur.close()
            conn.close()

        return '', 204


if __name__ == '__main__':
    app.run(debug=True)


#http://127.0.0.1:5000/courses?page=2&per_page=5&filter_name=Python
