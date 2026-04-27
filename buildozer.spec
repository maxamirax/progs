[app]

# (str) Название твоего приложения
title = My Tetris Game

# (str) Имя пакета (без пробелов)
package.name = mytetris

# (str) Домен (обычно org.test или твой ник)
package.domain = org.test

# (str) Где лежит основной код (точка означает текущую папку)
source.dir = .

# (list) Какие файлы включать в APK
source.include_exts = py,png,jpg,kv,atlas

# (str) Версия приложения
version = 0.1

# (list) Библиотеки, от которых зависит игра
# ВАЖНО: Указываем конкретную версию Kivy для стабильности
requirements = python3,kivy==2.3.0

# (str) Ориентация экрана (портретная для Тетриса)
orientation = portrait

# (bool) Фулскрин режим
fullscreen = 1

# (list) Архитектуры процессоров (для современных Android)
android.archs = arm64-v8a, armeabi-v7a

# (int) Минимальная версия Android (21 — это Android 5.0)
android.minapi = 21

# (int) Целевая версия Android (33 или 34)
android.sdk = 33

# (bool) Пропускать ли установку зависимостей (нет)
android.skip_setup = False

# (bool) Принимать ли лицензии SDK автоматически
android.accept_sdk_license = True

# (str) Имя точки входа (твой файл должен называться именно main.py)
python_fallback = python3

[buildozer]
# (int) Уровень логов (2 — самый подробный, если что-то пойдет не так)
log_level = 2

# (int) Пауза перед сборкой (на всякий случай)
warn_on_root = 1
