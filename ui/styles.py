"""전역 CSS 스타일"""

import streamlit as st


def inject_global_styles():
    """전역 CSS 주입"""
    st.html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&display=swap');

        @keyframes flame {
            0%, 100% { text-shadow: 0 0 10px #ff6600, 0 0 20px #ff3300; }
            50% { text-shadow: 0 0 30px #ff3300, 0 0 50px #ff0000; }
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .title-container {
            text-align: center;
            padding: 30px 0 10px 0;
        }
        .title-text {
            font-family: 'Black Han Sans', sans-serif;
            font-size: 3.5rem;
            color: #FF4B4B;
            animation: flame 1.5s infinite;
            letter-spacing: 8px;
        }
        .subtitle-text {
            font-size: 1.1rem;
            color: #888;
            margin-top: 8px;
        }
        .vs-badge {
            font-family: 'Black Han Sans', sans-serif;
            font-size: 3rem;
            color: #FF4B4B;
            text-shadow: 0 0 20px rgba(255,75,75,0.5);
            animation: pulse 1s infinite;
        }
        .fighter-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            border: 2px solid #333;
        }
        .fighter-name {
            font-family: 'Black Han Sans', sans-serif;
            font-size: 1.5rem;
            color: #FAFAFA;
            margin-top: 10px;
        }
        .fighter-title {
            font-size: 0.9rem;
            color: #FF4B4B;
            margin-top: 4px;
        }
        .winner-text {
            font-family: 'Black Han Sans', sans-serif;
            font-size: 3rem;
            text-align: center;
            color: #FFD700;
            text-shadow: 0 0 20px rgba(255,215,0,0.5);
            animation: fadeInUp 1s ease-out;
        }
        .loser-text {
            font-family: 'Black Han Sans', sans-serif;
            font-size: 3rem;
            text-align: center;
            color: #666;
            animation: fadeInUp 1s ease-out;
        }
        .user-char-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 12px 16px;
            text-align: center;
            color: white;
            margin-bottom: 16px;
            animation: fadeInUp 0.5s ease-out;
        }
        .rarity-legendary { border-color: #ff9800 !important; box-shadow: 0 0 15px rgba(255,152,0,0.3); }
        .rarity-epic { border-color: #9c27b0 !important; box-shadow: 0 0 15px rgba(156,39,176,0.3); }
        .rarity-rare { border-color: #2196f3 !important; box-shadow: 0 0 15px rgba(33,150,243,0.3); }
    </style>
    """)
