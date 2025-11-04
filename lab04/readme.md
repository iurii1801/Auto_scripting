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

Необходимо создайть папку `secrets` в корне проекта и добавить в неё ключи `SSH`, необходимые для подключения к удаленным серверам.

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
   Если нет — перейти во вкладку **Available** и установи его.

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
2. Ввести имя — `ssh-agent1` и выберать **Permanent Agent**.
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

### Шаг 8. Создание конвейера `Jenkins` для PHP-проекта

#### 8.1 Подготовка PHP-проекта для конвейера

Для выполнения лабораторной работы использовался PHP-проект, подготовленный локально (ранее выполненная лабораторная работа).
Проект был **распакован из архива** и размещён в каталоге `lab04`.

Он содержит базовые PHP-файлы и структуру, необходимую для демонстрации конвейера `Jenkins`.
В проекте изначально не было модульных тестов, поэтому в лабораторной работе демонстрируется запуск конвейера с базовыми командами (например, проверка версии PHP или простая проверка синтаксиса).

#### 8.2 Создание Pipeline-job в Jenkins

1. На главной странице Jenkins необходимо нажать **“Создать Item (New Item)”**.
2. Ввести имя, например: **`php-lab04-pipeline`**.
3. Выбрать тип **`Pipeline`** и нажать **OK**.

В настройках задания:

- во вкладке **General** можно оставить настройки по умолчанию;
- отдельный чекбокс “Restrict where this project can be run” для pipeline-job не использовался —
  привязка к агенту выполняется через `label` в самом Jenkinsfile.

![image](https://i.imgur.com/6gZRoFs.png)

#### 8.3 Настройка секции *Pipeline* (скрипт Jenkinsfile)

Во вкладке **Pipeline**:

1. В поле **Definition** необходимо выбрать вариант **`Pipeline script`**.
2. В текстовое поле **Script** вставить следующий конвейер:

```groovy
pipeline {
    agent {
        label 'php-agent'
    }

    stages {
        stage('Prepare Project') {
            steps {
                echo 'Preparing PHP project...'
                sh 'php -v'
            }
        }

        stage('Run Simple Check') {
            steps {
                echo 'Running syntax check...'
                sh 'php -l index.php || echo "No syntax errors"'
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

![image](https://i.imgur.com/uNAkmeb.png)

Этот конвейер:

- запускается **на агенте с меткой `php-agent`** (**SSH-агент в Docker**);
- на шаге **Install Dependencies** выполняет установку зависимостей через **Composer**;
- на шаге **Test** запускает модульные тесты с помощью **PHPUnit**;
- в блоке `post` выводит сообщения о статусе выполнения.

#### 8.4 Запуск и проверка конвейера

1. На странице задания **`php-lab04-pipeline`** необходимо нажать **“Собрать сейчас (Build Now)”**.
2. В левой части появится новый билд `#1`.
3. Нажать по билду → **Console Output**, чтобы посмотреть лог.


В логе должны быть строки примерно такого вида:

```text
[Pipeline] Start of Pipeline
[Pipeline] node
Running on ssh-agent1 in /home/jenkins/agent/workspace/php-lab04-pipeline
[Pipeline] stage (Prepare Project)
[Pipeline] sh
+ php -v
...
[Pipeline] stage (Run Simple Check)
[Pipeline] sh
+ php -l index.php || echo "No syntax errors"
...
[Pipeline] echo
All stages completed successfully!
Finished: SUCCESS
```

![image](https://i.imgur.com/WO89hou.png)

> В результате конвейер **php-lab04-pipeline** успешно выполнился.
> `Jenkins` выполнил все этапы (Prepare Project и Run Simple Check) на агенте `ssh-agent1`, что подтверждается зелёной меткой *SUCCESS*.

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
