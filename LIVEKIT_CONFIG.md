# LiveKit Docker 配置说明

## 配置文件概述

本项目使用 `livekit-docker.yaml` 作为 LiveKit 服务器的配置文件，该配置针对 Docker Compose 环境进行了优化。

## 主要配置项

### 1. 端口配置
```yaml
port: 7880                    # 主服务端口
rtc:
  port_range_start: 50000     # UDP 端口范围起始
  port_range_end: 50100       # UDP 端口范围结束（优化为100个端口）
  tcp_port: 7881              # TCP 备用端口
```

### 2. API 认证
```yaml
keys:
  devkey: devsecret          # 开发环境 API 密钥对
```

### 3. 网络优化
- **外部 IP 发现**: 启用 STUN 服务器自动发现公网 IP
- **拥塞控制**: 启用带宽管理和流量控制
- **TCP 回退**: 当 UDP 不可用时自动切换到 TCP
- **缓冲区优化**: 针对容器环境调整数据包缓冲区大小

### 4. 房间配置
- **自动创建房间**: 允许参与者加入时自动创建房间
- **超时设置**: 空房间5分钟后关闭，所有人离开后30秒关闭
- **编解码器**: 支持 Opus 音频和 VP8/H.264 视频
- **远程控制**: 允许远程取消静音

## Docker Compose 集成

### 服务配置
```yaml
livekit:
  command: ["--config", "/etc/livekit.yaml"]
  volumes:
    - ./livekit-docker.yaml:/etc/livekit.yaml:ro
  ports:
    - "7880:7880/tcp"
    - "7881:7881/tcp"
    - "50000-50100:50000-50100/udp"
```

### 环境变量统一
所有服务使用相同的 API 密钥对：
- `LIVEKIT_API_KEY=devkey`
- `LIVEKIT_API_SECRET=devsecret`

## 性能优化

### 1. 端口范围缩减
- 从原来的 10,000 个端口（50000-60000）缩减到 100 个端口（50000-50100）
- 减少防火墙配置复杂度
- 提高端口分配效率

### 2. 缓冲区调整
- 视频缓冲区: 300 个数据包（原 500）
- 音频缓冲区: 150 个数据包（原 200）
- 适合容器环境的内存使用

### 3. 日志优化
- 使用 JSON 格式便于容器日志解析
- 调整 Pion 日志级别减少噪音
- 开发模式下禁用采样

## 扩展配置

### Redis 集群（可选）
如需分布式部署，取消注释 Redis 配置：
```yaml
redis:
  address: redis:6379
  db: 0
```

### TURN 服务器（可选）
如需 NAT 穿透支持，启用 TURN 配置：
```yaml
turn:
  enabled: true
  udp_port: 3478
  tls_port: 5349
```

### 监控指标（可选）
启用 Prometheus 监控：
```yaml
prometheus_port: 6789
```

## 故障排除

### 1. 端口冲突
如果端口范围冲突，可以调整配置：
```yaml
rtc:
  port_range_start: 51000
  port_range_end: 51100
```

### 2. 网络连接问题
检查防火墙设置，确保以下端口开放：
- TCP: 7880, 7881
- UDP: 50000-50100

### 3. API 认证失败
确保所有服务使用相同的 API 密钥对，检查环境变量设置。

## 生产环境建议

1. **更改默认密钥**: 使用强密码替换 `devkey:devsecret`
2. **启用 TLS**: 配置 HTTPS 和 WSS 连接
3. **配置 Redis**: 启用分布式部署
4. **监控配置**: 启用 Prometheus 和日志聚合
5. **资源限制**: 根据负载调整缓冲区和连接限制