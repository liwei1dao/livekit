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

	// AI服务
	openaiService     *OpenAIService
	assemblyaiService *AssemblyAIService
	cartesiaService   *CartesiaService
}

func NewAIAgent() *AIAgent {
	logger := logrus.New()
	logger.SetLevel(logrus.InfoLevel)

	ctx, cancel := context.WithCancel(context.Background())

	// 初始化AI服务
	var openaiService *OpenAIService
	var assemblyaiService *AssemblyAIService
	var cartesiaService *CartesiaService

	// 从环境变量获取API密钥
	if openaiKey := os.Getenv("OPENAI_API_KEY"); openaiKey != "" {
		var err error
		openaiService, err = NewOpenAIService(openaiKey)
		if err != nil {
			logger.Errorf("初始化OpenAI服务失败: %v", err)
		} else {
			logger.Info("OpenAI服务已初始化")
		}
	} else {
		logger.Warn("未设置OPENAI_API_KEY环境变量，OpenAI服务将不可用")
	}

	if assemblyaiKey := os.Getenv("ASSEMBLYAI_API_KEY"); assemblyaiKey != "" {
		var err error
		assemblyaiService, err = NewAssemblyAIService(assemblyaiKey)
		if err != nil {
			logger.Errorf("初始化AssemblyAI服务失败: %v", err)
		} else {
			logger.Info("AssemblyAI服务已初始化")
		}
	} else {
		logger.Warn("未设置ASSEMBLYAI_API_KEY环境变量，AssemblyAI服务将不可用")
	}

	if cartesiaKey := os.Getenv("CARTESIA_API_KEY"); cartesiaKey != "" {
		cartesiaService = NewCartesiaService(cartesiaKey)
		logger.Info("Cartesia服务已初始化")
	} else {
		logger.Warn("未设置CARTESIA_API_KEY环境变量，Cartesia服务将不可用")
	}

	return &AIAgent{
		logger:            logger,
		participants:      make(map[string]*lksdk.RemoteParticipant),
		ctx:               ctx,
		cancel:            cancel,
		openaiService:     openaiService,
		assemblyaiService: assemblyaiService,
		cartesiaService:   cartesiaService,
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

	// 音频缓冲区
	audioBuffer := make([]byte, 0)
	bufferDuration := 3 * time.Second // 收集3秒的音频数据
	lastProcessTime := time.Now()

	for {
		select {
		case <-a.ctx.Done():
			return
		default:
			// 读取音频数据
			rtpPacket, _, err := track.ReadRTP()
			if err != nil {
				a.logger.Errorf("读取RTP包失败: %v", err)
				continue
			}

			// 将RTP包的payload添加到缓冲区
			audioBuffer = append(audioBuffer, rtpPacket.Payload...)

			// 检查是否应该处理音频
			if time.Since(lastProcessTime) >= bufferDuration && len(audioBuffer) > 0 {
				go a.processAudioBuffer(audioBuffer, participant)
				audioBuffer = make([]byte, 0) // 清空缓冲区
				lastProcessTime = time.Now()
			}
		}
	}
}

func (a *AIAgent) processAudioBuffer(audioData []byte, participant *lksdk.RemoteParticipant) {
	a.logger.Infof("开始处理音频数据，大小: %d bytes", len(audioData))

	// 步骤1: 语音转文字 (STT)
	var transcription string
	if a.assemblyaiService != nil {
		var err error
		transcription, err = a.assemblyaiService.TranscribeAudioBytes(audioData)
		if err != nil {
			a.logger.Errorf("语音转文字失败: %v", err)
			// 发送错误消息
			a.sendTextMessage("抱歉，我无法理解您说的话。")
			return
		}
		a.logger.Infof("转录结果: %s", transcription)
	} else {
		a.logger.Warn("AssemblyAI服务不可用，跳过语音转文字")
		a.sendTextMessage("抱歉，语音识别服务暂时不可用。")
		return
	}

	// 如果转录结果为空或太短，跳过处理
	if len(transcription) < 3 {
		a.logger.Info("转录结果太短，跳过处理")
		return
	}

	// 步骤2: 生成AI回复 (LLM)
	var aiResponse string
	if a.openaiService != nil {
		var err error
		systemMessage := "你是一个友好的AI助手，请用中文回复用户的问题。回复要简洁明了。"
		aiResponse, err = a.openaiService.GenerateResponse(systemMessage, transcription, 150, 0.7)
		if err != nil {
			a.logger.Errorf("生成AI回复失败: %v", err)
			aiResponse = "抱歉，我现在无法生成回复。"
		}
		a.logger.Infof("AI回复: %s", aiResponse)
	} else {
		a.logger.Warn("OpenAI服务不可用，使用默认回复")
		aiResponse = fmt.Sprintf("我听到您说：%s。但是AI服务暂时不可用。", transcription)
	}

	// 步骤3: 文字转语音 (TTS)
	if a.cartesiaService != nil {
		audioResponse, err := a.cartesiaService.TextToSpeech(a.ctx, aiResponse)
		if err != nil {
			a.logger.Errorf("文字转语音失败: %v", err)
			// 如果TTS失败，发送文本消息
			a.sendTextMessage(aiResponse)
		} else {
			// 发送音频回复
			a.sendAudioMessage(audioResponse, participant)
		}
	} else {
		a.logger.Warn("Cartesia服务不可用，发送文本回复")
		// 发送文本消息
		a.sendTextMessage(aiResponse)
	}
}

func (a *AIAgent) sendTextMessage(message string) {
	err := a.room.LocalParticipant.PublishData([]byte(message))
	if err != nil {
		a.logger.Errorf("发送文本消息失败: %v", err)
	} else {
		a.logger.Infof("已发送文本消息: %s", message)
	}
}

func (a *AIAgent) sendAudioMessage(audioData []byte, participant *lksdk.RemoteParticipant) {
	a.logger.Infof("准备发送音频回复，大小: %d bytes", len(audioData))

	// 这里需要将音频数据转换为适合LiveKit的格式
	// 由于这是一个复杂的过程，现在先发送文本通知
	textNotification := "🎵 AI正在生成语音回复..."
	a.sendTextMessage(textNotification)

	// TODO: 实现音频轨道发布
	// 这需要创建音频轨道并发布到房间
	a.logger.Info("音频回复功能正在开发中，已发送文本通知")
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
