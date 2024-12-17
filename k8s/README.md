# Kubernetes Cluster Setup

Это руководство предназначено для настройки Kubernetes-кластера и разверытывания различных инструментов, таких как  Prometheus, Grafana и Kubeflow. Предполагается , что helm и kustomize уже установлены.  

## Предварительная очистка системы

Если Kubernetes уже установлен, то желательно сбросить текущую конфигурацию. Для этого выполните следующие команды:

```bash
sudo kubeadm reset -f
sudo rm -rf /etc/kubernetes/ /var/lib/etcd /var/lib/kubelet /var/lib/dockershim /var/run/kubernetes
sudo rm -rf /etc/cni /var/lib/cni
sudo ip link delete cni0
sudo ip link delete flannel.1 # для Flannel //У нас может быть другой
sudo reboot
```

## Инициализация кластера
 
Инициализируем кластер:

```bash
kubeadm init --pod-network-cidr=10.244.0.0/16
```

Важно: если в системе установлены и Docker и CRI-O, укажите параметр CRI-сокет: --cri-socket unix:///var/run/crio/crio.sock.

Если у нас есть только мастер нода, отключим ограничение на использование её для вычислений.

```bash
kubectl taint nodes masternode node-role.kubernetes.io/control-plane:NoSchedule-
```

## Установка инструментов

Установить flannel:

```bash
kubectl apply -f https://github.com/coreos/flannel/raw/master/Documentation/kube-flannel.yml
kubectl get po -n kube-flannel
```
Установить и обновить нужные чарты:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/
helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
helm repo add gpu-helm-charts \
  https://nvidia.github.io/dcgm-exporter/helm-charts
helm repo update
```

Установить NFS-контроллер:

```bash
helm install nfs-subdir-external-provisioner nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
  --set nfs.server=10.1.1.9 \
  --set nfs.path=/mnt/nfs_share \
  --namespace nfs-provisioner \
  --create-namespace
```

### Мониторинг


Установить Prometheus, Grafana, Loki (если Loki не устанавливается, решение можно найти в папке loki-stack https://github.com/Team2RoboTech1TOrg/k8s/tree/main/loki-stack):

```bash
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
helm install loki grafana/loki-stack --namespace monitoring --set grafana.enabled=false
```

Если не работает node-exporter из kube-prometheus-stack, его можно развернуть отдельным контейнером:

```bash
docker run -d \
  --name=node-exporter \
  -p 9101:9101 \
  prom/node-exporter --web.listen-address=":9101"
```
  
### Поддержка GPU

Предполагается, что на сервере уже установлен Nvidia-smi и Nvidia-container-toolkit.  
Установите плагин от NVIDIA:

```bash
helm install -i nvdp nvdp/nvidia-device-plugin \
  --namespace nvidia-device-plugin \
  --create-namespace \
  --version 0.17.0
```

Установите экспортер метрик о GPU:
```bash
helm repo add gpu-helm-charts \
  https://nvidia.github.io/dcgm-exporter/helm-charts
```

### Установка Kubeflow

Клонируем репозиторий:

```bash
git clone https://github.com/kubeflow/manifests.git
```

Настраиваем систему:
```bash
sudo sysctl fs.inotify.max_user_instances=2280
sudo sysctl fs.inotify.max_user_watches=1255360
```
Изменить пароль и логин пользователя по умолчанию. Для этого редактируем файл common/dex/base/dex-passwords.yaml.
Пароль можно сгенерировать командой: 
```bash
python3 -c 'from passlib.hash import bcrypt; import getpass; print(bcrypt.using(rounds=12, ident="2y").hash(getpass.getpass()))'
```
Изменим  apps/pipeline/upstream/base/pipeline/ml-pipeline-ui-deployment.yaml , а именно добавим DISABLE_GKE_METADATA\
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
Отредактировать манифесты, чтобы можно было подключаться к сервисам kubeflow по http:  
```bash
find . -type f -exec sed -i 's/APP_SECURE_COOKIES=true/APP_SECURE_COOKIES=false/g' {} +
```
Применить манифесты:
```bash
kubectl apply -f pvc/mysql-pvc.yaml
kubectl apply -f pvc/minio-pvc.yaml
kubectl apply -f pvc/katib-mysql-pvc.yaml
```
Развернуть kubeflow:

```bash
while ! kustomize build example | awk '!/well-defined/' | kubectl apply -f -; do 
  echo "Retrying to apply resources"; 
  sleep 10; 
done
```

### Обеспечиваем доступ к сервисам
Поправить под свои svc либо использовать istio

```bash
kubectl get secret --namespace default grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo 
kubectl patch svc grafana -n monitoring -p '{"spec": {"type": "NodePort"}}'   
kubectl patch svc prometheus-server -n monitoring -p '{"spec": {"type": "NodePort"}}'
kubectl patch svc istio-ingressgateway -n istio-system -p '{"spec": {"type": "NodePort"}}'
```

## В завершение 
Необходимо вручную зайти в grafana и настроить пользователей и дашборд для gpu(ID 14574). 
