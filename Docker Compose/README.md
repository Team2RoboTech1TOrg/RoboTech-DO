# Инфраструктура сервере с применением docker compose

Этот репозиторий содержит конфигурацию `docker-compose` и все необходимые файлы для развёртывания стека иструментов  для разработки AI, ML и мониторинга.  

## Подготовка

Перед началом убедитесь, что на вашей системе установлен docker compose  

### Шаги по развертыванию

1. Клонируйте репозиторий  
2. Создайте пустую папку grafana на уровне с папкой prometheus  
3. Измените логин/пароль в docker compose у postgresql и postgresql exporter(рекомендуется использовать docker secrets), а так же заменить данные alertmanager-bot на свои. 
4. Изменяем данные в файлах /alertmanager/config.yml на свои

   
## Список инструментов

nginx(для вывода приветственной страницы),alertmanager,alertmanager-bot, grafana, jupyterhub,postgres-exporter,juteam(рабочая среда DS и DA),postgres,postgres-exporter,dcgm_exporter,node-exporter, prometheus.  
 
