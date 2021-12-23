# 后端

请在 settings 下注释掉 django.middleware.csrf.CsrfViewMiddleware 这个中间件，我们不需要 CSRF。

定时任务使用了 django-q 包管理。在配置完毕后，另开一个 screen/tmux，输入以下命令开始定时任务。

```
python manage.py qcluster
```

数据库设置为 `utf8mb4`，因为 mysql 的 utf8 实际上在 utf8 正式标准提出之前就实装了，其 utf8 为三字节长。mb4 为 most bytes 4 的意思，用于实现正确的 utf8 标准。
