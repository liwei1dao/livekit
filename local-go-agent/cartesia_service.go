package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
)

type CartesiaService struct {
	apiKey  string
	baseURL string
	client  *http.Client
}

type CartesiaRequest struct {
	ModelID    string                 `json:"model_id"`
	Transcript string                 `json:"transcript"`
	Voice      map[string]interface{} `json:"voice"`
	OutputFormat map[string]interface{} `json:"output_format"`
}

func NewCartesiaService(apiKey string) *CartesiaService {
	return &CartesiaService{
		apiKey:  apiKey,
		baseURL: "https://api.cartesia.ai",
		client:  &http.Client{},
	}
}

func (s *CartesiaService) TextToSpeech(ctx context.Context, text string) ([]byte, error) {
	log.Printf("正在使用Cartesia将文字转换为语音: %s", text)
	
	// 构建请求数据
	requestData := CartesiaRequest{
		ModelID:    "sonic-english", // 使用Sonic模型
		Transcript: text,
		Voice: map[string]interface{}{
			"mode": "id",
			"id":   "a0e99841-438c-4a64-b679-ae501e7d6091", // 默认声音ID
		},
		OutputFormat: map[string]interface{}{
			"container":   "raw",
			"encoding":    "pcm_f32le",
			"sample_rate": 22050,
		},
	}
	
	jsonData, err := json.Marshal(requestData)
	if err != nil {
		return nil, fmt.Errorf("序列化请求数据失败: %v", err)
	}
	
	// 创建HTTP请求
	req, err := http.NewRequestWithContext(ctx, "POST", s.baseURL+"/tts/bytes", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("创建HTTP请求失败: %v", err)
	}
	
	// 设置请求头
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", s.apiKey)
	req.Header.Set("Cartesia-Version", "2024-06-10")
	
	// 发送请求
	resp, err := s.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("发送HTTP请求失败: %v", err)
	}
	defer resp.Body.Close()
	
	// 检查响应状态
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("Cartesia API返回错误状态 %d: %s", resp.StatusCode, string(body))
	}
	
	// 读取音频数据
	audioData, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("读取音频数据失败: %v", err)
	}
	
	log.Printf("Cartesia文字转语音完成，音频数据大小: %d bytes", len(audioData))
	return audioData, nil
}

func (s *CartesiaService) TextToSpeechWithVoice(ctx context.Context, text string, voiceID string) ([]byte, error) {
	log.Printf("正在使用Cartesia将文字转换为语音，声音ID: %s, 文字: %s", voiceID, text)
	
	// 构建请求数据
	requestData := CartesiaRequest{
		ModelID:    "sonic-english",
		Transcript: text,
		Voice: map[string]interface{}{
			"mode": "id",
			"id":   voiceID,
		},
		OutputFormat: map[string]interface{}{
			"container":   "raw",
			"encoding":    "pcm_f32le",
			"sample_rate": 22050,
		},
	}
	
	jsonData, err := json.Marshal(requestData)
	if err != nil {
		return nil, fmt.Errorf("序列化请求数据失败: %v", err)
	}
	
	// 创建HTTP请求
	req, err := http.NewRequestWithContext(ctx, "POST", s.baseURL+"/tts/bytes", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("创建HTTP请求失败: %v", err)
	}
	
	// 设置请求头
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", s.apiKey)
	req.Header.Set("Cartesia-Version", "2024-06-10")
	
	// 发送请求
	resp, err := s.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("发送HTTP请求失败: %v", err)
	}
	defer resp.Body.Close()
	
	// 检查响应状态
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("Cartesia API返回错误状态 %d: %s", resp.StatusCode, string(body))
	}
	
	// 读取音频数据
	audioData, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("读取音频数据失败: %v", err)
	}
	
	log.Printf("Cartesia文字转语音完成，音频数据大小: %d bytes", len(audioData))
	return audioData, nil
}