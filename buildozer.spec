name: Build APK
on: push

jobs:
  build:
    runs-on: ubuntu-22.04 # Используем конкретную версию системы
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          sudo apt update
          sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
          pip3 install --user --upgrade buildozer cython==0.29.33 virtualenv

      - name: Build with Buildozer
        run: |
          export PATH=$PATH:$HOME/.local/bin
          # Генерируем конфиг если его нет, или используем твой
          buildozer android debug
        continue-on-error: false

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: my-tetris-app
          path: bin/*.apk
