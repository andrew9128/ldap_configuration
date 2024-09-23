from flask import Flask, request, render_template, send_file, redirect, url_for
import pandas as pd
from ldap3 import Server, Connection, ALL
import random
import string
import os

app = Flask(__name__)

LDAP_SERVER = os.getenv('LDAP_SERVER')

def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def check_and_create_ou(conn, ou_dn):
    if not conn.search(ou_dn, '(objectClass=organizationalUnit)'):
        ou_attrs = {
            'objectClass': ['organizationalUnit'],
            'ou': ou_dn.split(',')[0].split('=')[1]
        }
        conn.add(ou_dn, attributes=ou_attrs)

def create_user(conn, username, password, group):
    gid_map = {
        'ИКТК-11': 1011,
        'ИКТК-12': 1012,
        'ИКТК-03': 1003,
    }
    gid_number = gid_map.get(group, 1000)
    uid_number = random.randint(10000, 99999)
    home_directory = f"/home/{username}"

    dn = f"cn={username},ou=users,dc=alibnr,dc=com"
    attrs = {
        'objectClass': ['inetOrgPerson', 'posixAccount', 'top'],
        'cn': username,
        'sn': username,
        'uid': username,
        'userPassword': password,
        'gidNumber': gid_number,
        'uidNumber': uid_number,
        'homeDirectory': home_directory
    }
    
    if not conn.add(dn, attributes=attrs):
        print(f"Error adding user {username}: {conn.result}")

@app.route('/')
def index():
    return render_template('auth.html')

@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/upload', methods=['POST'])
def upload():
    ldap_user = request.form.get('ldap_user')
    ldap_password = request.form.get('ldap_password')
    if not ldap_user or not ldap_password:
        return 'LDAP логин и пароль обязательны', 401

    file = request.files.get('file')
 
    if not file or not file.filename.endswith('.xlsx'):
        return 'Неправильный формат файла. Требуется .xlsx', 401

    try:
        df = pd.read_excel(file)
    except Exception as e:
        return f'Ошибка при открытии файла: {e}', 400

    try:
        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=f'cn={ldap_user},dc=alibnr,dc=com', password=ldap_password, auto_bind=True)
    except Exception as e:
        if 'invalidCredentials' in str(e):
            return redirect(url_for('error'))
        return f'Ошибка подключения к LDAP: {e}', 401

    try:
        required_columns = ['ФИО', 'номер зачетки', 'группа']
        if not all(column in df.columns for column in required_columns):
            return 'Excel-файл не содержит обязательные столбцы', 400

        check_and_create_ou(conn, 'ou=users,dc=alibnr,dc=com')

        output = []
        for index, row in df.iterrows():
            username = row['номер зачетки']
            password = generate_password()
            group = row['группа']
            create_user(conn, username, password, group)
            output.append({'username': username, 'password': password})

        output_df = pd.DataFrame(output)
        output_file = 'output.csv'
        output_df.to_csv(output_file, index=False)

        conn.unbind()

        return send_file(output_file, as_attachment=True)

    except Exception as e:
        return f'Произошла ошибка: {e}', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)
