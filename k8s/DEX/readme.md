# Настройка статических пользователей в Kubeflow

Здесь описана выполненная настройка статических пользователей для их авторизации в веб-интерфейсе **Kubeflow** через **DEX**.
Авторизация через сторонних провайдеров авторизации в данном случае не рассматривалась.

## Роли

Предусмотрено следующее разделение ролей:

- cluster-admin-role - администраторы;
- researcher-role - Data scientists;
- data-analyst-role - Дата аналитики.

## Профили пользователей

Для каждого из пользователей  создан [индивидуальный файл профиля](https://github.com/Team2RoboTech1TOrg/k8s/tree/main/DEX/user-profiles) c указанием адреса электронной почты, используемого при настройке авторизации.
В связи с тем, что при применении профиля пользователя в **Kubeflow** создается именной **namespace**, в условиях ограниченности ресурсов сервера и имеющихся ограничений кластера по созданию ресурсов (подов), профили были созданы только для ограниченного числа пользователей.

## Применение конфигураций

Для применения конфигураций ролей, привязок ролей и пользователей, необходимо из корневой директории **DEX** выполнить:

``` bash
kubectl apply -f ./roles-bindings/ -f ./user-profiles
```

## Модификация configmap DEX

Для настройки авторизации пользователей с учетом описанных выше конфигураций ролей, привязок ролей и профилей польлзоателей, необходимо модифицировать действующие настройки configmap DEX.
Для этого необходимо:

- Выполнить импорт в файл текущей конфигурации **DEX**;
- Внести в него необходимые изменения;
- Выполнить на базе полученного манифеста обновление конфигурации на сервере;
- Выполнить перезапуск сервера **DEX** с обновлённой конфигурацией.
  
### Импорт текущей конфигурации в файл

``` bash
 kubectl get configmap dex -n auth -o jsonpath='{.data.config\.yaml}' > dex-upd.yaml
```

### Добавление в полученный файл в секцию staticPassword: записей для каждого из новых статических пользователей

Добавление записей для новых статических пользователей выполнены в следующем виде:

``` bash
- email: "ngorbenko@example.com"
  hash: "$2b$12$7Mjxpl67buAUFSmxc/h.8.5ah1UaGh7jiZl7yjmymnLRpPNoLCgd6"
  username: ngorbenko
  userID: ngorbenko
```

Для создания хеша пароля можно:

- Использовать команду:

``` bash
python3 -c 'from passlib.hash import bcrypt; import getpass; print(bcrypt.using(rounds=12, ident="2y").hash(getpass.getpass()))'  
 ```

- Воспользоваться [подходящим онлайн сервисом, например, этим,](https://bcrypt-generator.com/) или
- Использовать скрипт Python, предварительно установив пакет `bcrypt`:

``` bash
pip install bcrypt
```

``` python
import bcrypt

password = b"insert_password_here"
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed.decode())
```

### Обновление конфигурации на сервере

``` bash
kubectl create configmap dex --from-file=config.yaml=dex-upd.yaml -n auth --dry-run=client -o yaml | kubectl apply -f -
```

### Перезапуск DEX с обновленной конфигурацией

``` bash
kubectl rollout restart deployment dex -n auth
```
