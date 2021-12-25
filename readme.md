# 后端

请在 settings 下注释掉 django.middleware.csrf.CsrfViewMiddleware 这个中间件，我们不需要 CSRF。

定时任务使用了 django-q 包管理。在配置完毕后，另开一个 screen/tmux，输入以下命令开始定时任务。

```
python manage.py qcluster
```

数据库设置为 `utf8mb4`，因为 mysql 的 utf8 实际上在 utf8 正式标准提出之前就实装了，其 utf8 为三字节长。mb4 为 most bytes 4 的意思，用于实现正确的 utf8 标准。

# docker-compose

后端可使用 docker-compose 一键部署。

```
git clone https://github.com/3C-Group/backend.git
cd backend
docker-compose up
```

这种部署下使用的是默认的 8000 端口。可修改的配置有：

- .env
  - DB_NAME：将要使用的数据库的名称
  - DB_USER：将要使用的数据库中将创建的用户的名称
  - DB_PASSWORD：将要使用的数据库中将创建的用户的密码
  - DB_ROOT_PASSWORD：将要使用的数据库的root用户密码
    如果是从已有的后端迁移过来，则可以将 `docker-compose` 中 `mysql` 部分 `environment` 全都删掉。数据库默认保存位置映射为 `/home/ubuntu/mysql/`，可根据实际需要自行修改；如果是从已有的数据库进行迁移，只需将其设置为对应地址，否则请保证映射出去的位置没有数据。修改端口也同样在 `docker-compose` 中，`nginx` 部分。若用于生产环境，可直接将其改为 22。
- my.cnf
  - database：后端使用的数据库的名称，一般与 `DB_NAME` 相同
  - user：后端使用的数据库用户的名称，一般与 `DB_USER` 相同
  - password：后端使用的数据库用户的密码，一般与 `DB_PASSWORD` 相同
  - host：mysql 服务器的地址，一般为 `mysql`，即为 `docker-compose` 中指定的 mysql 容器名
- backend/settings.py
  - 为了安全性，最好在 `ALLOWED_HOSTS` 中仅允许前端 IP 访问。
- config/nginx/django_app.conf
  - server_name 改为实际使用的域名或 IP。
  - listen 若改动，需要在 `docker-compose` 中将映射出去的端口一并修改。
