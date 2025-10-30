package main

import (
	"bytes"
	"context"
	"fmt"

	"github.com/AssemblyAI/assemblyai-go-sdk"
)

type AssemblyAIService struct {
	client *assemblyai.Client
}

func NewAssemblyAIService(apiKey string) (*AssemblyAIService, error) {
	if apiKey == "" {
		return nil, fmt.Errorf("AssemblyAI API key is required")
	}

	client := assemblyai.NewClient(apiKey)
	return &AssemblyAIService{client: client}, nil
}

func (s *AssemblyAIService) TranscribeAudio(audioURL string) (string, error) {
	transcript, err := s.client.Transcripts.TranscribeFromURL(context.Background(), audioURL, &assemblyai.TranscriptOptionalParams{
		LanguageCode: assemblyai.TranscriptLanguageCode("zh"),
	})
	if err != nil {
		return "", fmt.Errorf("转录失败: %v", err)
	}

	return *transcript.Text, nil
}

func (s *AssemblyAIService) TranscribeAudioBytes(audioData []byte) (string, error) {
	reader := bytes.NewReader(audioData)
	params := &assemblyai.TranscriptOptionalParams{
		LanguageCode: assemblyai.TranscriptLanguageCode("zh"),
	}

	transcript, err := s.client.Transcripts.TranscribeFromReader(context.Background(), reader, params)
	if err != nil {
		return "", fmt.Errorf("转录失败: %v", err)
	}

	return *transcript.Text, nil
}
