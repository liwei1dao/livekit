package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	lksdk "github.com/livekit/server-sdk-go/v2"
	"github.com/pion/webrtc/v3"
	"github.com/sirupsen/logrus"
)

const (
	defaultLiveKitURL    = "ws://livekit:7880"
	defaultAPIKey        = "APIcyMmEUQTDGnS"
	defaultAPISecret     = "EfnCKnGxm8dyz8x7kia5UoP8coukwGmoVemUrBSiRBc"
	defaultRoomName      = "test-room"
	defaultParticipantID = "go-ai-agent"
)

type AIAgent struct {
	room         *lksdk.Room
	logger       *logrus.Logger
	participants map[string]*lksdk.RemoteParticipant
	ctx          context.Context
	cancel       context.CancelFunc
}

func NewAIAgent() *AIAgent {
	logger := logrus.New()
	logger.SetLevel(logrus.InfoLevel)

	ctx, cancel := context.WithCancel(context.Background())

	return &AIAgent{
		logger:       logger,
		participants: make(map[string]*lksdk.RemoteParticipant),
		ctx:          ctx,
		cancel:       cancel,
	}
}

func (a *AIAgent) Connect() error {
	// 获取环境变量
	liveKitURL := getEnv("LIVEKIT_URL", defaultLiveKitURL)
	apiKey := getEnv("LIVEKIT_API_KEY", defaultAPIKey)
	apiSecret := getEnv("LIVEKIT_API_SECRET", defaultAPISecret)
	roomName := getEnv("ROOM_NAME", defaultRoomName)
	participantID := getEnv("PARTICIPANT_NAME", defaultParticipantID)

	a.logger.Infof("连接到LiveKit服务器: %s", liveKitURL)
	a.logger.Infof("房间名称: %s", roomName)
	a.logger.Infof("参与者ID: %s", participantID)

	// 创建房间连接
	room, err := lksdk.ConnectToRoom(liveKitURL, lksdk.ConnectInfo{
		APIKey:              apiKey,
		APISecret:           apiSecret,
		RoomName:            roomName,
		ParticipantIdentity: participantID,
		ParticipantName:     "AI助手",
	}, &lksdk.RoomCallback{
		ParticipantCallback: lksdk.ParticipantCallback{
			OnTrackSubscribed: a.onTrackSubscribed,
		},
		OnParticipantConnected:    a.onParticipantConnected,
		OnParticipantDisconnected: a.onParticipantDisconnected,
		OnDisconnected:            a.onRoomDisconnected,
	})

	if err != nil {
		return fmt.Errorf("连接房间失败: %w", err)
	}

	a.room = room
	a.logger.Info("成功连接到LiveKit房间")

	// 发送欢迎消息
	go a.sendWelcomeMessage()

	return nil
}

func (a *AIAgent) sendWelcomeMessage() {
	time.Sleep(2 * time.Second) // 等待连接稳定

	welcomeMsg := "你好！我是你的AI助手，有什么可以帮助你的吗？"

	// 发送文本消息
	err := a.room.LocalParticipant.PublishData([]byte(welcomeMsg))
	if err != nil {
		a.logger.Errorf("发送欢迎消息失败: %v", err)
		return
	}

	a.logger.Info("已发送欢迎消息")
}

func (a *AIAgent) onParticipantConnected(participant *lksdk.RemoteParticipant) {
	a.logger.Infof("参与者加入: %s (%s)", participant.Name(), participant.Identity())
	a.participants[participant.Identity()] = participant

	// 向新参与者发送欢迎消息
	welcomeMsg := fmt.Sprintf("欢迎 %s 加入房间！", participant.Name())
	err := a.room.LocalParticipant.PublishData([]byte(welcomeMsg))
	if err != nil {
		a.logger.Errorf("发送个人欢迎消息失败: %v", err)
	}
}

func (a *AIAgent) onParticipantDisconnected(participant *lksdk.RemoteParticipant) {
	a.logger.Infof("参与者离开: %s (%s)", participant.Name(), participant.Identity())
	delete(a.participants, participant.Identity())
}

func (a *AIAgent) onTrackSubscribed(track *webrtc.TrackRemote, publication *lksdk.RemoteTrackPublication, participant *lksdk.RemoteParticipant) {
	a.logger.Infof("订阅轨道: %s 来自 %s", publication.Name(), participant.Identity())

	if publication.Kind() == lksdk.TrackKindAudio {
		a.logger.Info("开始处理音频轨道")
		go a.processAudioTrack(track, participant)
	}
}

func (a *AIAgent) processAudioTrack(track *webrtc.TrackRemote, participant *lksdk.RemoteParticipant) {
	a.logger.Infof("处理来自 %s 的音频轨道", participant.Identity())

	// 这里应该实现STT处理
	// 现在只是记录接收到音频轨道
	for {
		select {
		case <-a.ctx.Done():
			return
		default:
			// 模拟音频处理
			time.Sleep(1 * time.Second)
			// 这里应该调用STT服务将音频转换为文本
			// 然后调用LLM生成回复
			// 最后调用TTS生成语音回复

			// 模拟处理后发送回复
			reply := "我听到了你的声音，但目前只能发送文本回复。"
			err := a.room.LocalParticipant.PublishData([]byte(reply))
			if err != nil {
				a.logger.Errorf("发送音频处理回复失败: %v", err)
			} else {
				a.logger.Infof("已回复音频消息给 %s", participant.Identity())
			}

			// 避免频繁发送
			time.Sleep(5 * time.Second)
		}
	}
}

func (a *AIAgent) onRoomDisconnected() {
	a.logger.Info("与房间断开连接")
	a.cancel()
}

func (a *AIAgent) Disconnect() {
	if a.room != nil {
		a.room.Disconnect()
	}
	a.cancel()
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func main() {
	log.Println("启动LiveKit Go AI代理...")

	agent := NewAIAgent()

	// 连接到LiveKit
	if err := agent.Connect(); err != nil {
		log.Fatalf("连接失败: %v", err)
	}

	// 等待中断信号
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	log.Println("AI代理已启动，等待连接...")
	<-sigChan

	log.Println("正在关闭AI代理...")
	agent.Disconnect()
	log.Println("AI代理已关闭")
}
