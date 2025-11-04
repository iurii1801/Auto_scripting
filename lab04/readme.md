# Лабораторная работа №4: Настройка Jenkins для автоматизации задач DevOps (CI/CD)

## Цель работы

Освоить базовую конфигурацию системы **Jenkins** для автоматизации задач DevOps, а именно:

- запуск контроллера `Jenkins` в **Docker**;
- настройка удалённого агента по SSH;
- создание и выполнение конвейера (**Jenkins Pipeline**) для PHP-проекта с запуском тестов.

---

## Подготовка

Работу нужно выполнить в каталоге `lab04` в репозитории GitHub для хранения всех файлов, связанных с этой лабораторной работой.
Для выполнения лабораторной работы необходимы **Docker** и **Docker Compose**.

## Назначение

Создать `docker-compose.yml` файл и определить в нем следующие службы:

1. **Jenkins Controller**
2. **SSH Agent**

---

## Ход выполнения работы

### Шаг 1. Создание структуры проекта

Создать папку и войти в неё можно с помощью команд:

```bash
mkdir lab04
cd lab04
```

### Шаг 2. Создание файла `docker-compose.yml`

Необходимо создать файл **`docker-compose.yml`** в папке `lab04` и вставить в него начальную конфигурацию `Jenkins Controller`:

```yaml
version: '3.8'

services:
  jenkins-controller:
    image: jenkins/jenkins:lts
    container_name: jenkins-controller
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
    networks:
      - jenkins-network

volumes:
  jenkins_home:
  jenkins_agent_volume:

networks:
  jenkins-network:
    driver: bridge
```

![image](https://i.imgur.com/ea5XT1U.png)

### Шаг 3. Запуск `Jenkins Controller`

Из папки `lab04` необходимо выполнить команду:

```bash
docker compose up -d
```

![image](https://i.imgur.com/QujPpj5.png)
![image](https://i.imgur.com/7lvILfw.png)

Затем нужно открыть браузер и перейти по адресу:
**[http://localhost:8080](http://localhost:8080)**

![image](https://i.imgur.com/pgAuMBz.png)

На экране появляется страница с настройками `Jenkins`.

### Шаг 4. Вход в `Jenkins` и завершение первичной настройки

Перед началом необходимо узнать пароль для входа. 

Сделать это можно командой:

```bash
docker exec -it jenkins-controller cat /var/jenkins_home/secrets/initialAdminPassword
```

![image](https://i.imgur.com/9Rxtorp.png)

Необходимо скопировать пароль.

Далее в браузере на странице **Unlock Jenkins** необходимо вставить туда скопированный пароль.

![image](https://i.imgur.com/F7gZasi.png)

После этого надо установить рекомендуемые плагины.

Когда `Jenkins` попросит установить плагины, нужно выбрать:

**`Install suggested plugins`**

![image](https://i.imgur.com/D27yEnx.png)

> Установка может занять 2–5 минут. После этого `Jenkins` предложит создать первого пользователя.

### Шаг 5. Создание пользователя

Необходимо заполнить все поля, которые появятся на экране.

Нажать **Save and Continue → Start using Jenkins**

![image](https://i.imgur.com/JZmsvin.png)
![image](https://i.imgur.com/KPolPaP.png)

После этого попадаем на главную страницу `Jenkins Dashboard`.

![image](https://i.imgur.com/5snEzfR.png)

> `Jenkins` успешно настроен.

### Шаг 6. Подготовка SSH-агента (второй контейнер)

На этом шаге необходимо добавить **вторую службу** — `ssh-agent`, чтобы `Jenkins` мог запускать сборки не только на своём контроллере, но и на выделённом агенте через `SSH`.

#### 6.1 Создание SSH-ключей

Необходимо создать папку `secrets` в корне проекта и добавить в неё ключи `SSH`, необходимые для подключения `Jenkins`-контроллера к `SSH`-агенту.

Нужно поочерёдно выполнить команды:

```bash
mkdir secrets
cd secrets
ssh-keygen -f jenkins_agent_ssh_key
```

![image](https://i.imgur.com/ypmAkyj.png)
![image](https://i.imgur.com/SQHdC3E.png)
![image](https://i.imgur.com/DqSXuiB.png)

После этого появятся файлы:

- `jenkins_agent_ssh_key` — приватный ключ
- `jenkins_agent_ssh_key.pub` — публичный ключ

Публичный ключ нужно будет использовать в `.env`.

#### 6.2 Создание `Dockerfile` для агента

В том же каталоге (`lab04`) необходимо создать **`Dockerfile`**, со следующим содержимым:

```dockerfile
FROM jenkins/ssh-agent

RUN apt-get update && apt-get install -y php-cli
```

![image](https://i.imgur.com/Fu6r2fr.png)

> Этот **`Dockerfile`** создаёт образ на основе официального `jenkins/ssh-agent` и устанавливает PHP для последующих тестов.

#### 6.3 Обновление `docker-compose.yml`

Теперь необходимо добавить вторую службу:

```yaml
ssh-agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ssh-agent
    environment:
      - JENKINS_AGENT_SSH_PUBKEY=${JENKINS_AGENT_SSH_PUBKEY}
    volumes:
      - jenkins_agent_volume:/home/jenkins/agent
    depends_on:
      - jenkins-controller
    networks:
      - jenkins-network
```

![image](https://i.imgur.com/gxdEtxE.png)

#### 6.4 Создание файла `.env`

В корне `lab04` необходимо создать файл `.env` и добавить `JENKINS_AGENT_SSH_PUBKEY` переменную среды.
(скопировать содержимое из `jenkins_agent_ssh_key.pub` в одну строку без переносов)

![image](https://i.imgur.com/eLPpfTB.png)

#### 6.5 Перезапуск `Docker Compose`

После сохранения файлов нужно выполнить следующую команду, чтобы изменения вступили в силу.:

```bash
docker compose up -d --build
```

![image](https://i.imgur.com/nUKdTQx.png)
![image](https://i.imgur.com/d87MpD3.png)

### Шаг 7. Настройка `Jenkins` для работы с SSH-агентом

#### 7.1 Установка и проверка плагина `SSH Build Agents Plugin`

1. В интерфейсе `Jenkins` необходимо открыть:
   **Manage Jenkins → Plugins → Installed**
2. В поиске ввести `SSH Build Agents`.
   Если плагин есть — отлично.
   Если нет — перейти во вкладку **Available** и установить его.

![image](https://i.imgur.com/yMkSJHL.png)

#### 7.2 Добавление `SSH-учётных данных (Credentials)`

1. Необходимо перейти в **Manage Jenkins → Credentials → System → Global credentials (unrestricted)**.
2. Нажать **Add Credentials** и выбрать тип — **SSH Username with private key**.
3. Заполнить поля:

   - **Scope:** Global
   - **Username:** `jenkins`
   - **Private Key:** *Enter directly* → вставить содержимое файла `secrets/jenkins_agent_ssh_key`
   - **Passphrase:** оставить пустым
4. Нажать **Create** и убедиться, что запись появилась в списке.

![image](https://i.imgur.com/9iYlmfz.png)
![image](https://i.imgur.com/PQYeNax.png)

#### 7.3 Создание узла-агента (Manage Nodes)

1. Необходимо открыть **Manage Jenkins → Nodes → New Node**.
2. Ввести имя — `ssh-agent1` и выбрать **Permanent Agent**.
3. Настроить параметры:

   - **Remote root directory:** `/home/jenkins/agent`
   - **Labels:** `php-agent`
   - **Executors:** `1`
   - **Launch method:** *Launch agents via SSH*
   - **Host:** `ssh-agent` (имя контейнера из docker-compose.yml)
   - **Credentials:** выбрать созданные SSH-ключи

4. Сохранить и дождаться статуса **Agent is online**.

![image](https://i.imgur.com/eF37cMr.png)
![image](https://i.imgur.com/U5TtCX8.png)
![image](https://i.imgur.com/2SAH2Af.png)

> После этого `Jenkins` сможет подключаться к агенту `ssh-agent` и выполнять конвейеры с лейблом `php-agent`.

### Шаг 8. Создание конвейера Jenkins для PHP-проекта

#### 8.1. Подготовка PHP-проекта и размещение в GitHub

Для выполнения лабораторной работы был использован PHP-проект **recipe-book**, ранее созданный в рамках курса по PHP-программированию. Проект был размещён в репозитории GitHub **[iurii1801/auto_scripting](https://github.com/iurii1801/auto_scripting)** в отдельной ветке `lab04`, в каталоге `lab04/recipe-book`.

Проект содержит файлы PHP, конфигурацию Composer и простейшие юнит-тесты PHPUnit, размещённые в папке `tests`.

#### 8.2. Добавление `Jenkinsfile` в проект

Для автоматизации сборки и тестирования в корне папки `recipe-book` необходимо создать файл **`Jenkinsfile`**.
Он описывает конвейер (`Pipeline`), состоящий из двух основных стадий — **установка зависимостей** и **тестирование**.

```groovy
pipeline {
    agent {
        label 'php-agent'
    }

    stages {
        stage('Install Dependencies') {
            steps {
                echo 'Preparing project...'
                dir('lab04/recipe-book') {
                    sh 'composer install'
                }
            }
        }

        stage('Test') {
            steps {
                dir('lab04/recipe-book') {
                    sh './vendor/bin/phpunit --testdox tests'
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed.'
        }
        success {
            echo 'All stages completed successfully!'
        }
        failure {
            echo 'Errors detected in the pipeline.'
        }
    }
}
```

> Конвейер выполняется на агенте `php-agent` (контейнере ssh-agent), устанавливает зависимости через `Composer` и запускает тесты `PHPUnit`.
> Использование `dir('lab04/recipe-book')` позволяет выполнять команды в нужной директории проекта.

#### 8.3. Настройка конвейера Jenkins

На главной странице `Jenkins` необходимо создать новый элемент (**New Item**) с именем `php-lab04-pipeline` и типом **Pipeline**.
Во вкладке **Pipeline** выбрать вариант **Pipeline script from SCM**, где задать параметры:

- **SCM:** Git
- **Repository URL:** `https://github.com/iurii1801/auto_scripting.git`
- **Credentials:** `jenkins`
- **Branch Specifier:** `*/lab04`
- **Script Path:** `lab04/recipe-book/Jenkinsfile`

![image](https://i.imgur.com/H2hP8kn.png)
![image](https://i.imgur.com/W7QuxeN.png)

> Эти параметры позволяют Jenkins автоматически загружать конвейер из ветки `lab04` и использовать соответствующий Jenkinsfile из папки проекта.

#### 8.4. Запуск и проверка конвейера

После сохранения конфигурации конвейер нужно запустить вручную с помощью кнопки **“Собрать сейчас (Build Now)”**.
В процессе выполнения `Jenkins` выполнит следующие действия:

1. Клонирует репозиторий с GitHub;
2. Устанавливает зависимости проекта (`composer install`);
3. Запускает тесты PHPUnit из каталога `tests`;
4. Завершает сборку успешно.

Фрагмент лога выполнения:

```text
+ composer install
Loading composer repositories with package information
Installing dependencies from lock file
Generating autoload files
+ ./vendor/bin/phpunit --testdox tests
PHPUnit 10.5.58 by Sebastian Bergmann and contributors.

Sample
 ✔ testTrue

All stages completed successfully!
Finished: SUCCESS
```

> Результат выполнения показывает, что все этапы прошли успешно, а тесты были выполнены без ошибок.
> Jenkins автоматически отметил сборку как **успешную (SUCCESS)**.

#### 8.5. Итог

Таким образом, в рамках данного шага был реализован полный цикл `CI/CD`-процесса для PHP-проекта:

- исходный код хранится в GitHub;
- Jenkins автоматически загружает проект, устанавливает зависимости и выполняет тесты;
- результаты отображаются в панели Jenkins.

![image](https://i.imgur.com/vmQ70WW.png)

> Это подтверждает успешное выполнение лабораторной работы и корректную настройку системы `Jenkins` для автоматизации задач `DevOps`.

---

## Выводы

В ходе выполнения лабораторной работы была проведена полная настройка системы `Jenkins` для автоматизации `DevOps`-задач. В процессе работы был создан проект в среде `Docker`, включающий контроллер `Jenkins` и `SSH-агент`, обеспечивающий удалённое выполнение конвейеров. Была выполнена установка `Jenkins`, произведена первичная настройка интерфейса, добавлены необходимые плагины, сгенерированы и подключены SSH-ключи для безопасного взаимодействия между контейнерами. Затем был успешно создан и запущен `Jenkins-конвейер` для PHP-проекта, который демонстрирует автоматизацию базовых этапов подготовки и проверки проекта. Все этапы сборки были корректно выполнены, что подтверждается успешным завершением конвейера со статусом «SUCCESS». В результате работы удалось закрепить знания по созданию и настройке `Jenkins`-окружения в `Docker`, освоить принципы работы контроллера и агента, а также отработать практические навыки построения и выполнения конвейеров `CI/CD`.

---

## Библиография

1. [Jenkins Documentation](https://www.jenkins.io/doc/) — официальная документация по установке, настройке и использованию системы **Jenkins**.
2. [Jenkins Docker Hub](https://hub.docker.com/r/jenkins/jenkins) — страница официального Docker-образа **Jenkins**, используемого для развёртывания контроллера.
3. [Jenkins SSH Build Agents Plugin](https://plugins.jenkins.io/ssh-slaves/) — документация по плагину для подключения удалённых агентов через **SSH**.
4. [Docker Compose Documentation](https://docs.docker.com/compose/) — руководство по созданию и управлению многоконтейнерными приложениями с помощью **Docker Compose**.
5. [Jenkins Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/) — описание синтаксиса **Declarative Pipeline**, используемого для построения конвейеров.
6. [PHP Documentation](https://www.php.net/docs.php) — официальная документация языка **PHP**, применяемого для тестирования и выполнения команд в конвейере Jenkins.
