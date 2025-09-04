执行步骤

1. 安装依赖

```bash
uv sync 
```

2. 配置config
至少配置config.yaml.example里的项目

3. 运行veadk web
先准备一下数据
```bash
python demo/prepare_data.py 
```

这个要等三到五分钟，因为用的是viking memory，第一次运行会等一阵

```bash
LONG_TERM_MEMORY_BACKEND=viking veadk web
```



- tracing结果
![image](images/img.png)

- 多轮对话效果
![image1](images/img_1.png)
