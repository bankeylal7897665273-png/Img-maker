import os
import random
import urllib.parse
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# IMPORTANT: Asli video banane ke liye yahan apna Hugging Face token daalo!
# Yeh 100% free hai. Yahan se lo: https://huggingface.co/settings/tokens
HF_API_TOKEN = "" # Jese: "hf_xYzABCdefGHI..."

HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Magic Studio</title>
    <style>
        :root {
            --neon-blue: #00e5ff;
            --neon-purple: #b000ff;
            --bg-color: #0d0e15;
        }
        body {
            background-color: var(--bg-color);
            color: #fff;
            font-family: 'Segoe UI', Tahoma, sans-serif;
            padding: 20px;
            display: flex;
            justify-content: center;
        }
        .container {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 229, 255, 0.2);
            border-radius: 16px;
            padding: 25px;
            width: 100%;
            max-width: 450px;
            box-shadow: 0 0 25px rgba(176, 0, 255, 0.15);
        }
        h2 {
            text-align: center;
            text-shadow: 0 0 10px var(--neon-blue);
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }
        .instruction {
            font-size: 12px;
            color: #888;
            text-align: center;
            margin-bottom: 15px;
        }
        textarea {
            width: 100%;
            height: 100px;
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid var(--neon-blue);
            color: #fff;
            border-radius: 10px;
            padding: 15px;
            box-sizing: border-box;
            margin-bottom: 20px;
            resize: none;
            outline: none;
        }
        textarea:focus {
            box-shadow: 0 0 15px rgba(0, 229, 255, 0.3);
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(45deg, var(--neon-blue), var(--neon-purple));
            border: none;
            color: white;
            font-weight: 800;
            font-size: 16px;
            border-radius: 10px;
            cursor: pointer;
            text-transform: uppercase;
            transition: 0.3s;
        }
        button:active {
            transform: scale(0.95);
        }
        #output {
            margin-top: 25px;
            min-height: 250px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px dashed rgba(255,255,255,0.2);
            border-radius: 10px;
            background: rgba(0,0,0,0.4);
            padding: 10px;
            overflow: hidden;
        }
        img, video {
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 0 15px rgba(255,255,255,0.1);
        }
        .loading-text {
            color: var(--neon-purple);
            font-weight: bold;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 1; text-shadow: 0 0 10px var(--neon-purple); }
            100% { opacity: 0.6; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>AI Magic Studio</h2>
        <p class="instruction">Write 'Make a video...' or 'Generate an image...'. AI will auto-detect your need.</p>
        
        <textarea id="prompt" placeholder="Example: Make a cyberpunk video of a futuristic city..."></textarea>
        
        <button onclick="processAI()">Generate AI Magic</button>
        
        <div id="output">
            <span style="color: #666; font-size: 14px;">Media will appear here</span>
        </div>
    </div>

    <script>
        async function processAI() {
            const prompt = document.getElementById('prompt').value.trim();
            const outputDiv = document.getElementById('output');
            
            if(!prompt) {
                alert('Bhai, box khali hai. Pehle kuch type karo!');
                return;
            }

            // Clean processing animation without any "just a moment"
            outputDiv.innerHTML = '<span class="loading-text">AI is processing your prompt...</span>';

            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: prompt})
                });
                
                const data = await response.json();
                
                if(data.status === 'success') {
                    if(data.format === 'image') {
                        outputDiv.innerHTML = `<img src="${data.url}" alt="AI Result">`;
                    } else if (data.format === 'video') {
                        // Adding random param to video URL to avoid browser caching
                        outputDiv.innerHTML = `<video controls autoplay loop><source src="${data.url}?v=${Math.random()}" type="video/mp4"></video>`;
                    }
                } else {
                    outputDiv.innerHTML = `<span style="color: #ff4444; font-size: 14px; text-align: center;">${data.message}</span>`;
                }
            } catch(error) {
                outputDiv.innerHTML = `<span style="color: #ff4444;">Server error! Check connection.</span>`;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_CODE)

@app.route('/api/process', methods=['POST'])
def process():
    data = request.json
    prompt = data.get('text', '').lower()
    
    # --- SMART AI INTENT DETECTION ---
    # Code khud detect karega ki prompt mein video manga hai ya image
    is_video_requested = any(word in prompt for word in ['video', 'animation', 'movie', 'mp4', 'animate'])
    
    if not is_video_requested:
        # --- 1. REAL IMAGE GENERATION (CACHE FIXED) ---
        seed = random.randint(1, 9999999) # Seed se purani image nahi aayegi, hamesha nayi banegi
        safe_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=512&height=512&seed={seed}&nologo=true"
        
        return jsonify({"status": "success", "format": "image", "url": image_url})
        
    else:
        # --- 2. REAL VIDEO GENERATION ---
        if not HF_API_TOKEN:
            return jsonify({
                "status": "error", 
                "message": "Asli Video banani hai toh code mein HF_API_TOKEN daalna padega! (Hugging Face se free mein milta hai)"
            })
            
        # Hugging Face ka powerful Text-to-Video Model
        API_URL = "https://api-inference.huggingface.co/models/damo-vilab/text-to-video-ms-1.7b"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        try:
            # Server se video mangwa rahe hain
            response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=120)
            
            if response.status_code == 200:
                os.makedirs("static", exist_ok=True)
                video_path = "static/output.mp4"
                with open(video_path, "wb") as f:
                    f.write(response.content)
                return jsonify({"status": "success", "format": "video", "url": "/" + video_path})
            else:
                return jsonify({"status": "error", "message": "Video API busy hai. Kuch der baad try karo."})
                
        except Exception as e:
            return jsonify({"status": "error", "message": f"Video fail: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
