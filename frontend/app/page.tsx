'use client';

import { useChat } from 'ai/react';
import { useEffect, useRef, useState } from 'react';
import { 
  PaperAirplaneIcon, 
  UserCircleIcon,
  SparklesIcon,
  XMarkIcon,
  ArrowPathIcon
} from '@heroicons/react/24/solid';

// Message Component
function Message({ role, content }: { role: string; content: string }) {
  const isUser = role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className="flex items-end gap-2 max-w-[85%] md:max-w-[70%]">
        {!isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-sky-400 to-blue-500 flex items-center justify-center">
            <SparklesIcon className="w-5 h-5 text-white" />
          </div>
        )}
        <div className={`message-bubble ${isUser ? 'message-user' : 'message-assistant'}`}>
          <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
        {isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-400 to-pink-500 flex items-center justify-center">
            <UserCircleIcon className="w-5 h-5 text-white" />
          </div>
        )}
      </div>
    </div>
  );
}

// Typing Indicator Component
function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="flex items-end gap-2 max-w-[70%]">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-sky-400 to-blue-500 flex items-center justify-center">
          <SparklesIcon className="w-5 h-5 text-white" />
        </div>
        <div className="message-bubble message-assistant">
          <div className="typing-indicator">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Welcome Message Component
function WelcomeMessage() {
  const suggestions = [
    "Book a car wash",
    "Check service packages",
    "Schedule maintenance",
    "Get a quote"
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full p-8 animate-fade-in">
      <div className="bg-gradient-to-br from-sky-500 to-blue-600 w-20 h-20 rounded-full flex items-center justify-center mb-6 shadow-lg">
        <SparklesIcon className="w-10 h-10 text-white" />
      </div>
      <h1 className="text-3xl md:text-4xl font-bold text-center mb-3 bg-gradient-to-r from-sky-600 to-blue-600 bg-clip-text text-transparent">
        Yawlit AI Assistant
      </h1>
      <p className="text-gray-500 dark:text-gray-400 text-center mb-8 max-w-md">
        Your intelligent car service companion. Ask me anything about bookings, services, or maintenance!
      </p>
      <div className="grid grid-cols-2 gap-3 w-full max-w-lg">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            className="px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-sky-500 hover:bg-sky-50 dark:hover:bg-sky-900/20 transition-all text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit, isLoading, stop, reload } = useChat({
    api: `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/chat`,
    onResponse: (response) => {
      console.log('🔄 Response received', { status: response.status });
    },
    onFinish: (message) => {
      console.log('✅ Message finished', { id: message.id });
    },
    onError: (error) => {
      console.error('❌ Chat error', error);
    }
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Handle scroll button visibility
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      setShowScrollButton(scrollHeight - scrollTop - clientHeight > 100);
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    handleSubmit(e);
    inputRef.current?.focus();
  };

  const handleClearChat = () => {
    if (confirm('Clear all messages?')) {
      reload();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-700 px-4 py-4 md:px-6 shadow-sm">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-sky-500 to-blue-600 w-10 h-10 rounded-xl flex items-center justify-center shadow-lg">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">Yawlit AI</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {isLoading ? 'Thinking...' : 'Online'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={handleClearChat}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                title="Clear chat"
              >
                <XMarkIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Messages Container */}
      <main 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6 md:px-6"
      >
        <div className="max-w-5xl mx-auto">
          {messages.length === 0 ? (
            <WelcomeMessage />
          ) : (
            <>
              {messages.map((message) => (
                <Message key={message.id} role={message.role} content={message.content} />
              ))}
              {isLoading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Scroll to Bottom Button */}
        {showScrollButton && (
          <button
            onClick={scrollToBottom}
            className="fixed bottom-28 right-8 bg-white dark:bg-gray-800 p-3 rounded-full shadow-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all"
          >
            <ArrowPathIcon className="w-5 h-5 text-gray-600 dark:text-gray-400 rotate-90" />
          </button>
        )}
      </main>

      {/* Input Form */}
      <footer className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg border-t border-gray-200 dark:border-gray-700 px-4 py-4 md:px-6 shadow-lg">
        <form onSubmit={handleFormSubmit} className="max-w-5xl mx-auto">
          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={handleInputChange}
                placeholder="Type your message..."
                disabled={isLoading}
                className="w-full px-4 py-3 pr-12 rounded-2xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 input-focus disabled:opacity-50 disabled:cursor-not-allowed text-sm md:text-base"
                autoComplete="off"
              />
              {input && (
                <button
                  type="button"
                  onClick={() => {
                    handleInputChange({ target: { value: '' } } as any);
                    inputRef.current?.focus();
                  }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <XMarkIcon className="w-4 h-4 text-gray-400" />
                </button>
              )}
            </div>
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="btn-primary px-6 py-3 rounded-2xl font-medium text-sm md:text-base flex items-center gap-2 shadow-md"
            >
              <PaperAirplaneIcon className="w-5 h-5" />
              <span className="hidden md:inline">{isLoading ? 'Sending...' : 'Send'}</span>
            </button>
          </div>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-2 text-center">
            Powered by AI • Always learning to serve you better
          </p>
        </form>
      </footer>
    </div>
  );
}
