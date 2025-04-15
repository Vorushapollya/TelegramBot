# TelegramBot

## CI/CD настройка

Проект настроен с использованием GitHub Actions для автоматической интеграции и развертывания.

### Как это работает

1. **Continuous Integration (CI)**
   - При каждом пуше в ветки `main` или `master`
   - При каждом pull request в эти ветки
   - Запускаются тесты и проверка кода с помощью flake8

2. **Continuous Deployment (CD)**
   - При успешном прохождении CI на ветках `main` или `master`
   - Автоматическая сборка Docker образа
   - Публикация образа в Docker Hub

### Настройка секретов

Для работы CI/CD необходимо добавить следующие секреты в настройках репозитория GitHub:

1. `DOCKER_HUB_USERNAME` - имя пользователя Docker Hub
2. `DOCKER_HUB_TOKEN` - токен доступа Docker Hub

### Локальный запуск Docker образа

```bash
docker pull ваш-username/tg-bot:latest
docker run -d ваш-username/tg-bot:latest
```