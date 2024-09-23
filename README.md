# ldap_configuration

1. **Клонирование репозитория:**

```bash
git clone https://github.com/your_username/LAM_LDAP.git
cd LAM_LDAP
```
2. **Установка зависимостей:**

```bash
pip install -r lpad_php/requirements.txt
```

3. **Настройка переменного окружения находится в файле ldap_server.env:**

```env
LDAP_SERVER=ldap://openldap:389
```

4. **Запуск Docker-контейнеров:**

```bash
docker-compose up -d
```

**Порт приложения Web-app - 5010:**

```bash
http://localhost:5010
```

**Порт phpLDAPadmin - 8081:**
```bash
http://localhost:8081
```
