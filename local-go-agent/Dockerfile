# 使用官方Go镜像作为构建环境
FROM golang:1.21-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制go mod文件
COPY go.mod go.sum ./

# 下载依赖
RUN go mod download

# 复制源代码
COPY . .

# 构建应用
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# 使用轻量级镜像运行应用
FROM alpine:latest

# 安装ca-certificates用于HTTPS连接
RUN apk --no-cache add ca-certificates

WORKDIR /root/

# 从构建阶段复制二进制文件
COPY --from=builder /app/main .

# 设置环境变量
ENV LIVEKIT_URL=ws://livekit:7880
ENV LIVEKIT_API_KEY=APIcyMmEUQTDGnS
ENV LIVEKIT_API_SECRET=EfnCKnGxm8dyz8x7kia5UoP8coukwGmoVemUrBSiRBc
ENV ROOM_NAME=test-room
ENV PARTICIPANT_NAME=go-ai-agent

# 暴露端口（如果需要）
EXPOSE 8080

# 运行应用
CMD ["./main"]