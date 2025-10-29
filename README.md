# LiveKit 实时音视频应用

这是一个基于 LiveKit 的实时音视频应用，包含 LiveKit 服务器、Python 代理和 React Web 前端。

## 项目结构

```
├── agent-starter-python/    # Python 代理服务
├── agent-starter-react/     # React Web 前端
├── livekit/                 # LiveKit 服务器源码
├── docker-compose.yml       # Docker Compose 配置
├── livekit-docker.yaml      # LiveKit 服务器配置
└── README.md               # 项目说明文档
```

## 功能特性

- 🎥 实时音视频通信
- 🤖 AI 代理集成 (支持 OpenAI、AssemblyAI、Cartesia)
- 🌐 现代化 Web 界面
- 🐳 Docker 容器化部署
- 🔧 开发环境热重载

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- Git

### 安装和运行

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd livekit
   ```

2. **启动所有服务**
   ```bash
   docker compose up -d
   ```

3. **访问应用**
   - Web 应用: http://localhost:3000
   - LiveKit 服务器: ws://localhost:7880

### 服务说明

#### LiveKit 服务器
- **端口**: 7880 (HTTP/WebSocket), 7881 (RTC TCP)
- **UDP 端口范围**: 50000-50100
- **配置文件**: `livekit-docker.yaml`

#### Python 代理服务
- **容器名**: `agent-python`
- **功能**: AI 代理处理和实时交互
- **支持的 AI 服务**: OpenAI, AssemblyAI, Cartesia

#### React Web 前端
- **端口**: 3000
- **容器名**: `agent-react`
- **功能**: 用户界面和实时音视频交互

## 配置

### API 密钥配置

项目已预配置了开发用的 API 密钥：
- **API Key**: `APIcyMmEUQTDGnS`
- **API Secret**: `EfnCKnGxm8dyz8x7kia5UoP8coukwGmoVemUrBSiRBc`

### 环境变量 (可选)

如需使用 AI 服务，请在主机环境中设置以下变量：

```bash
export OPENAI_API_KEY=your_openai_key
export ASSEMBLYAI_API_KEY=your_assemblyai_key
export CARTESIA_API_KEY=your_cartesia_key
```

## 开发

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f livekit
docker compose logs -f agent
docker compose logs -f web
```

### 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart livekit
```

### 停止服务

```bash
docker compose down
```

## 故障排除

### LiveKit 服务器无法启动
1. 检查端口是否被占用 (7880, 7881, 50000-50100)
2. 查看服务日志: `docker logs livekit-server`
3. 确认配置文件格式正确

### 代理服务连接失败
1. 确认 LiveKit 服务器正在运行
2. 检查 API 密钥配置是否正确
3. 查看代理服务日志

### Web 应用无法访问
1. 确认端口 3000 未被占用
2. 检查容器是否正常运行: `docker compose ps`

## 技术栈

- **后端**: LiveKit (Go), Python
- **前端**: React, Next.js, TypeScript
- **容器化**: Docker, Docker Compose
- **实时通信**: WebRTC, WebSocket

## 许可证

本项目遵循相应的开源许可证，详见各子项目的 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进项目。

## 相关链接

- [LiveKit 官方文档](https://docs.livekit.io/)
- [LiveKit GitHub](https://github.com/livekit/livekit)