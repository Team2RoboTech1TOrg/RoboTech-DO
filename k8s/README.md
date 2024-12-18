# Описание инфраструктуры, развернутой на сервере с применением k8s

Это итоговая инфраструктура нашего проекта.

## Список инструментов развернутых в кластере
 
Prometheus, Grafana, Loki, Flannel, NFS Subdir External Provisioner, NVIDIA Device Plugin (nvdp),DCGM Exporter,Kubeflow,Node Exporter, dcgm-exporter, kube-state-metrics, Promtail, Dex.
 

# Шаги по развертыванию

Ниже приведено руководство по настройке Kubernetes-кластера и разверытыванию различных инструментов, таких как **Prometheus**, **Grafana** и **Kubeflow**. На этой стадии предполагается, что **Helm**, **Kustomize** , **nfs** и плагины **NVIDIA** уже установлены.  

## Предварительная очистка системы

Если по какой-либо причине **Kubernetes** уже был установлен на сервере прежде (например, в случае, если выполняется его переустановка), то желательно  очистить его прошлую конфигурацию. Для этого необходимо выполнить следующие команды:

```bash
sudo kubeadm reset -f
sudo rm -rf /etc/kubernetes/ /var/lib/etcd /var/lib/kubelet /var/lib/dockershim /var/run/kubernetes
sudo rm -rf /etc/cni /var/lib/cni
sudo ip link delete cni0
sudo ip link delete flannel.1 # для Flannel //У нас может быть другой
sudo reboot
```

## Инициализация кластера
 
Для инициации выполним команду:

```bash
kubeadm init --pod-network-cidr=10.244.0.0/16
```

**Важно:** если в системе установлены два контейнерных движка, например, **Docker** и **CRI-O**, в команде инициализации необходимо указать параметр **CRI-сокет**: 
`--cri-socket unix:///var/run/crio/crio.sock`.

В нашем случае мы выполняем развертывание в режиме **Single node**, поэтому необходимо отключить предусмотренное по умолчанию ограничение на использование **Master node** для вычислений.

```bash
kubectl taint nodes masternode node-role.kubernetes.io/control-plane:NoSchedule-
```

## Установка необходимых дополнительных инструментов

- Установим сетевой плагин **Flannel**:

```bash
kubectl apply -f https://github.com/coreos/flannel/raw/master/Documentation/kube-flannel.yml
kubectl get po -n kube-flannel
```
- Выполним установку и обновление нужных чартов:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/
helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
helm repo add gpu-helm-charts \
  https://nvidia.github.io/dcgm-exporter/helm-charts
helm repo update
```

- Установим NFS-контроллер:

```bash
helm install nfs-subdir-external-provisioner nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
  --set nfs.server=10.1.1.9 \
  --set nfs.path=/mnt/nfs_share \
  --namespace nfs-provisioner \
  --create-namespace
```

# Мониторинг

Для организации мониторинга установим **Prometheus, Grafana, Loki** (если **Loki** не устанавливается, решение можно найти в папке [loki-stack](https://github.com/Team2RoboTech1TOrg/RoboTech-DO/tree/main/k8s/loki-stack):

```bash
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
helm install loki grafana/loki-stack --namespace monitoring --set grafana.enabled=false
```

Возможно возникновение проблем с корректной работой **node-exporter** из **kube-prometheus-stack**. В таком случае его можно развернуть отдельным контейнером:

```bash
docker run -d \
  --name=node-exporter \
  -p 9101:9101 \
  prom/node-exporter --web.listen-address=":9101"
```
  
# Настройка поддержки GPU в кластере

Предполагается, что на сервере уже установлены драйвер **Nvidia-smi**, а также **Nvidia-container-toolkit**.

- Установим плагин от **NVIDIA**:

```bash
helm install -i nvdp nvdp/nvidia-device-plugin \
  --namespace nvidia-device-plugin \
  --create-namespace \
  --version 0.17.0
```

- Установим экспортер метрик о GPU:

```bash
helm repo add gpu-helm-charts \
  https://nvidia.github.io/dcgm-exporter/helm-charts
```

# Установка Kubeflow

- Клонируем репозиторий:

```bash
git clone https://github.com/kubeflow/manifests.git
```

- Настраиваем систему:
```bash
sudo sysctl fs.inotify.max_user_instances=2280
sudo sysctl fs.inotify.max_user_watches=1255360
```
- В целях безопасности меняем пароль и логин пользователя по умолчанию. Для этого редактируем файл `common/dex/base/dex-passwords.yaml`.

Хеш для обновленного пароля пользователя по умолчанию можно сгенерировать командой: 

```bash
python3 -c 'from passlib.hash import bcrypt; import getpass; print(bcrypt.using(rounds=12, ident="2y").hash(getpass.getpass()))'
```

- Откорректируем файл `apps/pipeline/upstream/base/pipeline/ml-pipeline-ui-deployment.yaml`, добавив `DISABLE_GKE_METADATA`
  
  ```bash
    spec:
      containers:
      - env:
        - name: DISABLE_GKE_METADATA
          value: "true"
        - name: VIEWER_TENSORBOARD_POD_TEMPLATE_SPEC_PATH
          value: /etc/config/viewer-pod-template.json
        - name: DEPLOYMENT
          value: KUBEFLOW
        - name: ARTIFACTS_SERVICE_PROXY_NAME
          value: ml-pipeline-ui-artifact
        - name: ARTIFACTS_SERVICE_PROXY_PORT
          value: "80"
```

- Отредактируем манифесты, таким образом, чтобы обеспечить возможность подключения к сервисам kubeflow по http:
  
```bash
find . -type f -exec sed -i 's/APP_SECURE_COOKIES=true/APP_SECURE_COOKIES=false/g' {} +
```

- Применим манифесты:

```bash
kubectl apply -f pvc/mysql-pvc.yaml
kubectl apply -f pvc/minio-pvc.yaml
kubectl apply -f pvc/katib-mysql-pvc.yaml
```

- Развернем **Kubeflow**:

```bash
while ! kustomize build example | awk '!/well-defined/' | kubectl apply -f -; do 
  echo "Retrying to apply resources"; 
  sleep 10; 
done
```

## Обеспечиваем доступ к сервисам

- Для доступа к сервисам необходимо пробросить порты, для этого можно использовать следующие команды:
- 
```bash
kubectl patch svc grafana -n monitoring -p '{"spec": {"type": "NodePort"}}'   
kubectl patch svc prometheus-server -n monitoring -p '{"spec": {"type": "NodePort"}}'
kubectl patch svc istio-ingressgateway -n istio-system -p '{"spec": {"type": "NodePort"}}'
```

## Настройка авторизации пользователей

Процедуры настройки авторизации пользователей для доступа к веб-интерфейсу **Kubeflow** описаны в директории [DEX](https://github.com/Team2RoboTech1TOrg/RoboTech-DO/tree/main/k8s/DEX).

## В завершение 


Необходимо вручную зайти в **Grafana** и настроить пользователей и дашборд через графический интерфейс. Чтобы узнать пароль, который сгенерировался по умолчанию, необходимо выполнить команду:

```bash
kubectl get secret --namespace default grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo 
```
Для метрик железа и кластера дашборды настроены по умолчанию,  для gpu можно использовать готовый дашборд, его можно найти по ID:14574. 
