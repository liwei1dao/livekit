package main

import (
	"context"
	"fmt"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/option"
)

type OpenAIService struct {
	client openai.Client
}

func NewOpenAIService(apiKey string) (*OpenAIService, error) {
	if apiKey == "" {
		return nil, fmt.Errorf("OpenAI API key is required")
	}

	client := openai.NewClient(option.WithAPIKey(apiKey))
	return &OpenAIService{client: client}, nil
}

func (s *OpenAIService) GenerateResponse(systemMessage, userMessage string, maxTokens int, temperature float64) (string, error) {
	ctx := context.Background()

	params := openai.ChatCompletionNewParams{
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage(systemMessage),
			openai.UserMessage(userMessage),
		},
		Model: openai.ChatModelGPT3_5Turbo,
		// 暂时省略MaxTokens和Temperature参数，使用默认值
	}

	completion, err := s.client.Chat.Completions.New(ctx, params)
	if err != nil {
		return "", fmt.Errorf("failed to generate response: %w", err)
	}

	if len(completion.Choices) == 0 {
		return "", fmt.Errorf("no response generated")
	}

	return completion.Choices[0].Message.Content, nil
}
