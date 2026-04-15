from flask import Flask, render_template_string, request, jsonify
import urllib.parse
import time

app = Flask(__name__)

# Pura HTML, CSS aur JS ek hi string ke andar
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>AI Studio Pro</title>
    <style>
        :root {
            --neon-cyan: #00f3ff;
            --neon-purple: #bc13fe;
            --dark-bg: #0b0c10;
            --glass-bg: rgba(255, 255, 255, 0.05);
        }
        body {
            background-color: var(--dark-bg);
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            width: 100%;
            max-width: 400px;
            box-sizing: border-box;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.15);
        }
        h2 {
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 0;
            text-shadow: 0 0 10px var(--neon-cyan);
        }
        textarea {
            width: 100%;
            height: 90px;
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid var(--neon-cyan);
            color: #fff;
            border-radius: 8px;
            padding: 12px;
            box-sizing: border-box;
            margin-bottom: 15px;
            font-size: 14px;
            outline: none;
            resize: none;
        }
        textarea::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }
        textarea:focus {
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.4);
        }
        button {
            width: 100%;
            padding: 14px;
            margin-bottom: 12px;
            background: transparent;
            border: 2px solid var(--neon-purple);
            color: white;
            font-weight: bold;
            font-size: 15px;
            border-radius: 8px;
            cursor: pointer;
            text-transform: uppercase;
            transition: 0.3s;
            box-shadow: 0 0 10px rgba(188, 19, 254, 0.2);
        }
        button:active {
            background: var(--neon-purple);
            transform: scale(0.98);
        }
        .btn-img { 
            border-color: var(--neon-cyan); 
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.2); 
        }
        .btn-img:active { 
            background: var(--neon-cyan); 
            color: #000;
        }
        
        #output {
            margin-top: 20px;
            text-align: center;
            min-height: 250px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px dashed rgba(255,255,255,0.2);
            border-radius: 10px;
            background: rgba(0,0,0,0.3);
            overflow: hidden;
            padding: 5px;
        }
        img, video {
            max-width: 100%;
            max-height: 300px;
            border-radius: 8px;
            object-fit: cover;
        }
        .loader {
            color: var(--neon-cyan);
            font-weight: bold;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { opacity: 0.5; }
            50% { opacity: 1; text-shadow: 0 0 15px var(--neon-cyan); }
            100% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>AI Studio Pro</h2>
        <textarea id="prompt" placeholder="Enter prompt... (e.g., A futuristic cyberpunk car in neon city)"></textarea>
        
        <button class="btn-img" onclick="generateMedia('image')">Generate Image</button>
        <button onclick="generateMedia('video')">Generate Video</button>
        
        <div id="output">
            <span style="color: #888; font-size: 14px;">Media output will appear here</span>
        </div>
    </div>

    <script>
        async function generateMedia(type) {
            const prompt = document.getElementById('prompt').value;
            const outputDiv = document.getElementById('output');
            
            if(!prompt.trim()) {
                alert('Bhai, pehle prompt toh daal!');
                return;
            }

            outputDiv.innerHTML = '<span class="loader">Generating ' + type + '...<br>Wait karo bhai...</span>';

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt: prompt, type: type})
                });
                
                const data = await response.json();
                
                if(data.status === 'success') {
                    if(type === 'image') {
                        outputDiv.innerHTML = `<img src="${data.url}" alt="AI Generated Image">`;
                    } else {
                        // For video, we display the generated/dummy URL
                        outputDiv.innerHTML = `<video controls autoplay loop><source src="${data.url}" type="video/mp4"></video>
                                               <div style="font-size: 10px; color: var(--neon-purple); margin-top: 5px;">${data.message || ''}</div>`;
                    }
                } else {
                    outputDiv.innerHTML = `<span style="color: #ff3333;">Error: ${data.message}</span>`;
                }
            } catch(e) {
                outputDiv.innerHTML = `<span style="color: #ff3333;">Server connect nahi ho raha hai.</span>`;
            }
        }
    </script>
</body>
</html>
"""

# Route for rendering the UI
@app.route('/')
def home():
    return render_template_string(HTML_CODE)

# Route for handling API requests
@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    media_type = data.get('type', '')
    
    if media_type == 'image':
        # Free Text-to-Image API (No Key Required)
        # URL encoding prompt so it handles spaces properly
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true"
        
        return jsonify({
            "status": "success", 
            "url": image_url
        })
        
    elif media_type == 'video':
        # Simulating processing time
        time.sleep(2)
        
        # NOTE: Real text-to-video API requires Replicate/Hugging Face Tokens.
        # Aapko yahan apna actual API backend connect karna hoga.
        # Filhal ek dummy sample video bhej raha hoon player test karne ke liye.
        dummy_video = "https://www.w3schools.com/html/mov_bbb.mp4"
        
        return jsonify({
            "status": "success", 
            "url": dummy_video,
            "message": "(Note: Real Text-To-Video requires an API Key like HuggingFace/Replicate in backend)"
        })

if __name__ == '__main__':
    # Running on 0.0.0.0 taaki phone ke browser par http://localhost:5000 se access ho sake
    app.run(host='0.0.0.0', port=5000, debug=True)
