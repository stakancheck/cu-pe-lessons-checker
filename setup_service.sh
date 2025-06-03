#!/bin/bash

# Проверяем, запущен ли скрипт с правами root
if [ "$EUID" -ne 0 ]; then 
    echo "Пожалуйста, запустите скрипт с правами root (sudo)"
    exit 1
fi

# Запрашиваем информацию у пользователя
read -p "Введите имя пользователя, от которого будет запускаться бот: " USERNAME
read -p "Введите полный путь к директории с ботом: " BOT_PATH
read -p "Введите полный путь к виртуальному окружению: " VENV_PATH

# Создаем временный файл сервиса
cat > /tmp/pe-bot.service << EOL
[Unit]
Description=Physical Education Attendance Bot
After=network.target

[Service]
Type=simple
User=$USERNAME
WorkingDirectory=$BOT_PATH
Environment=PYTHONPATH=$BOT_PATH
ExecStart=$VENV_PATH/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Копируем файл сервиса в systemd
cp /tmp/pe-bot.service /etc/systemd/system/

# Перезагружаем конфигурацию systemd
systemctl daemon-reload

# Включаем автозапуск сервиса
systemctl enable pe-bot.service

# Запускаем сервис
systemctl start pe-bot.service

# Проверяем статус
systemctl status pe-bot.service

echo "Установка завершена!"
echo "Для управления сервисом используйте команды:"
echo "  sudo systemctl start pe-bot.service    # Запустить бота"
echo "  sudo systemctl stop pe-bot.service     # Остановить бота"
echo "  sudo systemctl restart pe-bot.service  # Перезапустить бота"
echo "  sudo systemctl status pe-bot.service   # Проверить статус"
echo "  sudo journalctl -u pe-bot.service      # Посмотреть логи" 