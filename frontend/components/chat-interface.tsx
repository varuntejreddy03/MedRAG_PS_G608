"use client";

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Loader2, RefreshCw, Moon, Sun } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
// ScrollArea removed - using simple div
import { Badge } from '@/components/ui/badge';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isTyping?: boolean;
}

const TypingAnimation = ({ text, onComplete }: { text: string; onComplete?: () => void }) => {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayText(prev => prev + text[currentIndex]);
        setCurrentIndex(prev => prev + 1);
      }, 20);
      return () => clearTimeout(timer);
    } else {
      onComplete?.();
    }
  }, [currentIndex, text, onComplete]);

  return <span>{displayText}</span>;
};

const ThinkingDots = () => (
  <div className="flex space-x-1">
    {[0, 1, 2].map((i) => (
      <div
        key={i}
        className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce"
        style={{ animationDelay: `${i * 0.2}s` }}
      />
    ))}
  </div>
);

interface ChatInterfaceProps {
  onDiagnosis?: (diagnosis: any) => void;
  initialPrompt?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onDiagnosis, initialPrompt }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: initialPrompt || 'Hello! I\'m your MedRAG AI assistant. Brief responses only.',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [isDark, setIsDark] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Generate session ID
    setSessionId(`session_${Math.random().toString(36).substr(2, 9)}`);
  }, []);

  const sendMessage = useCallback(async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: `${inputValue}. Keep response under 50 words.`,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response,
        sender: 'bot',
        timestamp: new Date(),
        isTyping: true
      };

      setMessages(prev => [...prev, botMessage]);

      // If this looks like a diagnosis, trigger the callback
      if (onDiagnosis && data.response.includes('### Diagnosis')) {
        onDiagnosis({
          diagnosis: data.response.split('### Diagnosis')[1]?.split('###')[0]?.trim() || 'Analysis provided',
          reasoning: data.response,
          matches: data.matches || []
        });
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading, sessionId, onDiagnosis]);

  const clearChat = () => {
    setMessages([
      {
        id: '1',
        content: 'Hello! I\'m your MedRAG AI assistant. Please describe your symptoms or medical concerns, and I\'ll help analyze them.',
        sender: 'bot',
        timestamp: new Date()
      }
    ]);
    setSessionId(`session_${Math.random().toString(36).substr(2, 9)}`);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <Card className="h-full bg-slate-900/90 backdrop-blur-lg border-slate-700/30 shadow-2xl">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2 text-white text-base sm:text-lg">
            <Bot className="h-4 w-4 sm:h-5 sm:w-5 text-emerald-400" />
            MedRAG AI Assistant
          </CardTitle>
          <div className="flex gap-2 w-full sm:w-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsDark(!isDark)}
              className="bg-slate-800/50 border-slate-600/30 text-white hover:bg-slate-700/50"
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={clearChat}
              className="bg-slate-800/50 border-slate-600/30 text-white hover:bg-slate-700/50"
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Clear
            </Button>
          </div>
        </div>
        <Badge variant="secondary" className="w-fit bg-blue-500/20 text-blue-300 border-blue-500/30">
          Session: {sessionId.slice(-6)}
        </Badge>
      </CardHeader>
      <CardContent className="flex flex-col h-[calc(100%-120px)]">
        <div className="flex-1 pr-2 mb-4 overflow-y-auto" style={{maxHeight: 'calc(100vh - 300px)'}}>
          <div className="space-y-4">
            <AnimatePresence>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] sm:max-w-[80%] rounded-lg p-2 sm:p-3 text-sm sm:text-base ${
                      message.sender === 'user'
                        ? 'bg-emerald-600/80 text-white ml-2 sm:ml-4'
                        : 'bg-slate-800/80 text-white mr-2 sm:mr-4 border border-slate-600/20'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      {message.sender === 'bot' && (
                        <Bot className="h-4 w-4 text-blue-400 mt-0.5 flex-shrink-0" />
                      )}
                      {message.sender === 'user' && (
                        <User className="h-4 w-4 text-white mt-0.5 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <div className="text-sm whitespace-pre-wrap">
                          {message.isTyping ? (
                            <TypingAnimation 
                              text={message.content}
                              onComplete={() => {
                                setMessages(prev => 
                                  prev.map(m => 
                                    m.id === message.id ? { ...m, isTyping: false } : m
                                  )
                                );
                              }}
                            />
                          ) : (
                            message.content
                          )}
                        </div>
                        <div className="text-xs opacity-60 mt-1">
                          {message.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="bg-slate-800/80 text-white mr-4 border border-slate-600/20 rounded-lg p-3 max-w-[80%]">
                  <div className="flex items-center gap-2">
                    <Bot className="h-4 w-4 text-blue-400" />
                    <ThinkingDots />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
          <div ref={messagesEndRef} />
        </div>
        
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your symptoms..."
            className="flex-1 bg-slate-800/50 border-slate-600/30 text-white placeholder-slate-400"
            disabled={isLoading}
          />
          <Button
            onClick={sendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default ChatInterface;