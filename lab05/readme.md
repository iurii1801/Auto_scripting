# Лабораторная работа №5: Ansible playbook для конфигурации сервера

## Цель

Научиться создавать Ansible playbook для автоматизации конфигурации серверов.

---

## Подготовка

Задание выполняется на базе лабораторной работы №4.

Необходимо создать папку `lab05` в репозитории GitHub для хранения всех файлов, связанных с этой лабораторной работой. Должен быть установлен Docker и Docker Compose для выполнения задания. Также должен быть репозиторий с проектом PHP, содержащим модульные тесты, как в лабораторной работе №4.

Скопировать из предыдущей лабораторной работы `lab04` файлы в папку `lab05`.

Задание включает в себя также описание шагов из предыдущих лабораторных работ с пометкой "Повторение".

---

## Ход выполнения работы

### Шаг 0. Подготовка проекта

Для выполнения лабораторной работы необходимо создать папку `lab05`.  
Из предыдущей лабораторной работы №4 нужно скопировать следующие файлы:

- PHP-проект `recipe-book` с модульными тестами;
- файл `composer.json`;
- файл `Jenkinsfile`;
- папка `secrets` с SSH-ключами для Jenkins SSH-агента;
- `docker-compose.yml` и `Dockerfile` из IW04.

Эти файлы будут использованы как основа для настройки новых конвейеров Jenkins и создания Ansible playbook.

### Шаг 1. Установка и настройка Jenkins Controller

Jenkins будет использоваться для управления всеми этапами автоматизации в рамках лабораторной работы.

#### 1.1. Создание файла docker-compose.yaml и сервиса `jenkins-controller`

В файле необходимо описать сервис **`jenkins-controller`** на основе образа `jenkins/jenkins:lts`, с пробросом портов и volume для данных Jenkins.

```yaml
services:
  jenkins-controller:
    image: jenkins/jenkins:lts
    container_name: jenkins-controller
    ports:
      - "9090:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
    restart: unless-stopped

volumes:
  jenkins_home:
```

![image](https://i.imgur.com/MXktSMv.png)

#### 1.2. Запуск контейнера Jenkins Controller

Необходимо перейти в каталог `lab05` и запустить контейнер Jenkins с помощью Docker Compose:

```bash
cd lab05
docker compose up -d
```

![image](https://i.imgur.com/PC40YyZ.png)

После запуска нужно проверить, что контейнер работает:

```bash
docker ps
```

Ожидается, что контейнер **jenkins-controller** находится в статусе `Up`.

![image](https://i.imgur.com/GhBk2Rg.png)

#### 1.3. Первичная настройка Jenkins (Unlock Jenkins)

Необходимо открыть Jenkins в браузере по адресу:

```text
http://localhost:9090
```

При первом запуске Jenkins запрашивает пароль администратора.
Пароль берётся из логов контейнера:

```bash
docker logs jenkins-controller
```

Нужно скопировать значение **initialAdminPassword**, вставить его в поле **Administrator password** и нажать **Continue**.

![image](https://i.imgur.com/dscRVkS.png)

#### 1.4. Установка необходимых плагинов (`Docker`, `Docker Pipeline`, `GitHub`, `SSH Agent`)

После разблокировки Jenkins необходимо пройти мастер настройки и установить плагины.

1. Выбрать вариант настройки плагинов (**Select plugins to install**).

![image](https://i.imgur.com/P7goGv9.png)
![image](https://i.imgur.com/LDZ6Buq.png)

2. После завершения мастера перейти в:

   **Manage Jenkins → Plugins → Available plugins**

3. Найти и установить следующие плагины:

   - **Docker plugin**
   - **Docker Commons Plugin**
   - **Docker Pipeline**
   - **Docker API Plugin**
   - **SSH Agent Plugin**
   - **SSH Build Agents plugin** (при наличии)
   - **GitHub Integration Plugin**
   - **GitHub Branch Source Plugin**

После установки плагинов убедиться, что они отображаются во вкладке **Installed plugins** и помечены как активные.

![image](https://i.imgur.com/zhzyFLQ.png)
![image](https://i.imgur.com/1mIdwgy.png)
![image](https://i.imgur.com/kALvzPR.png)

### Шаг 2. Подготовка SSH-агента

Агент SSH будет использоваться Jenkins для сборки PHP-проекта и запуска модульных тестов по SSH.

#### 2.1 Создание файла `Dockerfile.ssh_agent`

Нужно создать в папке `lab05` файл **`Dockerfile.ssh_agent`** и описать в нём образ SSH-агента.

```dockerfile
# SSH-агент для сборки PHP-проекта
FROM php:8.3-cli

# Устанавливаем SSH-сервер и нужные утилиты
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    git \
    unzip \
    zip \
    rsync \
 && rm -rf /var/lib/apt/lists/*

# Устанавливаем Composer (для установки зависимостей PHP-проекта)
RUN curl -sS https://getcomposer.org/installer | php -- \
    --install-dir=/usr/local/bin --filename=composer

# Создаем пользователя, от имени которого Jenkins будет подключаться
RUN useradd -m -d /home/jenkins -s /bin/bash jenkins

# Готовим SSH
RUN mkdir -p /var/run/sshd

# Копируем публичный ключ в контейнер (ключи уже лежат в папке secrets из lab04)
# jenkins_agent_ssh_key.pub — ПУБЛИЧНЫЙ ключ
COPY secrets/jenkins_agent_ssh_key.pub /home/jenkins/.ssh/authorized_keys

RUN chown -R jenkins:jenkins /home/jenkins/.ssh && \
    chmod 700 /home/jenkins/.ssh && \
    chmod 600 /home/jenkins/.ssh/authorized_keys

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D", "-e"]
```

Этот образ:

- основан на `php:8.3-cli`, чтобы был доступен PHP-CLI;
- устанавливает SSH-сервер и полезные утилиты;
- ставит Composer;
- создаёт пользователя `jenkins`, от имени которого Jenkins будет подключаться по SSH;
- копирует **публичный ключ** из папки `secrets` в `authorized_keys`;
- настраивает права на `.ssh` и запускает `sshd`.

![image](https://i.imgur.com/4ek6I0k.png)

#### 2.2 Подготовка SSH-ключей (повторение из lab04)

Ключи уже перенесены из лабораторной работы №4 в папку `secrets`, но по заданию нужно описать процесс их создания.

Для генерации пары ключей (один раз в lab04) используется команда:

```bash
mkdir -p secrets
ssh-keygen -t ed25519 -f secrets/jenkins_agent_ssh_key -C "jenkins@lab"
```

- `secrets/jenkins_agent_ssh_key` — **приватный** ключ (остаётся на хосте и в Jenkins Credentials).
- `secrets/jenkins_agent_ssh_key.pub` — **публичный** ключ (копируется в контейнер SSH-агента, как указано в Dockerfile).

#### 2.3 Добавление сервиса `ssh-agent` в docker-compose

Теперь нужно добавить сервис **`ssh-agent`** в файл `docker-compose.yaml`.

Файл должен содержать два сервиса: `jenkins-controller` и `ssh-agent`:

```yaml
services:
  jenkins-controller:
    image: jenkins/jenkins:lts
    container_name: jenkins-controller
    ports:
      - "9090:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
    restart: unless-stopped

  ssh-agent:
    build:
      context: .
      dockerfile: Dockerfile.ssh_agent
    container_name: ssh-agent
    ports:
      - "2222:22"
    restart: unless-stopped

volumes:
  jenkins_home:
```

> Важно: порт `2222` на хосте проброшен на порт `22` внутри контейнера SSH-агента. Именно на `localhost:2222` потом будет подключаться Jenkins.

![image](https://i.imgur.com/ccLXwFe.png)

#### 2.4 Сборка образа SSH-агента и запуск контейнеров

Далее нужно:

1. Собрать образ **`ssh-agent`** по новому Dockerfile:

```bash
docker compose build ssh-agent
```

![image](https://i.imgur.com/6tm4sQ7.png)
![image](https://i.imgur.com/yGFQtgX.png)

2. Запустить оба сервиса в фоне:

```bash
docker compose up -d
```

![image](https://i.imgur.com/SeHMWQa.png)

3. Убедиться, что контейнеры запущены и порты проброшены корректно:

```bash
docker ps
```

Ожидаемый результат:

- контейнер **jenkins-controller** в статусе `Up`, порты `9090` и `50000` проброшены;
- контейнер **ssh-agent** в статусе `Up`, порт `2222->22/tcp`.

![image](https://i.imgur.com/mRsFQyQ.png)

### Шаг 3. Создание агента Ansible

Агент Ansible будет использоваться Jenkins для выполнения Ansible playbook, который будет настраивать тестовый сервер.
На этом шаге необходимо создать Docker-образ с Ansible, подготовить SSH-ключи для Jenkins и для подключения к тестовому серверу, а также описать сервис `ansible-agent` в docker-compose.

#### 3.1. Создание файла **`Dockerfile.ansible_agent`**

Необходимо создать файл **`Dockerfile.ansible_agent`** в папке `lab05` и описать в нём образ Ansible-агента на базе Ubuntu 22.04.

Код файла:

```dockerfile
# Ansible-агент на базе Ubuntu
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Устанавливаем SSH-сервер, Python, Ansible и Java
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    python3 \
    python3-pip \
    ansible \
    git \
    openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Создаём пользователя ansible
RUN useradd -m -d /home/ansible -s /bin/bash ansible && \
    mkdir -p /home/ansible/.ssh && \
    chown -R ansible:ansible /home/ansible/.ssh

# Готовим SSH-сервер
RUN mkdir -p /var/run/sshd

# Публичный ключ Jenkins -> Ansible-агент
# jenkins_ansible_ssh_key.pub будет сгенерирован в разделе 3.2
COPY secrets/jenkins_ansible_ssh_key.pub /home/ansible/.ssh/authorized_keys

RUN chown ansible:ansible /home/ansible/.ssh/authorized_keys && \
    chmod 700 /home/ansible/.ssh && \
    chmod 600 /home/ansible/.ssh/authorized_keys

# Ключи Ansible-агента для подключения к тестовому серверу (раздел 3.3)
COPY secrets/ansible_test_ssh_key /home/ansible/.ssh/id_ed25519
COPY secrets/ansible_test_ssh_key.pub /home/ansible/.ssh/id_ed25519.pub

RUN chown ansible:ansible /home/ansible/.ssh/id_ed25519* && \
    chmod 600 /home/ansible/.ssh/id_ed25519

# Папка для будущих настроек Ansible (inventory, ansible.cfg)
RUN mkdir -p /etc/ansible && chown -R ansible:ansible /etc/ansible

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D", "-e"]
```

![image](https://i.imgur.com/QJFH16v.png)

#### 3.2. Генерация SSH-ключей для Jenkins → Ansible-агент

Эти ключи нужны Jenkins, чтобы подключаться к контейнеру ansible-agent через SSH.

Команда:

```bash
ssh-keygen -t ed25519 -f secrets/jenkins_ansible_ssh_key -C "jenkins->ansible-agent"
```

![image](https://i.imgur.com/MxWVSin.png)
![image](https://i.imgur.com/pHxOADG.png)

#### 3.3. Генерация SSH-ключей Ansible-агента → тестовый сервер

Эти ключи будут использоваться внутри контейнера ansible-agent для подключения к будущему тестовому серверу.

Команда:

```bash
ssh-keygen -t ed25519 -f secrets/ansible_test_ssh_key -C "ansible->test-server"
```

![image](https://i.imgur.com/zedGJ6N.png)
![image](https://i.imgur.com/aSaysok.png)

#### 3.4. Добавление сервиса `ansible-agent` в docker-compose

Необходимо добавить новый сервис в файл **docker-compose.yaml**:

```yaml
ansible-agent:
  build:
    context: .
    dockerfile: Dockerfile.ansible_agent
  container_name: ansible-agent
  ports:
    - "2223:22"
  restart: unless-stopped
```

![image](https://i.imgur.com/uDgClXF.png)

#### 3.5. Сборка Ansible-агента

Выполнить:

```bash
docker compose build ansible-agent
```

![image](https://i.imgur.com/Rp2rfse.png)

#### 3.6. Запуск контейнеров и проверка контейнеров

Запускаем все сервисы:

```bash
docker compose up -d
```

проверка контейнеров:

```bash
docker ps
```

Ожидается:

- `jenkins-controller` — running
- `ssh-agent` — running
- `ansible-agent` — running, порт `2223->22`

![image](https://i.imgur.com/NAZmVBA.png)

### Шаг 4. Создание тестового сервера

Тестовый сервер — это отдельный контейнер, на котором будет выполняться Ansible-playbook.
Задача тестового сервера — предоставить окружение, в котором:

- Ansible сможет подключаться по SSH от имени пользователя **ansible**,
- выполнять привилегированные команды (через sudo),
- и производить тестовые изменения.

На этом шаге создаётся Docker-образ тестового сервера, добавляется пользователь, настраивается SSH и пробрасывается порт.

#### 4.1 Создание файла **`Dockerfile.test_server`**

В каталоге `lab05` нужно создать файл **`Dockerfile.test_server`**.

Внутри него описывается тестовый сервер на базе Ubuntu 22.04.

```dockerfile
# Тестовый сервер на базе Ubuntu
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Ставим SSH-сервер и sudo (чтобы Ansible мог выполнять привилегированные задачи)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    sudo \
 && rm -rf /var/lib/apt/lists/*

# Создаём пользователя ansible
RUN useradd -m -d /home/ansible -s /bin/bash ansible && \
    mkdir -p /home/ansible/.ssh && \
    chown -R ansible:ansible /home/ansible/.ssh && \
    echo "ansible ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ansible

# Готовим SSH-сервер
RUN mkdir -p /var/run/sshd

# Подключаем публичный ключ Ansible-агента
COPY secrets/ansible_test_ssh_key.pub /home/ansible/.ssh/authorized_keys

RUN chown ansible:ansible /home/ansible/.ssh/authorized_keys && \
    chmod 700 /home/ansible/.ssh && \
    chmod 600 /home/ansible/.ssh/authorized_keys

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D", "-e"]
```

![image](https://i.imgur.com/GAOzIAR.png)

#### 4.2 Добавление сервиса `test-server` в docker-compose.yaml

В файл `docker-compose.yaml` добавляется новый сервис:

```yaml
test-server:
  build:
    context: .
    dockerfile: Dockerfile.test_server
  container_name: test-server
  ports:
    - "2224:22"
  restart: unless-stopped
```

![image](https://i.imgur.com/VxeJk6T.png)

#### 4.3 Сборка образа тестового сервера

Выполняется сборка:

```bash
docker compose build test-server
```

![image](https://i.imgur.com/T37E9kw.png)

#### 4.4 Запуск всех контейнеров

```bash
docker compose up -d
```

![image](https://i.imgur.com/SAYWR4Y.png)

#### 4.5 Проверка работы контейнеров

```bash
docker ps
```

Ожидаемая картина:

- `jenkins-controller` — Running
- `ssh-agent` — Running
- `ansible-agent` — Running
- `test-server` — Running, порт **2224 → 22**

![image](https://i.imgur.com/ZVZVtmA.png)

### Шаг 5. Создание Ansible playbook для настройки тестового сервера

Далее нужно создать инфраструктура Ansible для автоматической настройки тестового сервера:

- в папке `ansible` необходимо определить инвентарный файл `hosts.ini` с параметрами подключения;
- Необходимо создать playbook `setup_test_server.yml`, который:

  - установит и настроит **Apache2**;
  - установит **PHP** и необходимые расширения;
  - настроит виртуальный хост Apache для PHP-проекта `recipe-book`.

#### 5.1. Создание папки `ansible` и файла `hosts.ini`

В каталоге `lab05` необходимо создать папку `ansible`.

Внутри папки `ansible` необходимо создать файл **`hosts.ini`** со следующим содержимым:

```ini
[test_server]
test-server ansible_host=test-server ansible_port=22 ansible_user=ansible ansible_ssh_private_key_file=/home/ansible/.ssh/id_ed25519 ansible_python_interpreter=/usr/bin/python3
```

Здесь:

- `test_server` — группа хостов Ansible (используется в playbook);
- `test-server` — имя контейнера Docker (из `docker-compose.yaml`);
- `ansible_user=ansible` — пользователь, под которым Ansible подключается по SSH;
- `ansible_ssh_private_key_file=/home/ansible/.ssh/id_ed25519` — путь к приватному ключу, который мы положили в образ `ansible-agent`;
- `ansible_python_interpreter=/usr/bin/python3` — путь к Python 3 на целевой машине.

![image](https://i.imgur.com/0Tgtgkk.png)

#### 5.2. Создание Ansible playbook `setup_test_server.yml`

В той же папке `ansible` необходимо создать файл **`setup_test_server.yml`**, который выполняет все шаги по настройке тестового сервера:

```yaml
---
- name: Setup test server for PHP application
  hosts: test_server
  become: yes
  become_user: root

  vars:
    app_root: /var/www/recipe-book
    app_public: /var/www/recipe-book/public
    server_name: recipe-book.local

  tasks:
    - name: Update APT cache
      ansible.builtin.apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Install Apache2
      ansible.builtin.apt:
        name: apache2
        state: present

    - name: Install PHP and required extensions
      ansible.builtin.apt:
        name:
          - php
          - libapache2-mod-php
          - php-cli
          - php-mbstring
          - php-xml
          - php-mysql
        state: present

    - name: Enable Apache rewrite module
      ansible.builtin.command: a2enmod rewrite
      args:
        warn: false
      notify: Reload Apache

    - name: Create application root directory
      ansible.builtin.file:
        path: "{{ app_root }}"
        state: directory
        owner: www-data
        group: www-data
        mode: "0755"

    - name: Ensure public directory exists
      ansible.builtin.file:
        path: "{{ app_public }}"
        state: directory
        owner: www-data
        group: www-data
        mode: "0755"

    - name: Configure Apache virtual host for recipe-book
      ansible.builtin.copy:
        dest: /etc/apache2/sites-available/recipe-book.conf
        content: |
          <VirtualHost *:80>
              ServerName {{ server_name }}
              DocumentRoot {{ app_public }}

              <Directory {{ app_public }}>
                  AllowOverride All
                  Require all granted
              </Directory>

              ErrorLog ${APACHE_LOG_DIR}/recipe-book_error.log
              CustomLog ${APACHE_LOG_DIR}/recipe-book_access.log combined
          </VirtualHost>
      notify: Reload Apache

    - name: Enable recipe-book site
      ansible.builtin.command: a2ensite recipe-book.conf
      args:
        warn: false
      notify: Reload Apache

    - name: Disable default Apache site
      ansible.builtin.command: a2dissite 000-default.conf
      args:
        warn: false
      ignore_errors: yes
      notify: Reload Apache

    - name: Ensure Apache2 is running and enabled
      ansible.builtin.service:
        name: apache2
        state: started
        enabled: yes

  handlers:
    - name: Reload Apache
      ansible.builtin.service:
        name: apache2
        state: restarted
```

Основные действия playbook:

- обновляет кеш пакетов `apt`;
- ставит Apache2 и расширения PHP, необходимые для работы Laravel-подобного проекта;
- создаёт директории `/var/www/recipe-book` и `/var/www/recipe-book/public`;
- создаёт конфигурацию виртуального хоста `recipe-book.conf` с `ServerName recipe-book.local` и корнем `{{ app_public }}`;
- включает сайт `recipe-book`, отключает дефолтный `000-default.conf`;
- применяет изменения через хэндлер `Reload Apache` и гарантирует, что служба `apache2` запущена и включена в автозапуск.

![image](https://i.imgur.com/XQoFec4.png)
![image](https://i.imgur.com/K6AbF7l.png)
![image](https://i.imgur.com/advbKpL.png)

### Шаг 6. Настройка и запуск Jenkins Pipeline для тестирования PHP-проекта

На этом шаге создаётся Pipeline-задача в Jenkins, которая будет выполнять автоматическую сборку и тестирование PHP-проекта с использованием PHPUnit.
Pipeline запускается на созданном ранее SSH-агенте и использует Jenkinsfile (Groovy Pipeline Script), расположенный в репозитории GitHub.

#### 6.1. Создание нового Pipeline-проекта в Jenkins

1. В интерфейсе Jenkins необходимо нажать **New Item**.
2. Ввести имя задачи, например:
   **`php-build-test`**
3. Выбрать тип задачи **Pipeline**.
4. Нажать **OK**.

![image](https://i.imgur.com/h2OVWkX.png)

#### 6.2. Настройка Pipeline Script From SCM

В разделе **Pipeline → Definition** выбрать:

- **Pipeline script from SCM**
- SCM: **Git**
- Repository URL:
  `https://github.com/iurii1801/Auto_scripting`
- Branches to build:
  `*/lab05`
- Script Path:
  `lab05/pipelines/php_build_and_test_pipeline.groovy`

![image](https://i.imgur.com/BbLK1tW.png)
![image](https://i.imgur.com/8G6oNcK.png)

#### 6.3. Конфигурация Pipeline-файла

Файл `php_build_and_test_pipeline.groovy` загружается Jenkins'ом из GitHub.
Он выполняет:

- клонирование проекта;
- установку зависимостей через Composer;
- запуск PHPUnit тестов;
- архивирование результатов тестирования.

Код `Pipeline`:

```groovy
pipeline {
    agent { label 'ssh-agent' }

    environment {
        REPO_URL    = 'https://github.com/iurii1801/auto_scripting.git'
        REPO_BRANCH = 'lab05'
        PROJECT_DIR = 'lab05/recipe-book'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout project') {
            steps {
                echo "Cloning auto_scripting repository (branch: ${env.REPO_BRANCH})..."
                git branch: "${env.REPO_BRANCH}", url: "${env.REPO_URL}"
            }
        }

        stage('Install Composer dependencies') {
            steps {
                echo "Installing Composer dependencies inside ${env.PROJECT_DIR}..."
                dir("${env.PROJECT_DIR}") {
                    sh '''
                        composer install --no-interaction --prefer-dist --no-progress
                    '''
                }
            }
        }

        stage('Run PHPUnit tests') {
            steps {
                echo "Running PHPUnit tests..."
                dir("${env.PROJECT_DIR}") {
                    sh '''
                        mkdir -p build/logs
                        ./vendor/bin/phpunit \
                          --colors=always \
                          --log-junit build/logs/junit.xml \
                          tests
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "Archiving test reports..."
            archiveArtifacts artifacts: "${env.PROJECT_DIR}/build/logs/**/*.xml", fingerprint: true
            junit "${env.PROJECT_DIR}/build/logs/**/*.xml"
        }

        success {
            echo "Tests passed successfully!"
        }

        failure {
            echo "Tests failed! Check console output and reports."
        }
    }
}
```

![image](https://i.imgur.com/tWusZlI.png)
![image](https://i.imgur.com/SrY4OXJ.png)

#### 6.4. Запуск Pipeline

После сохранения настроек необходимо нажать:

`Build Now`

Процесс сборки включает:

- получение кода из GitHub;
- запуск контейнера ssh-agent;
- установку зависимостей Composer;
- выполнение PHPUnit тестов;
- генерацию отчёта JUnit.

![image](https://i.imgur.com/1pxc7BF.png)
![image](https://i.imgur.com/gu8pL5a.png)
![image](https://i.imgur.com/42Dl3Cb.png)

#### 6.5. Проверка отчётов о тестах

После успешного запуска:

- появится вкладка **Test Results**
- будет доступен артефакт `junit.xml`

![image](https://i.imgur.com/SAiei5j.png)

После выполнения всех этапов:

- Pipeline выполняется без ошибок
- Composer устанавливает зависимости
- PHPUnit запускает тесты
- Отчёт тестирования сохраняется как артефакт
- Jenkins показывает **SUCCESS ✓**

### Шаг 7. Конвейер для настройки тестового сервера с помощью Ansible

На этом шаге создаётся отдельный Jenkins Pipeline, который выполняет автоматическую настройку тестового сервера с помощью Ansible-агента.
Конвейер использует ранее созданный агент **ansible-agent**, подключённый по SSH и успешно запущенный (см. скриншоты подтверждения подключения).

#### 7.1. Создание файла `ansible_setup_pipeline.groovy`

В каталоге `lab05/pipelines/` необходимо создать файл `ansible_setup_pipeline.groovy`

Этот pipeline должен:

1. Клонировать GitHub-репозиторий с Ansible playbook.
2. Запустить выполнение playbook на тестовом сервере через Ansible-агент.

Содержимое файла:

```groovy
pipeline {
    agent { label 'ansible-agent' }

    environment {
        REPO_URL        = 'https://github.com/iurii1801/Auto_scripting.git'
        REPO_BRANCH     = 'lab05'
        ANSIBLE_DIR     = 'lab05/ansible'
        INVENTORY_FILE  = 'hosts.ini'
        PLAYBOOK_FILE   = 'setup_test_server.yml'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {

        stage('Checkout Ansible repo') {
            steps {
                echo "Cloning repository with Ansible playbook (branch: ${env.REPO_BRANCH})..."
                git branch: "${env.REPO_BRANCH}", url: "${env.REPO_URL}"
            }
        }

        stage('Run Ansible playbook') {
            steps {
                echo "Running Ansible playbook ${env.PLAYBOOK_FILE}..."
                dir("${env.ANSIBLE_DIR}") {
                    sh """
                        ansible-playbook -i ${env.INVENTORY_FILE} ${env.PLAYBOOK_FILE}
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Ansible setup completed successfully!"
        }
        failure {
            echo "Ansible setup failed. Check console output for details."
        }
    }
}
```

![image](https://i.imgur.com/mZnOH7H.png)
![image](https://i.imgur.com/eHY9rYS.png)

#### 7.2. Создание нового Pipeline в Jenkins

1. В разделе Jenkins необходимо нажать **New Item**.
2. Ввести имя задачи, например:

   `ansible-agent`
3. Выбрать тип **Pipeline**.
4. Нажать **OK**.

![image](https://i.imgur.com/Shpmrwj.png)

#### 7.3. Настройка Pipeline из SCM

В разделе **Pipeline**:

- **Definition** → *Pipeline script from SCM*
- **SCM** → *Git*
- Repository URL:

  ```
  https://github.com/iurii1801/Auto_scripting.git
  ```
- Branch:

  ```
  */lab05
  ```
- Script Path:

  ```
  lab05/pipelines/ansible_setup_pipeline.groovy
  ```

![image](https://i.imgur.com/bjHySkm.png)
![image](https://i.imgur.com/YT5DxId.png)

#### 7.4. Запуск конвейера

После сохранения необходимо нажать `Build Now`

После успешного выполнения Pipeline:

- Playbook `setup_test_server.yml` выполнится на тестовом сервере.
- Apache2 будет установлен.
- PHP-окружение будет настроено.
- Виртуальный хост `recipe-book` будет активирован.
- Тестовый сервер будет полностью готов.

Консоль Jenkins должна завершиться сообщением:

```
Ansible setup completed successfully!
```

![image](https://i.imgur.com/7BNa46h.png)

