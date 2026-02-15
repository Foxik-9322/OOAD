# Простая логика для курсовой работы без переусложнения JWT
def verify_user(username, password):
	# В реальном проекте здесь проверка хеша пароля в БД
	users = {
		"admin": {"password": "admin", "role": "admin", "full_name": "Главный Администратор"},
		"user": {"password": "user", "role": "manager", "full_name": "Сменный Менеджер"}
	}
	if username in users and users[username]["password"] == password:
		return users[username]
	return None