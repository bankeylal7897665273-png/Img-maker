import os
import random
import urllib.parse
import requests
import time
import json
from flask import Flask, render_template_string, request, jsonify, session

# Use a complex secret key for sessions
app = Flask(__name__)
app.secret_key = os.urandom(24) 

# --- CONFIGURATION (IMPORTANT: For real use, configure actual endpoints) ---
# Since this is a single file without a DB, we use in-memory simulation for users and chat history.
# In production, connect this logic to Firebase or a database.
users_db = {} # Simulated user database: {email: {name, password, chats: []}}
session_data = {} # Simulated session chat history for current turn

# Hugging Face Model Endpoints (Free tier is rate limited, for real use add paid API keys)
CHAT_MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
CODE_FIX_MODEL_URL = "https://api-inference.huggingface.co/models/bigcode/starcoder" # Code-specialized
IMAGE_MODEL_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
VIDEO_MODEL_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5" # Stable fallback for text-to-video

# Add your free HF Token here if rate limits are an issue (Rate limits are still strict)
HF_TOKEN = "" # Jese: "Bearer hf_xxx"

HEADERS = {"Authorization": HF_TOKEN} if HF_TOKEN else {}

# --- HTML/CSS/JS (Complex, professional, mobile-first design) ---
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Nexis AI - Your Advanced Python Studio</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
    
    <style>
        :root {
            --bg-color: #0b0c10;
            --surface-color: #1f2833;
            --text-main: #c5c6c7;
            --text-muted: #888;
            --border-color: #45a29e;
            --sparkle-color: #66fcf1;
            --sidebar-bg: #12141a;
            --code-bg: #0e1117;
            --user-bubble-bg: rgba(102, 252, 241, 0.1);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Google Sans', Arial, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: var(--bg-color); color: var(--text-main); height: 100vh; overflow: hidden; display: flex; flex-direction: column; }

        .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24; }
        .filled-icon { font-variation-settings: 'FILL' 1, 'wght' 400; }

        /* --- AUTH SCREEN STYLES (Is Back!) --- */
        #auth-screen {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: var(--surface-color); z-index: 10000; display: flex;
            align-items: center; justify-content: center; padding: 20px; transition: 0.3s ease;
        }
        #auth-screen.hidden { opacity: 0; pointer-events: none; transform: translateY(-50px);}
        .auth-box {
            background: #fff; width: 100%; max-width: 400px; padding: 35px 25px;
            border-radius: 24px; box-shadow: 0 15px 50px rgba(102, 252, 241, 0.2);
            text-align: center; display: none; flex-direction: column; gap: 18px;
            animation: fadeIn 0.4s ease; border: 2px solid var(--border-color);
        }
        .auth-box.active { display: flex; }
        .auth-title { font-size: 26px; font-weight: 700; color: #000; margin-bottom: 5px; display: flex; align-items: center; justify-content: center; gap: 8px; text-transform: uppercase; letter-spacing: 1px;}
        .auth-input {
            width: 100%; padding: 15px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.1);
            font-size: 16px; outline: none; background: #fff; transition: 0.2s; color: #000;
        }
        .auth-input::placeholder { color: #888; }
        .auth-input:focus { border-color: var(--sparkle-color); box-shadow: 0 0 0 2px rgba(102, 252, 241, 0.3); }
        .auth-btn {
            width: 100%; padding: 15px; border: none; border-radius: 12px;
            background: linear-gradient(45deg, var(--sparkle-color), var(--border-color)); color: #000; font-size: 17px; font-weight: 700;
            cursor: pointer; transition: 0.3s; margin-top: 10px; text-transform: uppercase;
        }
        .auth-btn:hover { box-shadow: 0 0 15px rgba(102, 252, 241, 0.5); transform: scale(1.02); }
        .auth-switch { font-size: 15px; color: #666; cursor: pointer; margin-top: 15px; }
        .auth-switch span { color: #000; font-weight: 700; }
        #auth-error { color: #d93025; font-size: 14px; min-height: 20px; font-weight: bold; margin-bottom: -10px; }

        /* --- SIDEBAR ( Hamburger + New Chat + Memory list ) --- */
        .sidebar { position: fixed; top: 0; left: 0; width: 280px; height: 100%; background: var(--sidebar-bg); z-index: 1001; transform: translateX(-100%); transition: transform 0.3s ease; box-shadow: 5px 0 25px rgba(102,252,241,0.1); display: flex; flex-direction: column; border-right: 1px solid rgba(102,252,241,0.2); }
        .sidebar.active { transform: translateX(0); }
        .sidebar-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 1000; display: none; }
        .sidebar-overlay.active { display: block; }
        .sidebar-top { padding: 18px; border-bottom: 1px solid rgba(102,252,241,0.1); display: flex; justify-content: space-between; align-items: center;}
        .new-chat-btn-side { display: flex; align-items: center; gap: 10px; padding: 12px 15px; border-radius: 20px; cursor: pointer; transition: 0.2s; margin: 15px; border: 1px solid var(--sparkle-color); background: rgba(102,252,241,0.05);}
        .new-chat-btn-side:hover { background: rgba(102,252,241,0.15); box-shadow: 0 0 10px rgba(102,252,241,0.2); }
        .history-list { flex: 1; overflow-y: auto; padding: 10px 0; }
        .history-title-label { font-size: 13px; color: var(--text-muted); margin-left: 15px; margin-bottom: 12px; font-weight: 500; }
        .history-item { padding: 12px 15px; cursor: pointer; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-main); position: relative; border-radius: 0 20px 20px 0; margin-right: 10px;}
        .history-item:hover { background: rgba(102, 252, 241, 0.08); color: var(--sparkle-color); }
        .logout-btn { margin: 15px; padding: 12px 15px; border-radius: 20px; cursor: pointer; background: rgba(217, 48, 37, 0.1); color: #d93025; font-weight: 700; display: flex; align-items: center; gap: 10px; border: 1px solid #d93025; }
        .logout-btn:hover { background: rgba(217, 48, 37, 0.2); }

        /* HEADER */
        .header { display: flex; justify-content: space-between; align-items: center; padding: 15px 18px; background: var(--bg-color); z-index: 10; border-bottom: 1px solid rgba(102, 252, 241, 0.2); box-shadow: 0 0 15px rgba(102, 252, 241, 0.1); }
        .header-left { display: flex; align-items: center; gap: 15px; }
        .header-icon { color: var(--sparkle-color); cursor: pointer; padding: 8px; border-radius: 50%; }
        .header-icon:hover { background: rgba(102, 252, 241, 0.1); }
        .model-name { font-size: 20px; font-weight: 700; color: var(--sparkle-color); display: flex; align-items: center; gap: 6px; letter-spacing: 1px; text-transform: uppercase;}

        /* MAIN CHAT AREA (Ful scrolling and keyboard fix) */
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; align-items: center; position: relative; scroll-behavior: smooth; }
        .messages-wrapper { width: 100%; max-width: 768px; display: flex; flex-direction: column; gap: 24px; padding-bottom: 140px; } /* Ful scrollable till bottom */
        .welcome-screen { position: absolute; top: 30%; left: 50%; transform: translate(-50%, -50%); text-align: center; width: 100%; }
        .welcome-sparkle { font-size: 55px; background: -webkit-linear-gradient(45deg, #66fcf1, #45a29e, #bc13fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0 0 10px rgba(102,252,241,0.5));}

        /* BUBBLES */
        .msg-row { display: flex; width: 100%; animation: fadeIn 0.3s ease; }
        .msg-row.user { justify-content: flex-end; }
        .msg-row.ai { justify-content: flex-start; gap: 12px; }
        .user-bubble { background: var(--user-bubble-bg); border: 1px solid var(--border-color); padding: 12px 18px; border-radius: 24px 24px 4px 24px; font-size: 15px; max-width: 85%; line-height: 1.5; color: #fff; }
        .ai-icon-container { width: 28px; height: 28px; display: flex; align-items: flex-start; margin-top: 4px; flex-shrink: 0; }
        .ai-icon-container .material-symbols-outlined { font-size: 28px; background: -webkit-linear-gradient(45deg, #66fcf1, #bc13fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .ai-bubble { font-size: 15px; line-height: 1.6; width: 100%; max-width: 85%; color: #fff; padding-top: 4px; overflow-wrap: break-word; }

        /* CODE & CHAT UI */
        .code-block { background: var(--code-bg); border-radius: 12px; margin: 10px 0; overflow: hidden; font-family: monospace; color: #d4d4d4; border: 1px solid rgba(255,255,255,0.05); }
        .code-header { background: rgba(255,255,255,0.05); padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #a0a0a0; border-bottom: 1px solid rgba(255,255,255,0.05);}
        .copy-btn { background: none; border: none; color: #a0a0a0; cursor: pointer; font-size: 12px; display: flex; align-items: center; gap: 4px; transition: 0.2s; }
        .chat-image, .chat-video { max-width: 100%; border-radius: 12px; margin: 10px 0; border: 1px solid var(--sparkle-color); box-shadow: 0 0 15px rgba(102,252,241,0.2); }
        
        /* FLOATING INPUT BAR ( Fixed to bottom ) */
        .input-wrapper { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); width: 90%; max-width: 768px; background: var(--surface-color); border: 1px solid rgba(102, 252, 241, 0.3); border-radius: 24px; display: flex; flex-direction: column; padding: 4px 8px; z-index: 20; box-shadow: 0 5px 25px rgba(0,0,0,0.5); transition: 0.3s;}
        
        /* Previews area */
        .preview-container { display: flex; gap: 10px; padding: 8px 12px 0 12px; overflow-x: auto; max-height: 60px;}
        .preview-item { background: rgba(0,0,0,0.3); border: 1px solid rgba(102,252,241,0.2); padding: 4px 10px; border-radius: 12px; font-size: 12px; display: flex; align-items: center; gap: 6px; color: var(--text-muted); }
        .preview-item .remove { cursor: pointer; color: red; font-size: 16px; font-weight: bold; }

        .input-top { display: flex; align-items: center; }
        #user-input { flex: 1; background: transparent; border: none; outline: none; padding: 16px 12px; font-size: 16px; color: #fff; }
        #user-input::placeholder { color: #666; }
        
        .input-bottom { display: flex; justify-content: space-between; align-items: center; padding: 0 8px 8px 8px; }
        .action-icons { display: flex; gap: 8px; position: relative; align-items: center;}
        .icon-btn { background: transparent; border: none; color: var(--sparkle-color); cursor: pointer; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: 0.3s;}
        .icon-btn:hover { background: rgba(102, 252, 241, 0.1); box-shadow: 0 0 10px rgba(102,252,241,0.2); }
        
        .send-btn { color: var(--text-muted); display: flex; }
        .send-btn.active { color: var(--sparkle-color); filter: drop-shadow(0 0 5px var(--sparkle-color)); }
        
        /* Mode Menu & Upload Menu */
        .mode-badge { font-size: 10px; background: rgba(102,252,241,0.2); color: var(--sparkle-color); padding: 2px 7px; border-radius: 8px; position: absolute; top: -8px; left: 5px; font-weight: bold; border: 1px solid var(--border-color); pointer-events: none;}
        
        .attach-menu, .mode-menu { position: absolute; bottom: 50px; left: 0; background: var(--bg-color); border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); display: none; flex-direction: column; overflow: hidden; border: 1px solid var(--border-color); min-width: 170px; z-index: 30; }
        .attach-menu.active, .mode-menu.active { display: flex; }
        .menu-item { padding: 12px 16px; display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 14px; color: #fff; transition: 0.2s; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .menu-item:hover { background: rgba(102, 252, 241, 0.1); color: var(--sparkle-color); }

        .loader { color: var(--sparkle-color); font-size: 14px; animation: pulse 1s infinite; }
        @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; text-shadow: 0 0 10px var(--sparkle-color); } 100% { opacity: 0.5; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>

    <div id="auth-screen">
        <div class="auth-box active" id="login-box">
            <div class="auth-title"><span class="material-symbols-outlined filled-icon">auto_awesome</span> Welcome Back</div>
            <p style="color: #666; font-size: 14px; margin-bottom: 10px;">Login to use Nexis AI Studio</p>
            <input type="email" id="log-email" class="auth-input" placeholder="Email Address">
            <input type="password" id="log-pass" class="auth-input" placeholder="Password">
            <div id="log-error" class="auth-error"></div>
            <button class="auth-btn" onclick="loginUser()">Login</button>
            <div class="auth-switch" onclick="toggleAuth('signup')">Don't have an account? <span>Create One</span></div>
        </div>

        <div class="auth-box" id="signup-box">
            <div class="auth-title"><span class="material-symbols-outlined filled-icon">auto_awesome</span> Create Account</div>
            <p style="color: #666; font-size: 14px; margin-bottom: 10px;">Join Nexis AI Studio</p>
            <input type="text" id="reg-name" class="auth-input" placeholder="Full Name">
            <input type="email" id="reg-email" class="auth-input" placeholder="Email Address">
            <input type="password" id="reg-pass" class="auth-input" placeholder="Password (min 6 chars)">
            <div id="reg-error" class="auth-error"></div>
            <button class="auth-btn" onclick="registerUser()">Sign Up</button>
            <div class="auth-switch" onclick="toggleAuth('login')">Already have an account? <span>Login Here</span></div>
        </div>
    </div>

    <div id="app-container" style="display: none; flex-direction: column; height: 100%; width: 100%;">
        <div class="sidebar-overlay" id="sidebar-overlay" onclick="toggleSidebar()"></div>

        <div class="sidebar" id="sidebar">
            <div class="sidebar-top">
                <span style="font-size: 18px; font-weight: 700; color: var(--sparkle-color);">NEXIS SIDEBAR</span>
                <span class="material-symbols-outlined icon-btn" style="color: var(--sparkle-color);" onclick="toggleSidebar()">close</span>
            </div>
            <div class="new-chat-btn-side" onclick="startNewChat()">
                <span class="material-symbols-outlined">edit_square</span>
                <span> नई चैट (NEW CHAT) </span>
            </div>
            <div class="history-list">
                <div class="history-title-label">चैट इतिहास</div>
                <div id="history-container"></div>
            </div>
            <div class="logout-btn" onclick="logoutUser()">
                <span class="material-symbols-outlined">logout</span> Log Out
            </div>
        </div>

        <header class="header">
            <div class="header-left">
                <span class="material-symbols-outlined header-icon" onclick="toggleSidebar()">menu</span>
                <div class="model-name"><span class="material-symbols-outlined filled-icon">auto_awesome</span> NEXIS AI v2.0</div>
            </div>
            <span class="material-symbols-outlined header-icon" style="color:var(--text-muted); cursor: pointer;" onclick="clearCurrentChat()">delete</span>
        </header>

        <div class="chat-container" id="chat-container">
            <div class="welcome-screen" id="welcome-screen">
                <span class="material-symbols-outlined filled-icon welcome-sparkle">smart_toy</span>
                <div style="font-size: 22px; color: #fff; margin-top: 15px; font-weight: bold; text-shadow: 0 0 10px rgba(102,252,241,0.3);">नमस्ते <span id="welcome-name-display">Bhai</span>!</div>
                <div style="font-size: 14px; color: var(--text-muted); margin-top: 5px;">Aise hi 'Hello' nahin professional answers. Start typing!</div>
            </div>
            <div class="messages-wrapper" id="chat-box"></div>
        </div>

        <div class="input-wrapper">
            <div class="preview-container" id="preview-container"></div>
            <div class="input-top">
                <input type="text" id="user-input" placeholder="Gemini se nahin, professional AI se poochhein..." autocomplete="off">
            </div>
            <div class="input-bottom">
                <div class="action-icons">
                    <button class="icon-btn" onclick="toggleModeMenu()">
                        <span class="material-symbols-outlined">menu</span>
                        <span class="mode-badge" id="current-mode">AUTO</span>
                    </button>
                    <div class="mode-menu" id="mode-menu">
                        <div class="menu-item" onclick="setMode('auto')"><span class="material-symbols-outlined">smart_toy</span> Auto Detect</div>
                        <div class="menu-item" onclick="setMode('image')"><span class="material-symbols-outlined">image</span> Image Only</div>
                        <div class="menu-item" onclick="setMode('video')"><span class="material-symbols-outlined">movie</span> Video Only</div>
                    </div>

                    <button class="icon-btn" onclick="toggleAttachMenu()"><span class="material-symbols-outlined">add</span></button>
                    <div class="attach-menu" id="attach-menu">
                        <div class="menu-item" onclick="triggerFile('image/*')"><span class="material-symbols-outlined">image</span> Upload Image</div>
                        <div class="menu-item" onclick="triggerFile('video/*')"><span class="material-symbols-outlined">movie</span> Upload Video</div>
                        <div class="menu-item" onclick="triggerFile('.pdf,.doc,.docx,.txt,.py,.html')"><span class="material-symbols-outlined">description</span> Upload Document</div>
                    </div>
                    <input type="file" id="hidden-file-input" style="display: none;" onchange="handleFileSelect(event)">
                    <button class="icon-btn"><span class="material-symbols-outlined">mic</span></button>
                </div>
                
                <button class="icon-btn send-btn" id="send-btn" onclick="sendMessage()">
                    <span class="material-symbols-outlined filled-icon">send</span>
                </button>
            </div>
        </div>
    </div>

    <script>
        // --- CORE SESSION/DATA SIMULATION (Single file restriction) ---
        // Since no external DB, these values are only for the current page life.
        let users_db = JSON.parse(localStorage.getItem('nexis_users_db')) || {}; // Simulated simple signup
        let current_user_id = localStorage.getItem('nexis_current_user') || null;
        let currentChatMode = 'auto'; // default
        let selectedFile = null;
        let chatSessions = JSON.parse(localStorage.getItem('nexis_chat_history')) || []; // User session chat list

        // --- AUTH LOGIC (IS BACK!) ---
        function toggleAuth(type) {
            document.getElementById('log-error').innerText = '';
            document.getElementById('reg-error').innerText = '';
            if (type === 'signup') {
                document.getElementById('login-box').classList.remove('active');
                document.getElementById('signup-box').classList.add('active');
            } else {
                document.getElementById('signup-box').classList.remove('active');
                document.getElementById('login-box').classList.add('active');
            }
        }

        function registerUser() {
            const name = document.getElementById('reg-name').value.trim();
            const email = document.getElementById('reg-email').value.trim();
            const pass = document.getElementById('reg-pass').value.trim();
            const errorDiv = document.getElementById('reg-error');

            if (!name || !email || !pass) { errorDiv.innerText = "All fields are required!"; return; }
            if (pass.length < 6) { errorDiv.innerText = "Password must be at least 6 characters!"; return; }
            
            errorDiv.innerText = "Creating account...";
            
            if (users_db[email]) { errorDiv.innerText = "Email already registered. Please Login."; return;}

            // Simulate create account in memory/localStorage
            const uid = Date.now().toString();
            users_db[email] = { uid, name, email, pass };
            localStorage.setItem('nexis_users_db', JSON.stringify(users_db));
            
            setTimeout(() => {
                errorDiv.innerText = "";
                loginUser(email, pass); // auto login after signup
            }, 1000);
        }

        function loginUser(provided_email = '', provided_pass = '') {
            const email = provided_email || document.getElementById('log-email').value.trim();
            const pass = provided_pass || document.getElementById('log-pass').value.trim();
            const errorDiv = document.getElementById('log-error');

            if (!email || !pass) { errorDiv.innerText = "All fields are required!"; return; }
            errorDiv.innerText = "Logging in...";

            const user = users_db[email];
            
            setTimeout(() => {
                if (user && user.pass === pass) {
                    current_user_id = user.uid;
                    localStorage.setItem('nexis_current_user', current_user_id);
                    errorDiv.innerText = "";
                    renderApp();
                } else {
                    errorDiv.innerText = "Invalid Email or Password!";
                }
            }, 1000);
        }

        function logoutUser() {
            localStorage.removeItem('nexis_current_user');
            localStorage.removeItem('nexis_chat_history'); // Clear chat on logout since not persistent
            location.reload(); 
        }

        function renderApp() {
            document.getElementById('auth-screen').classList.add('hidden');
            document.getElementById('app-container').style.display = 'flex';
            
            const user = Object.values(users_db).find(u => u.uid === current_user_id);
            if(user) document.getElementById('welcome-name-display').innerText = user.name;
            startNewChat(); // start a fresh chat on app render
        }

        // Auto render app if logged in
        if (current_user_id) { renderApp(); }


        // --- CHAT & UI LOGIC ---

        function toggleSidebar() { document.getElementById('sidebar').classList.toggle('active'); document.getElementById('sidebar-overlay').classList.toggle('active'); }

        document.getElementById('user-input').addEventListener('input', function() {
            const sendBtn = document.getElementById('send-btn');
            if(this.value.trim().length > 0 || selectedFile) sendBtn.classList.add('active'); else sendBtn.classList.remove('active');
        });
        document.getElementById('user-input').addEventListener('keypress', function (e) { if (e.key === 'Enter') sendMessage(); });

        // Input height fix for mobile keyboard
        let inputWrapper = document.querySelector('.input-wrapper');
        document.getElementById('user-input').addEventListener('focus', function() {
            setTimeout(()=> { window.scrollTo(0, 0); document.body.scrollTop = 0; inputWrapper.style.bottom = '10px'; }, 300);
        });
        document.getElementById('user-input').addEventListener('blur', function() {
            setTimeout(()=> { inputWrapper.style.bottom = '20px'; }, 300);
        });

        // Mode Menu
        function toggleModeMenu() { document.getElementById('mode-menu').classList.toggle('active'); }
        function setMode(mode) { currentChatMode = mode; document.getElementById('current-mode').innerText = mode.toUpperCase(); toggleModeMenu(); }

        // Attach Menu & File upload
        function toggleAttachMenu() { document.getElementById('attach-menu').classList.toggle('active'); }
        function triggerFile(acceptType) { const input = document.getElementById('hidden-file-input'); input.accept = acceptType; input.click(); toggleAttachMenu(); }
        function handleFileSelect(event) {
            const file = event.target.files[0]; if(!file) return; 
            selectedFile = { name: file.name, type: file.type, size: file.size, fileObject: file }; 
            renderPreviews();
            document.getElementById('send-btn').classList.add('active'); 
            event.target.value = ''; 
        }
        function renderPreviews() {
            const container = document.getElementById('preview-container'); container.innerHTML = '';
            if(!selectedFile) return;
            let icon = 'description'; if(selectedFile.type.startsWith('image/')) icon = 'image'; else if(selectedFile.type.startsWith('video/')) icon = 'movie';
            container.innerHTML += `<div class="preview-item"><span class="material-symbols-outlined" style="font-size:16px;">${icon}</span> ${selectedFile.name} <span class="remove" onclick="removeFile()">×</span></div>`;
        }
        function removeFile() { selectedFile = null; renderPreviews(); if(document.getElementById('user-input').value.trim().length === 0) document.getElementById('send-btn').classList.remove('active'); }

        // Chat Sessions & History list
        function renderHistoryList() {
            const container = document.getElementById('history-container'); container.innerHTML = '';
            chatSessions.slice(0, 5).forEach((chat, index) => { // show only last 5 in memory
                const div = document.createElement('div'); div.className = 'history-item'; div.innerText = chat.title;
                div.onclick = () => { loadChat(chat.id); toggleSidebar(); }; container.appendChild(div);
            });
        }
        function clearCurrentChat() { chatSessions = []; startNewChat(); }
        function startNewChat() {
            const newId = Date.now().toString();
            document.getElementById('chat-box').innerHTML = ''; document.getElementById('welcome-screen').style.display = 'block';
            document.getElementById('user-input').value = ""; selectedFile = null; renderPreviews(); document.getElementById('send-btn').classList.remove('active');
            // Store current new chat in memory list
            if(!chatSessions.length || chatSessions[0].title !== "नई चैट (NEW CHAT)") {
                chatSessions.unshift({ id: newId, title: "नई चैट (NEW CHAT)", messages: [] });
                renderHistoryList();
            }
            if(document.getElementById('sidebar').classList.contains('active')) toggleSidebar();
        }
        function loadChat(id) {
            startNewChat(); // clear current UI, but we don't have true persistence so we cannot fully load old messages
            // chatSessions is just a list of names for now in this simulated single file
            document.getElementById('welcome-screen').style.display = 'block';
        }

        // APPEND FUNCTIONS
        function appendUserHtml(text) { document.getElementById('chat-box').insertAdjacentHTML('beforeend', `<div class="msg-row user"><div class="user-bubble">${text}</div></div>`); scrollToBottom();}

        function formatCodeBlock(text) {
             // Basic format for code blocks with copy btn
             text = text.replace(/```(\w*)\n([\s\S]*?)```/g, function(match, lang, code) {
                const escapedCode = code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
                return `<div class="code-block"><div class="code-header"><span>${lang || 'Code'}</span><button class="copy-btn" onclick="copyCode(this)"><span class="material-symbols-outlined" style="font-size:14px;">content_copy</span> Copy</button></div><pre><code>${escapedCode}</code></pre></div>`;
            });
            text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); return text;
        }

        function copyCode(btn) {
            const code = btn.parentElement.nextElementSibling.innerText;
            navigator.clipboard.writeText(code).then(() => {
                const originalHtml = btn.innerHTML; btn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;">check</span> Copied';
                btn.style.color = '#66fcf1'; setTimeout(() => { btn.innerHTML = originalHtml; btn.style.color = '#a0a0a0'; }, 2000);
            });
        }

        function scrollToBottom() {
            const container = document.getElementById('chat-container');
            container.scrollTop = container.scrollHeight;
        }

        function appendAiHtml(content, type = 'text') {
            const msgId = 'msg-' + Date.now();
            document.getElementById('chat-box').insertAdjacentHTML('beforeend', `
                <div class="msg-row ai">
                    <div class="ai-icon-container"><span class="material-symbols-outlined filled-icon">auto_awesome</span></div>
                    <div class="ai-bubble" id="${msgId}"></div>
                </div>`);
            const bubble = document.getElementById(msgId);
            
            if (type === 'image') {
                bubble.innerHTML = `<img src="${content}" class="chat-image" alt="Nexis AI Generated Image">`;
            } else if (type === 'video') {
                bubble.innerHTML = `<video src="${content}" class="chat-video" controls autoplay loop playsinline></video>
                                    <div style="font-size:12px; color:var(--sparkle-color); margin-top:5px;">${type === 'video' ? 'Nexis AI NOTE: Video model rate limited hai.' : ''}</div>`;
            } else {
                // Text/Code formatting
                let formatted = formatCodeBlock(content);
                formatted = formatted.replace(/\n(?![^<]*>)/g, '<br>');
                bubble.innerHTML = formatted;
            }
            scrollToBottom();
        }

        // SEND MESSAGE FUNCTION
        async function sendMessage() {
            const inputField = document.getElementById('user-input'); let message = inputField.value.trim();
            if (!message && !selectedFile) return;

            // UI feedback
            document.getElementById('welcome-screen').style.display = 'none'; 
            let displayMessage = message;
            if (selectedFile) {
                let fileIcon = 'description'; if(selectedFile.type.startsWith('image/')) fileIcon = 'image'; else if(selectedFile.type.startsWith('video/')) fileIcon = 'movie';
                displayMessage = `<span class="material-symbols-outlined" style="font-size:16px;">${fileIcon}</span> Uploaded: ${selectedFile.name}${message ? "<br>" + message : ""}`;
            }
            appendUserHtml(displayMessage); 
            inputField.value = ''; document.getElementById('send-btn').classList.remove('active');

            // Set simulated new chat name if first message
            if(chatSessions.length > 0 && chatSessions[0].title === "नई चैट (NEW CHAT)") {
                chatSessions[0].title = message.substring(0, 20) + "...";
                renderHistoryList();
            }
            scrollToBottom(); 

            const loadingId = 'load-' + Date.now();
            document.getElementById('chat-box').insertAdjacentHTML('beforeend', `
                <div class="msg-row ai" id="${loadingId}">
                    <div class="ai-icon-container"><span class="material-symbols-outlined filled-icon">auto_awesome</span></div>
                    <div class="ai-bubble loader">Nexis AI is processing your prompt...</div>
                </div>`);
            scrollToBottom();

            // Prepare API call
            const payload = { text: message, mode: currentChatMode };
            
            // Simulating uploading file content for single file backend processing
            if (selectedFile) {
                // For python/text files we can read content on client side for simulation
                if(selectedFile.type.startsWith('text/') || selectedFile.type.endsWith('py') || selectedFile.type.endsWith('html')){
                    payload.file_name = selectedFile.name;
                    payload.file_type = 'document';
                    // Using FileReader to read content
                    const reader = new FileReader();
                    reader.onload = async (e) => {
                        payload.file_content = e.target.result; // send text content for code fixing
                        removeFile(); // remove preview after submission simulation
                        await callApiAi(payload, loadingId); // nested await to ensure content read before call
                    }
                    reader.readAsText(selectedFile.fileObject);
                    return; // prevent second call
                } else {
                     // For image/video in this single file we just send name/type for processing logic to detect image generation fallback
                     payload.file_name = selectedFile.name;
                     payload.file_type = selectedFile.type.startsWith('image/') ? 'image' : 'video';
                     removeFile(); 
                }
            }

            await callApiAi(payload, loadingId); 
        }

        // Sub-function to call Flask Backend
        async function callApiAi(payload, loadingId) {
             try {
                // Call actual Python Backend
                const response = await fetch('/api/ai', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                const data = await response.json();
                
                if (document.getElementById(loadingId)) document.getElementById(loadingId).remove();

                if (data.type === 'image') {
                    appendAiHtml(data.url, 'image');
                } else if (data.type === 'video') {
                    appendAiHtml(data.url, 'video');
                } else {
                    // Normal Text/Code response
                    appendAiHtml(data.text, 'text');
                }
            } catch (error) {
                if (document.getElementById(loadingId)) document.getElementById(loadingId).remove();
                appendAiHtml(`<span style="color: #ff4d4d;">❌ Connection Error: Server se reply nahin mila. (Single file Flask running?)</span>`, 'text');
            }
        }
    </script>
</body>
</html>
"""

# --- FLASK BACKEND LOGIC ---

@app.route('/')
def home():
    # Simulated auth state on render (always shows login first)
    return render_template_string(HTML_CODE)

@app.route('/api/ai', methods=['POST'])
def nexis_ai_core():
    # Simulated user verification and memory handling
    # In a full app with database, use actual user ID from session.
    data = request.json
    prompt = data.get('text', '').lower()
    mode = data.get('mode', 'auto')
    
    # Check for simulated uploaded file details for processing
    file_name = data.get('file_name', '')
    file_type = data.get('file_type', '')
    file_content = data.get('file_content', '') # Client-side read content simulation
    
    # 1. LOGIC FOR CODE FIXING (PROFESSIONAL REQUEST)
    if file_type == 'document' and file_name.endswith(('.py', '.html')) and file_content:
        # Prompt model specialised for code fixing
        payload = {
            "inputs": f"You are Nexis AI, an advanced professional coder. A user provided this code from file '{file_name}':\n
http://googleusercontent.com/immersive_entry_chip/0

Bas is naye complete `app.py` aur `requirements.txt` dono ko Github par push karo aur Render se connect kar do. Ab naya, powerful aur professional "Nexis AI v2.0" chalu ho jayega bina generic answers aur login screen ke saath!
