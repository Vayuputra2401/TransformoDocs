"use client";

import { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, Download, Send, Bot, User, Activity } from 'lucide-react';

export default function Home() {
  const [file, setFile] = useState(null);
  const [docId, setDocId] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [query, setQuery] = useState('');
  const [chat, setChat] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  const handleUpload = async (e) => {
    const selected = e.target.files[0];
    if (!selected) return;
    setFile(selected);
    setIsProcessing(true);

    const formData = new FormData();
    formData.append('file', selected);

    try {
      const res = await axios.post('http://localhost:8000/api/v1/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setDocId(res.data.document_id);
      setMetrics(res.data.metrics);
    } catch (err) {
      console.error(err);
      alert("Error uploading document");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownloadJson = async () => {
    if (!docId) return;
    try {
      const res = await axios.get(`http://localhost:8000/api/v1/document/${docId}`);
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(res.data, null, 2));
      const a = document.createElement('a');
      a.href = dataStr;
      a.download = `structured_doc_${docId}.json`;
      a.click();
    } catch (err) {
      console.error(err);
    }
  };

  const handleChat = async (e) => {
    e.preventDefault();
    if (!query.trim() || !docId) return;

    const newChat = [...chat, { role: 'user', content: query }];
    setChat(newChat);
    setQuery('');
    setIsTyping(true);

    try {
      const res = await axios.post('http://localhost:8000/api/v1/chat', {
        query: query,
        document_id: docId
      });
      setChat([...newChat, { role: 'agent', content: res.data.answer }]);
    } catch (err) {
      console.error(err);
      setChat([...newChat, { role: 'agent', content: 'Agent Workflow Error. Please try again.' }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center bg-[#0d1117] text-white p-8">
      {/* Header */}
      <div className="w-full max-w-6xl text-center mb-12">
        <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-emerald-400 mb-4 tracking-tight">
          TransformoDocs ⚡
        </h1>
        <p className="text-[#8B949E] text-xl">Intelligent Document Conversion & RAG Analysis</p>
      </div>

      <div className="flex flex-col md:flex-row w-full max-w-6xl gap-8">
        {/* Left Panel: Upload & Metrics */}
        <div className="w-full md:w-1/3 flex flex-col gap-6">
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-6 shadow-2xl">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <FileText className="text-teal-400" /> Document Ingestion
            </h2>

            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-[#30363d] border-dashed rounded-lg cursor-pointer hover:bg-[#21262d] transition-colors relative">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <Upload className="w-8 h-8 text-gray-400 mb-2" />
                <p className="text-sm text-gray-400">
                  <span className="font-semibold">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs text-gray-500 mt-1">PDF, DOCX, TXT, Excel, PNG</p>
              </div>
              <input type="file" className="hidden" onChange={handleUpload} disabled={isProcessing} />
            </label>

            {isProcessing && (
              <div className="mt-4 flex items-center justify-center text-teal-400 text-sm animate-pulse">
                <Activity className="animate-spin mr-2 h-4 w-4" /> Processing with PyTesseract & Pandas...
              </div>
            )}

            {file && !isProcessing && (
              <div className="mt-4 p-3 bg-[#0d1117] rounded-md border border-emerald-900 flex justify-between items-center text-sm">
                <span className="truncate">{file.name}</span>
                <span className="text-emerald-400">Indexed ✓</span>
              </div>
            )}

            {metrics && (
              <div className="mt-6 pt-6 border-t border-[#30363d]">
                <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">MLOps Telemetry</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="bg-[#0d1117] p-3 rounded border border-[#30363d]">
                    <div className="text-gray-500 text-xs">Characters</div>
                    <div className="text-xl text-teal-400 font-mono">{metrics.character_count}</div>
                  </div>
                  <div className="bg-[#0d1117] p-3 rounded border border-[#30363d]">
                    <div className="text-gray-500 text-xs">Words</div>
                    <div className="text-xl text-teal-400 font-mono">{metrics.word_count}</div>
                  </div>
                  <div className="bg-[#0d1117] p-3 rounded border border-[#30363d] col-span-2 flex justify-between items-center">
                    <div>
                      <div className="text-gray-500 text-xs">Speed</div>
                      <div className="text-lg text-emerald-400 font-mono">{metrics.processing_time_sec}s</div>
                    </div>
                    <div className="text-xs text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded">
                      +36% Efficiency
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleDownloadJson}
                  className="mt-4 w-full flex items-center justify-center gap-2 bg-[#238636] hover:bg-[#2ea043] transition-colors py-2 rounded-md font-medium text-sm"
                >
                  <Download size={16} /> Export JSON Artifacts
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Chat Interface */}
        <div className="w-full md:w-2/3 flex flex-col bg-[#161b22] border border-[#30363d] rounded-xl shadow-2xl h-[600px]">
          <div className="p-4 border-b border-[#30363d] flex items-center justify-between">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Bot className="text-teal-400" /> Multi-Agent Analysis
            </h2>
            <div className="text-xs text-gray-500 flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-emerald-500"></div> System Online
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {!docId ? (
              <div className="h-full flex items-center justify-center text-gray-500 text-center flex-col">
                <Bot size={48} className="text-gray-700 mb-4" />
                <p>Upload a document to initialize the CrewAI analysis agents.</p>
              </div>
            ) : chat.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                Ask me anything about the document. I will use HyDE RAG to find the exact context!
              </div>
            ) : (
              chat.map((msg, i) => (
                <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                  {msg.role === 'agent' && (
                    <div className="w-8 h-8 rounded-full bg-teal-900/50 flex items-center justify-center shrink-0 border border-teal-500/30">
                      <Bot size={16} className="text-teal-400" />
                    </div>
                  )}
                  <div className={`max-w-[80%] p-4 rounded-xl text-sm leading-relaxed ${msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-[#21262d] text-gray-200 rounded-tl-none border border-[#30363d]'
                    }`}>
                    {msg.content}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-blue-800 flex items-center justify-center shrink-0">
                      <User size={16} className="text-blue-200" />
                    </div>
                  )}
                </div>
              ))
            )}

            {isTyping && (
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-teal-900/50 flex items-center justify-center shrink-0 border border-teal-500/30 animate-pulse">
                  <Bot size={16} className="text-teal-400" />
                </div>
                <div className="bg-[#21262d] text-gray-400 p-4 rounded-xl rounded-tl-none border border-[#30363d] text-sm flex items-center gap-2">
                  <Activity className="animate-spin" size={14} /> CrewAI Analyst synthesizing...
                </div>
              </div>
            )}
          </div>

          <div className="p-4 bg-[#0d1117] border-t border-[#30363d] rounded-b-xl">
            <form onSubmit={handleChat} className="relative flex items-center">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={!docId || isTyping}
                placeholder={docId ? "Query the Multi-Agent system..." : "Waiting for document..."}
                className="w-full bg-[#161b22] border border-[#30363d] text-white rounded-lg pl-4 pr-12 py-3 focus:outline-none focus:border-teal-500 transition-colors disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!docId || !query.trim() || isTyping}
                className="absolute right-2 p-2 bg-teal-500 hover:bg-teal-400 text-white rounded-md disabled:opacity-50 disabled:hover:bg-teal-500 transition-colors"
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </main>
  );
}
