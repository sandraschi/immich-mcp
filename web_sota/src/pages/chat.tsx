import { API_BASE } from "@/lib/api";
import { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
    Send, 
    Bot, 
    User, 
    Sparkles, 
    Cpu, 
    ChevronDown, 
    Layers,
    Loader2
} from "lucide-react";
import { 
    DropdownMenu, 
    DropdownMenuContent, 
    DropdownMenuItem, 
    DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    provider?: string;
    model?: string;
}

interface LLMProvider {
    id: string;
    name: string;
    url: string;
}

export function Chat() {
    const [messages, setMessages] = useState<Message[]>([
        { 
            role: 'assistant', 
            content: "Hello! I'm your Immich AI assistant. How can I help you with your photo library today?",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [providers, setProviders] = useState<LLMProvider[]>([]);
    const [selectedProvider, setSelectedProvider] = useState<string>("ollama");
    const [models, setModels] = useState<string[]>([]);
    const [selectedModel, setSelectedModel] = useState<string>("");
    
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Fetch providers
        fetch(API_BASE + "/api/v1/llm/providers")
            .then(res => res.json())
            .then(data => {
                if (data.success) setProviders(data.providers);
            });
    }, []);

    useEffect(() => {
        // Fetch models for provider
        fetch(API_BASE + `/api/v1/llm/models?provider=${selectedProvider}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    setModels(data.models);
                    if (data.models.length > 0) setSelectedModel(data.models[0]);
                }
            });
    }, [selectedProvider]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMsg: Message = {
            role: 'user',
            content: input,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const res = await fetch(API_BASE + "/api/v1/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: input,
                    provider: selectedProvider,
                    model: selectedModel
                })
            });
            const data = await res.json();
            
            if (data.success) {
                const assistantMsg: Message = {
                    role: 'assistant',
                    content: data.response,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    provider: selectedProvider,
                    model: selectedModel
                };
                setMessages(prev => [...prev, assistantMsg]);
            }
        } catch (err) {
            console.error("Chat error", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                        <Sparkles className="h-6 w-6 text-indigo-400" />
                        Immich AI Assistant
                    </h2>
                    <p className="text-slate-400">Natural language photo management and search</p>
                </div>
                
                <div className="flex gap-2">
                    {/* Provider Selector */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline" size="sm" className="border-slate-800 bg-slate-900 text-slate-300">
                                <Layers className="h-4 w-4 mr-2 text-indigo-400" />
                                {providers.find(p => p.id === selectedProvider)?.name || "Select Provider"}
                                <ChevronDown className="h-4 w-4 ml-2 opacity-50" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="bg-slate-900 border-slate-800 text-slate-200">
                            {providers.map(p => (
                                <DropdownMenuItem 
                                    key={p.id} 
                                    onClick={() => setSelectedProvider(p.id)}
                                    className="focus:bg-slate-800 focus:text-white"
                                >
                                    {p.name}
                                </DropdownMenuItem>
                            ))}
                        </DropdownMenuContent>
                    </DropdownMenu>

                    {/* Model Selector */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline" size="sm" className="border-slate-800 bg-slate-900 text-slate-300">
                                <Cpu className="h-4 w-4 mr-2 text-emerald-400" />
                                {selectedModel || "Select Model"}
                                <ChevronDown className="h-4 w-4 ml-2 opacity-50" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="bg-slate-900 border-slate-800 text-slate-200 max-h-64 overflow-y-auto">
                            {models.map(m => (
                                <DropdownMenuItem 
                                    key={m} 
                                    onClick={() => setSelectedModel(m)}
                                    className="focus:bg-slate-800 focus:text-white"
                                >
                                    {m}
                                </DropdownMenuItem>
                            ))}
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>

            <Card className="flex-1 border-slate-800 bg-black/40 backdrop-blur-md flex flex-col overflow-hidden shadow-2xl">
                <CardContent className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth">
                    <div ref={scrollRef} className="space-y-6">
                        {messages.map((msg, i) => (
                            <div key={i} className={`flex gap-4 ${msg.role === 'assistant' ? '' : 'flex-row-reverse'}`}>
                                <div className={`h-10 w-10 rounded-full flex items-center justify-center border shrink-0 ${
                                    msg.role === 'assistant' 
                                        ? 'bg-indigo-900/20 border-indigo-500/30' 
                                        : 'bg-slate-800 border-slate-700'
                                }`}>
                                    {msg.role === 'assistant' ? <Bot className="h-5 w-5 text-indigo-400" /> : <User className="h-5 w-5 text-slate-400" />}
                                </div>
                                <div className={`flex flex-col space-y-1 max-w-[80%] ${msg.role === 'assistant' ? '' : 'items-end'}`}>
                                    <div className="flex items-center gap-2 px-1">
                                        <span className="text-xs font-medium text-slate-400">
                                            {msg.role === 'assistant' ? 'Immich AI' : 'Operator'}
                                        </span>
                                        <span className="text-[10px] text-slate-600">{msg.timestamp}</span>
                                    </div>
                                    <div className={`text-sm p-4 rounded-2xl border ${
                                        msg.role === 'assistant' 
                                            ? 'bg-slate-900/50 border-slate-800 text-slate-200 rounded-tl-none' 
                                            : 'bg-indigo-600 border-indigo-500 text-white rounded-tr-none'
                                    }`}>
                                        {msg.content}
                                        {msg.provider && (
                                            <div className="mt-2 pt-2 border-t border-slate-800 flex items-center gap-2 text-[10px] text-slate-500">
                                                <Cpu className="h-3 w-3" />
                                                <span>Inference: {msg.provider} / {msg.model}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex gap-4 animate-pulse">
                                <div className="h-10 w-10 rounded-full bg-indigo-900/20 border border-indigo-500/30 flex items-center justify-center">
                                    <Loader2 className="h-5 w-5 text-indigo-400 animate-spin" />
                                </div>
                                <div className="space-y-2 flex-1">
                                    <div className="h-4 bg-slate-800 rounded w-1/4"></div>
                                    <div className="h-16 bg-slate-900/50 rounded-2xl w-1/2"></div>
                                </div>
                            </div>
                        )}
                    </div>
                </CardContent>
                
                <div className="p-4 border-t border-slate-800 bg-slate-900/50 backdrop-blur-xl">
                    <div className="flex gap-2 max-w-4xl mx-auto">
                        <textarea
                            rows={1}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend();
                                }
                            }}
                            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-none transition-all"
                            placeholder="Ask Immich AI to find photos, create albums, or analyze people..."
                        />
                        <Button 
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                            className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl px-6 h-auto"
                        >
                            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                        </Button>
                    </div>
                </div>
            </Card>
        </div>
    );
}
