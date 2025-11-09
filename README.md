# Anan's Sketchbook API

本项目基于 [安安的素描本聊天框](https://github.com/MarkCup-Official/Anan-s-Sketchbook-Chat-Box) 开发，提供了一个 Web API 接口实现。

一个将文本内容生成到安安素描本上的API服务，支持文本渲染、表情差分和自定义配置。

## 项目简介

本项目提供了一个 Web API 接口，允许用户通过HTTP请求将文本内容渲染到安安素描本的图片上。项目支持多种表情差分、文本样式定制和图片生成，并提供了灵活的配置选项。

## 功能特性

- 文本自动渲染到素描本上
- 多种表情差分支持（普通、开心、生气、无语、脸红、病娇）
- 文本颜色和样式自定义
- 灵活的配置系统，使用TOML格式
- 自动获取工作目录，支持相对路径配置
- 配置文件和日志统一存储在data目录
- 支持JSON格式请求
- 专业的API认证机制

## 项目结构

```text
├── BaseImages/       # 基础图片资源，包含不同表情的安安图片
├── api/              # API接口定义
├── core/             # 核心功能模块
├── data/             # 数据目录（配置文件、日志、生成的图片）
│   ├── config.toml   # 配置文件（TOML格式）
│   ├── log/          # 日志文件目录
│   └── sketchbooks/  # 生成的素描本图片
├── drawer/           # 素描本绘制功能
├── fonts/            # 字体文件目录
├── utils/            # 工具函数模块
├── main.py           # 应用入口文件
├── Dockerfile        # Docker构建文件
└── requirements.txt  # 项目依赖
```

## 配置系统

项目使用TOML格式的配置文件，配置文件位于`data/config.toml`。主要配置项包括：

### 项目基本信息
- `project_name`: 项目名称，如 "Anan's Sketchbook API"

### API配置
- `api_route`: API路由前缀，如 "/api"
- `api_port`: API服务端口，如 14541
- `api_host`: API服务主机地址，如 "0.0.0.0"
- `api_token`: API认证令牌（留空表示不启用认证）
- `domain`: 域名配置，用于生成回调URL，如 "127.0.0.1"

### 资源路径配置
```toml
[resource_path]
images = "BaseImages"  # 图片资源目录
font_file = "fonts/font.ttf"  # 字体文件路径
```

### 表情差分映射配置
```toml
[emotion_mapping]
"#普通#" = "base.png"  # 普通表情
"#开心#" = "开心.png"  # 开心表情
"#生气#" = "生气.png"  # 生气表情
"#无语#" = "无语.png"  # 无语表情
"#脸红#" = "脸红.png"  # 脸红表情
"#病娇#" = "病娇.png"  # 病娇表情
```

### 文本渲染配置
```toml
[text_config]
max_font_size = 96  # 最大字体大小，上限96
min_font_size = 12  # 最小字体大小，下限12
```

### 图片渲染配置
```toml
[image_config]
enable_sleeve_overlay = true  # 启用衣袖遮挡
```

### 文件配置
```toml
[file_config]
temp_file_retention_seconds = 300  # 临时文件保留时间，单位为秒，为0时禁用
```

所有路径配置均支持相对路径，相对于项目根目录解析。配置系统会自动创建不存在的目录，并确保路径正确解析为绝对路径。

## 部署指南

### 环境要求

- Python 3.10+
- 依赖项见requirements.txt

### 安装步骤

```bash
# 克隆项目代码

# 安装依赖
pip install -r requirements.txt

# 运行服务
python main.py
```

### Docker部署

项目已提供Docker支持，可通过以下步骤快速部署：

1. **构建Docker镜像**

```bash
docker build -t anan-sketchbook-api .
```

2. **运行Docker容器**

```bash
docker run -p 8000:8000 -v $(pwd)/data:/app/data anan-sketchbook-api
```

3. **Docker参数说明**
   - `-p 8000:8000`: 映射容器的8000端口到主机的8000端口（第一个8000是主机端口，可根据需要修改）
   - `-v $(pwd)/data:/app/data`: 挂载主机的data目录到容器中，实现数据持久化（配置、日志、生成的图片等）

4. **自定义配置**
   - 在运行容器前，可先创建data目录并放置自定义的`config.toml`文件
   - 或者在容器启动后，通过修改挂载的data目录中的配置文件进行配置

5. **查看日志**
   - 容器日志：`docker logs [容器ID]`
   - 应用日志：在挂载的data/log目录下查看app.log文件

6. **停止容器**

```bash
docker stop [容器ID]
```

7. **重启容器**

```bash
docker restart [容器ID]
```

## API使用

服务启动后，可以通过以下API进行交互：所有需要认证的接口都需要在请求头中提供有效的API令牌。

### 认证方式

API支持以下两种认证方式（推荐使用Authorization头）：

1. **Authorization头（推荐）**

```text
Authorization: Bearer 你的API令牌
```

2. **X-API-Token头**

```text
X-API-Token: 你的API令牌
```

### 生成文本素描本图片

**请求**: POST /api/generate/text

**请求体（JSON）**:
```json
{
  "text": "要绘制的文本内容，可以包含表情标记（如#开心#、#生气#等）"
}
```

**参数说明**:
- `text`: 要绘制的文本内容，可以包含表情标记（如#开心#、#生气#等，多个标记时只使用最后一个）

**返回**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "img_url": "生成的图片URL",
    "filename": "生成的图片文件名"
  }
}
```

### 上传图片生成素描本图片

**请求**: POST /api/generate/image

**参数**: form-data
- `image`: 要上传的图片文件

**返回**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "img_url": "生成的图片URL",
    "filename": "生成的图片文件名"
  }
}
```

### 生成Base64格式素描本图片

**请求**: POST /api/generate/base64

**请求体（JSON）**:
```json
{
  "text": "要绘制的文本内容"
}
```
或
```json
{
  "image_base64": "Base64编码的图片"
}
```

**参数说明**:
- `text`: 可选，要绘制的文本内容
- `image_base64`: 可选，Base64编码的图片内容

**返回**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "base64": "生成的Base64图片内容",
    "filename": "生成的图片文件名"
  }
}
```

### 获取可用表情列表

**请求**: GET /api/emotions

**返回**:
```json
{
  "success": true,
  "emotions": ["普通", "开心", "生气", "无语", "脸红", "病娇"]
}
```

### 获取系统状态

**请求**: GET /api/status

**返回**:
```json
{
  "success": true,
  "app": "Anan's Sketchbook API",
  "version": "1.0.0",
  "status": "running",
  "timestamp": "当前时间戳"
}
```

### API文档

服务启动后，可以访问以下地址查看完整的API文档：
- Swagger UI: http://[host]:[port]/docs

## 开发说明

### 表情差分

在文本中使用特殊标签可以切换安安的表情：
- `#普通#`: 普通表情
- `#开心#`: 开心表情
- `#生气#`: 生气表情
- `#无语#`: 无语表情
- `#脸红#`: 脸红表情
- `#病娇#`: 病娇表情

### 特殊文本格式

- 使用`[]`或`【】`包裹的文本会显示为紫色

## 注意事项

- 字体文件`font.ttf`位于fonts目录，可以替换为其他字体
- 底图文件位于BaseImages目录，如需更换底图，请确保保持相同的分辨率
- 生成的图片默认保存在data/sketchbooks目录下，并会在配置的保留时间后自动删除
- 如需禁用图片自动删除功能，可将`file_config.temp_file_retention_seconds`设置为0

## 许可证

[MIT License](LICENSE)

## 更新记录

- 更新配置系统为TOML格式
- 优化路径处理，使用相对路径
- 统一配置和日志到data目录
- 重构核心代码结构
- 优化API认证机制，支持标准Authorization头
- 添加专业的错误处理机制
- 优化图片临时文件管理
- 添加Docker支持