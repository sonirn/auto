import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Video Generation Status Component
const VideoStatus = ({ status, progress, timeRemaining }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'uploading': return 'bg-blue-500';
      case 'analyzing': return 'bg-yellow-500';
      case 'planning': return 'bg-purple-500';
      case 'generating': return 'bg-orange-500';
      case 'processing': return 'bg-indigo-500';
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'uploading': return 'Uploading files...';
      case 'analyzing': return 'Analyzing video content...';
      case 'planning': return 'Creating generation plan...';
      case 'generating': return 'Generating video with AI...';
      case 'processing': return 'Processing and combining clips...';
      case 'completed': return 'Video generation completed!';
      case 'failed': return 'Generation failed';
      default: return 'Ready';
    }
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-gray-900 rounded-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-white">{getStatusText()}</h3>
        {timeRemaining > 0 && (
          <span className="text-sm text-gray-300">
            {formatTime(timeRemaining)} remaining
          </span>
        )}
      </div>
      
      <div className="w-full bg-gray-700 rounded-full h-3 mb-4">
        <div 
          className={`h-3 rounded-full transition-all duration-300 ${getStatusColor()}`}
          style={{ width: `${progress * 100}%` }}
        ></div>
      </div>
      
      <div className="text-sm text-gray-400">
        {Math.round(progress * 100)}% complete
      </div>
    </div>
  );
};

// File Upload Component
const FileUpload = ({ onFileSelect, accept, label, icon }) => {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <div className="mb-6">
      <label className="block text-sm font-medium text-gray-300 mb-2">
        {label}
      </label>
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          dragActive 
            ? 'border-blue-500 bg-blue-500/10' 
            : 'border-gray-600 hover:border-gray-500'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="text-4xl mb-2">{icon}</div>
        <p className="text-gray-300 mb-1">
          Drag & drop your file here, or click to select
        </p>
        <p className="text-sm text-gray-500">
          {accept.includes('video') && 'Max 60 seconds'}
          {accept.includes('image') && 'JPEG, PNG supported'}
          {accept.includes('audio') && 'MP3, WAV supported'}
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileInput}
          className="hidden"
        />
      </div>
    </div>
  );
};

// Chat Component
const ChatInterface = ({ projectId, onPlanUpdate }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = { text: inputMessage, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/projects/${projectId}/chat`, {
        project_id: projectId,
        message: inputMessage,
        user_id: 'user123'
      });

      const aiMessage = { text: response.data.response, sender: 'ai' };
      setMessages(prev => [...prev, aiMessage]);

      if (response.data.updated_plan) {
        onPlanUpdate(response.data.updated_plan);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = { text: 'Sorry, there was an error processing your message.', sender: 'ai' };
      setMessages(prev => [...prev, errorMessage]);
    }

    setInputMessage('');
    setIsLoading(false);
  };

  return (
    <div className="bg-gray-900 rounded-lg p-6 mb-6">
      <h3 className="text-xl font-semibold text-white mb-4">💬 Chat with AI</h3>
      
      <div className="h-64 bg-gray-800 rounded-lg p-4 mb-4 overflow-y-auto">
        {messages.length === 0 ? (
          <p className="text-gray-500 text-center">
            Ask me to modify the generation plan or ask questions about your video.
          </p>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`mb-3 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
              <div className={`inline-block p-3 rounded-lg max-w-xs ${
                msg.sender === 'user' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-200'
              }`}>
                {msg.text}
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="text-left">
            <div className="inline-block p-3 rounded-lg bg-gray-700 text-gray-200">
              AI is typing...
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={sendMessage}
          disabled={isLoading || !inputMessage.trim()}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [currentStep, setCurrentStep] = useState('upload');
  const [projectId, setProjectId] = useState(null);
  const [userId] = useState('user123'); // Simple user ID for now
  const [files, setFiles] = useState({
    sample: null,
    character: null,
    audio: null
  });
  const [analysis, setAnalysis] = useState(null);
  const [plan, setPlan] = useState(null);
  const [videoStatus, setVideoStatus] = useState({
    status: 'ready',
    progress: 0,
    timeRemaining: 0
  });
  const [selectedModel, setSelectedModel] = useState('runwayml_gen4');

  // Create project on component mount
  useEffect(() => {
    const createProject = async () => {
      try {
        const response = await axios.post(`${API}/projects`, {
          user_id: userId
        });
        setProjectId(response.data.id);
      } catch (error) {
        console.error('Failed to create project:', error);
      }
    };
    createProject();
  }, [userId]);

  // Poll for status updates
  useEffect(() => {
    if (!projectId) return;

    const pollStatus = async () => {
      try {
        const response = await axios.get(`${API}/projects/${projectId}/status`);
        setVideoStatus(response.data);
      } catch (error) {
        console.error('Failed to get status:', error);
      }
    };

    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, [projectId]);

  const handleFileSelect = (file, type) => {
    setFiles(prev => ({ ...prev, [type]: file }));
  };

  const uploadFile = async (file, endpoint) => {
    const formData = new FormData();
    formData.append('file', file);
    
    await axios.post(`${API}/projects/${projectId}/${endpoint}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  };

  const handleAnalyze = async () => {
    try {
      setCurrentStep('analyzing');
      
      // Upload sample video (required)
      if (files.sample) {
        await uploadFile(files.sample, 'upload-sample');
      }

      // Upload character image (optional)
      if (files.character) {
        await uploadFile(files.character, 'upload-character');
      }

      // Upload audio (optional)
      if (files.audio) {
        await uploadFile(files.audio, 'upload-audio');
      }

      // Start analysis
      const response = await axios.post(`${API}/projects/${projectId}/analyze`);
      setAnalysis(response.data.analysis);
      setPlan(response.data.plan);
      setCurrentStep('planning');
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Analysis failed. Please try again.');
      setCurrentStep('upload');
    }
  };

  const handleGenerate = async () => {
    try {
      setCurrentStep('generating');
      await axios.post(`${API}/projects/${projectId}/generate?model=${selectedModel}`);
    } catch (error) {
      console.error('Generation failed:', error);
      alert('Generation failed. Please try again.');
    }
  };

  const handleDownload = async () => {
    try {
      const response = await axios.get(`${API}/projects/${projectId}/download`);
      
      // Create download link
      const link = document.createElement('a');
      link.href = `data:video/mp4;base64,${response.data.video_base64}`;
      link.download = response.data.filename;
      link.click();
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🎬 AI Video Generator
          </h1>
          <p className="text-gray-300">
            Upload a sample video and let AI create a similar one for you
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center space-x-4">
            {[
              { step: 'upload', label: 'Upload', icon: '📤' },
              { step: 'analyzing', label: 'Analyze', icon: '🔍' },
              { step: 'planning', label: 'Plan', icon: '📝' },
              { step: 'generating', label: 'Generate', icon: '🎬' },
              { step: 'completed', label: 'Done', icon: '✅' }
            ].map((item, index) => (
              <div key={item.step} className="flex items-center">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl ${
                  currentStep === item.step || videoStatus.status === item.step
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-400'
                }`}>
                  {item.icon}
                </div>
                <span className="ml-2 text-sm text-gray-300">{item.label}</span>
                {index < 4 && <div className="w-8 h-0.5 bg-gray-600 mx-4" />}
              </div>
            ))}
          </div>
        </div>

        {/* Status Display */}
        {videoStatus.status !== 'ready' && (
          <VideoStatus 
            status={videoStatus.status}
            progress={videoStatus.progress}
            timeRemaining={videoStatus.timeRemaining}
          />
        )}

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          {/* Upload Step */}
          {currentStep === 'upload' && (
            <div className="bg-gray-800 rounded-lg p-8">
              <h2 className="text-2xl font-bold text-white mb-6">Upload Your Files</h2>
              
              <FileUpload
                onFileSelect={(file) => handleFileSelect(file, 'sample')}
                accept="video/*"
                label="Sample Video (Required) - Max 60 seconds"
                icon="🎥"
              />
              
              <FileUpload
                onFileSelect={(file) => handleFileSelect(file, 'character')}
                accept="image/*"
                label="Character Image (Optional)"
                icon="👤"
              />
              
              <FileUpload
                onFileSelect={(file) => handleFileSelect(file, 'audio')}
                accept="audio/*"
                label="Audio Track (Optional)"
                icon="🎵"
              />

              <div className="mt-8">
                <h3 className="text-lg font-semibold text-white mb-4">Selected Files:</h3>
                <div className="space-y-2">
                  {Object.entries(files).map(([type, file]) => (
                    <div key={type} className="flex items-center justify-between bg-gray-700 p-3 rounded-lg">
                      <span className="text-gray-300 capitalize">{type}:</span>
                      <span className="text-white">{file ? file.name : 'None selected'}</span>
                    </div>
                  ))}
                </div>
              </div>

              <button
                onClick={handleAnalyze}
                disabled={!files.sample}
                className="w-full mt-6 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold"
              >
                {files.sample ? 'Analyze Video & Generate Plan' : 'Please upload a sample video'}
              </button>
            </div>
          )}

          {/* Planning Step */}
          {currentStep === 'planning' && plan && (
            <div className="space-y-6">
              {/* Analysis Results */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h2 className="text-2xl font-bold text-white mb-4">📊 Video Analysis</h2>
                <div className="bg-gray-900 rounded-lg p-4">
                  <pre className="text-gray-300 text-sm overflow-x-auto">
                    {JSON.stringify(analysis, null, 2)}
                  </pre>
                </div>
              </div>

              {/* Generation Plan */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h2 className="text-2xl font-bold text-white mb-4">🎯 Generation Plan</h2>
                <div className="bg-gray-900 rounded-lg p-4">
                  <pre className="text-gray-300 text-sm overflow-x-auto">
                    {JSON.stringify(plan, null, 2)}
                  </pre>
                </div>
              </div>

              {/* Chat Interface */}
              <ChatInterface 
                projectId={projectId}
                onPlanUpdate={setPlan}
              />

              {/* Model Selection */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-white mb-4">🤖 Select AI Model</h3>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { value: 'runwayml_gen4', label: 'RunwayML Gen 4 Turbo', desc: 'Latest, fastest generation' },
                    { value: 'runwayml_gen3', label: 'RunwayML Gen 3 Alpha', desc: 'Stable, reliable' },
                    { value: 'google_veo2', label: 'Google Veo 2', desc: 'Coming soon' },
                    { value: 'google_veo3', label: 'Google Veo 3', desc: 'Coming soon' }
                  ].map((model) => (
                    <div
                      key={model.value}
                      onClick={() => setSelectedModel(model.value)}
                      className={`p-4 rounded-lg cursor-pointer transition-colors ${
                        selectedModel === model.value
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      } ${model.value.includes('google') ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <h4 className="font-semibold">{model.label}</h4>
                      <p className="text-sm opacity-80">{model.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={() => setCurrentStep('upload')}
                  className="flex-1 bg-gray-600 text-white py-3 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Back to Upload
                </button>
                <button
                  onClick={handleGenerate}
                  disabled={selectedModel.includes('google')}
                  className="flex-1 bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold"
                >
                  🎬 Generate Video
                </button>
              </div>
            </div>
          )}

          {/* Generation/Completion Step */}
          {(currentStep === 'generating' || videoStatus.status === 'completed') && (
            <div className="bg-gray-800 rounded-lg p-8 text-center">
              {videoStatus.status === 'completed' ? (
                <div>
                  <h2 className="text-2xl font-bold text-white mb-4">🎉 Video Generated Successfully!</h2>
                  <p className="text-gray-300 mb-6">
                    Your AI-generated video is ready for download.
                  </p>
                  <div className="flex gap-4 justify-center">
                    <button
                      onClick={handleDownload}
                      className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 transition-colors font-semibold"
                    >
                      📥 Download Video
                    </button>
                    <button
                      onClick={() => {
                        setCurrentStep('upload');
                        setFiles({ sample: null, character: null, audio: null });
                        setAnalysis(null);
                        setPlan(null);
                      }}
                      className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      🔄 Create Another Video
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <h2 className="text-2xl font-bold text-white mb-4">
                    {videoStatus.status === 'generating' ? '🎬 Generating Your Video...' : '⚡ Processing...'}
                  </h2>
                  <p className="text-gray-300 mb-6">
                    The AI is working hard to create your video. This process will continue even if you close this page.
                  </p>
                  <div className="animate-pulse">
                    <div className="text-6xl mb-4">🤖</div>
                    <p className="text-gray-400">
                      AI is creating magic... Please wait.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-gray-500">
          <p>© 2025 AI Video Generator - Create amazing videos with AI</p>
        </div>
      </div>
    </div>
  );
};

export default App;