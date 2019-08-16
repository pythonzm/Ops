## 使用 docker-compose 快速部署

### 0. 安装 docker docker-compose

见 docker 官方文档

### 1. 构建镜像

+ ops

```
git clone https://github.com/pythonzm/Ops.git
cd Ops
docker build -t ops .
```

### 2. 创建数据持久化目录

```
sudo mkdir -p /data/mysql /data/redis /data/mongodb /data/ops/initapp /data/ops/ansible_roles
```

### 3. 启动

```
docker-compose up -d
```

### 4. 访问

浏览器访问：

```
http://<your-ip-address>:8000
```
