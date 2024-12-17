# Описание инфраструктуры, развернутой на сервере с применением Docker Compose

На начальном этапе стажировки на сервере был развернут стек ПО для разработки, обучения моделей и организации мониторинга на базе контейнеров.

Перед началом развертывания следует убедиться, что в системе установлен **Docker**

## Шаги по развертыванию

1. Клонирование репозитория  
2. Создание пустой директории `Grafana` на одном уровне с ди prometheus  
3. Измените логин/пароль в docker compose у postgresql и postgresql exporter(рекомендуется использовать docker secrets), а так же заменить данные alertmanager-bot на свои. 
4. Изменяем данные в файлах /alertmanager/config.yml на свои

   
## Список инструментов

nginx(для вывода приветственной страницы),alertmanager,alertmanager-bot, grafana, jupyterhub,postgres-exporter,juteam(рабочая среда DS и DA),postgres,postgres-exporter,dcgm_exporter,node-exporter, prometheus.  
 
