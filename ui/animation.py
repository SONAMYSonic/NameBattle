"""배틀 애니메이션 모듈"""

import streamlit.components.v1 as components
from ui.sounds import (
    AUDIO_INIT_JS, SFX_CLASH_JS, SFX_VS_SLAM_JS, SFX_IMPACT_JS,
    load_bgm_data_uri,
)


def render_battle_animation(
    player_name: str,
    opponent_name: str,
    player_img_b64: str,
    opponent_img_b64: str,
) -> None:
    """배틀 애니메이션 렌더링 (CSS/JS)

    시퀀스: 등장(0.8s) → 대치+떨림(0.7s) → VS(0.5s)
           → 돌진+충돌1(0.4s) → 튕김1(0.25s)
           → 돌진+충돌2(0.35s) → 튕김2(0.2s)
           → 돌진+최종충돌(0.3s) → 맞붙은 상태+충격파 → 화이트아웃(1.5s)
    """

    placeholder_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect width='200' height='200' fill='%23333'/%3E%3Ctext x='50%25' y='50%25' font-size='60' text-anchor='middle' dy='.3em' fill='%23666'%3E%3F%3C/text%3E%3C/svg%3E"

    player_src = f"data:image/png;base64,{player_img_b64}" if player_img_b64 else placeholder_svg
    opponent_src = f"data:image/png;base64,{opponent_img_b64}" if opponent_img_b64 else placeholder_svg

    battle_bgm_uri = load_bgm_data_uri("battle_bgm.mp3")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&display=swap');
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            background: #0E1117;
            overflow: hidden;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Black Han Sans', sans-serif;
        }}
        .arena {{
            position: relative;
            width: 100%;
            height: 450px;
            overflow: hidden;
        }}
        .character {{
            position: absolute;
            top: 50%;
            transform: translateY(-60%);
            text-align: center;
            z-index: 10;
        }}
        .character img {{
            width: 160px;
            height: 160px;
            border-radius: 16px;
            border: 3px solid #fff;
            box-shadow: 0 0 20px rgba(255,255,255,0.3);
            object-fit: cover;
        }}
        .character .name {{
            color: #fff;
            font-size: 1.2rem;
            margin-top: 8px;
            text-shadow: 0 0 10px rgba(255,255,255,0.5);
        }}

        /* 왼쪽 등장 */
        .left {{
            left: -250px;
            animation: slideInLeft 0.8s ease-out forwards;
        }}
        @keyframes slideInLeft {{
            to {{ left: 8%; }}
        }}

        /* 오른쪽 등장 */
        .right {{
            right: -250px;
            animation: slideInRight 0.8s ease-out forwards;
        }}
        @keyframes slideInRight {{
            to {{ right: 8%; }}
        }}

        /* 떨림 */
        .shake {{
            animation: shake 0.08s infinite;
        }}
        @keyframes shake {{
            0%,100% {{ transform: translateY(-60%) translateX(0); }}
            25% {{ transform: translateY(-60%) translateX(-4px); }}
            75% {{ transform: translateY(-60%) translateX(4px); }}
        }}

        /* VS 텍스트 */
        .vs {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -60%);
            font-size: 4rem;
            color: #FF4B4B;
            font-weight: 900;
            text-shadow: 0 0 30px #ff0000;
            opacity: 0;
            z-index: 20;
        }}
        .vs.show {{
            animation: vsAppear 0.4s ease-out forwards;
        }}
        @keyframes vsAppear {{
            from {{ opacity: 0; transform: translate(-50%,-60%) scale(3); }}
            to {{ opacity: 1; transform: translate(-50%,-60%) scale(1); }}
        }}

        /* 충격파 */
        .shockwave {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 10px;
            height: 10px;
            border-radius: 50%;
            border: 4px solid #fff;
            opacity: 0;
            z-index: 30;
        }}
        .shockwave.active {{
            animation: expand 0.6s ease-out forwards;
        }}
        @keyframes expand {{
            from {{ width:10px; height:10px; opacity:1; border-width:4px; }}
            to {{ width:800px; height:800px; opacity:0; border-width:1px; }}
        }}

        /* 화이트아웃 */
        .whiteout {{
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: white;
            opacity: 0;
            z-index: 50;
            pointer-events: none;
        }}
        .whiteout.active {{
            animation: fadeToWhite 1.5s ease-in forwards;
        }}
        @keyframes fadeToWhite {{
            0% {{ opacity: 0; }}
            40% {{ opacity: 0.7; }}
            100% {{ opacity: 1; }}
        }}

        /* 스파크 파티클 */
        .spark {{
            position: absolute;
            width: 6px;
            height: 6px;
            background: #FFD700;
            border-radius: 50%;
            opacity: 0;
            z-index: 25;
        }}
        .spark.active {{
            animation: sparkle 0.5s ease-out forwards;
        }}
        @keyframes sparkle {{
            from {{ opacity: 1; transform: translate(0, 0) scale(1); }}
            to {{ opacity: 0; transform: translate(var(--dx), var(--dy)) scale(0); }}
        }}
    </style>
    </head>
    <body>
    <div class="arena" id="arena">
        <div class="character left" id="charLeft">
            <img src="{player_src}" alt="player"/>
            <div class="name">{player_name}</div>
        </div>

        <div class="vs" id="vsText">VS</div>

        <div class="character right" id="charRight">
            <img src="{opponent_src}" alt="opponent"/>
            <div class="name">{opponent_name}</div>
        </div>

        <div class="shockwave" id="shock1"></div>
        <div class="shockwave" id="shock2"></div>
        <div class="whiteout" id="whiteout"></div>
        {"<audio id='bgm' autoplay loop><source src='" + battle_bgm_uri + "' type='audio/mpeg'></audio>" if battle_bgm_uri else ""}
    </div>

    <script>
        {AUDIO_INIT_JS}
        {SFX_VS_SLAM_JS}
        {SFX_IMPACT_JS}

        /* BGM 볼륨 설정 & 화이트아웃 시 페이드아웃 */
        var bgm = document.getElementById('bgm');
        if (bgm) {{ bgm.volume = 0.5; }}

        const L = document.getElementById('charLeft');
        const R = document.getElementById('charRight');
        const vs = document.getElementById('vsText');
        const shock1 = document.getElementById('shock1');
        const shock2 = document.getElementById('shock2');
        const whiteout = document.getElementById('whiteout');
        const arena = document.getElementById('arena');

        /* 스파크 파티클 생성 */
        function createSparks(n) {{
            for (let i = 0; i < n; i++) {{
                const s = document.createElement('div');
                s.className = 'spark';
                const a = (Math.PI * 2 / n) * i;
                const d = 40 + Math.random() * 60;
                s.style.setProperty('--dx', Math.cos(a)*d+'px');
                s.style.setProperty('--dy', Math.sin(a)*d+'px');
                s.style.top = '45%';
                s.style.left = '50%';
                arena.appendChild(s);
                setTimeout(() => s.classList.add('active'), 10);
            }}
        }}

        /* 화면 흔들림 (감쇠) */
        function screenShake(intensity, dur) {{
            const t0 = Date.now();
            (function frame() {{
                const e = Date.now() - t0;
                if (e > dur) {{ arena.style.transform = ''; return; }}
                const d = 1 - e / dur;
                const sx = (Math.random()-0.5) * intensity * d;
                const sy = (Math.random()-0.5) * intensity * d;
                arena.style.transform = 'translate('+sx+'px,'+sy+'px)';
                requestAnimationFrame(frame);
            }})();
        }}

        /* ─── 타임라인 ─── */

        /* 0.8s: 등장 완료 → 떨림 */
        setTimeout(() => {{
            L.style.left = '8%';
            R.style.right = '8%';
            L.classList.add('shake');
            R.classList.add('shake');
        }}, 800);

        /* 1.5s: VS 표시 */
        setTimeout(() => {{
            vs.classList.add('show');
            _vsSlam();
        }}, 1500);

        /* 2.0s: VS 사라지고, 첫 번째 돌진 시작 */
        setTimeout(() => {{
            vs.style.display = 'none';
            L.classList.remove('shake');
            R.classList.remove('shake');
            L.style.animation = 'none';
            R.style.animation = 'none';
            L.style.left = '8%';
            R.style.right = '8%';
            L.style.transition = 'left 400ms ease-in';
            R.style.transition = 'right 400ms ease-in';
            L.style.left = 'calc(50% - 160px)';
            R.style.right = 'calc(50% - 160px)';
        }}, 2000);

        /* 2.4s: 충돌 1 → 튕김 */
        setTimeout(() => {{
            _impact();
            createSparks(8);
            screenShake(10, 200);
            L.style.transition = 'left 250ms ease-out';
            R.style.transition = 'right 250ms ease-out';
            L.style.left = '18%';
            R.style.right = '18%';
        }}, 2400);

        /* 2.65s: 두 번째 돌진 */
        setTimeout(() => {{
            L.style.transition = 'left 350ms ease-in';
            R.style.transition = 'right 350ms ease-in';
            L.style.left = 'calc(50% - 160px)';
            R.style.right = 'calc(50% - 160px)';
        }}, 2650);

        /* 3.0s: 충돌 2 → 짧은 튕김 */
        setTimeout(() => {{
            _impact();
            createSparks(10);
            screenShake(14, 200);
            L.style.transition = 'left 200ms ease-out';
            R.style.transition = 'right 200ms ease-out';
            L.style.left = '25%';
            R.style.right = '25%';
        }}, 3000);

        /* 3.2s: 세 번째 돌진 (최종) */
        setTimeout(() => {{
            L.style.transition = 'left 300ms ease-in';
            R.style.transition = 'right 300ms ease-in';
            L.style.left = 'calc(50% - 150px)';
            R.style.right = 'calc(50% - 150px)';
        }}, 3200);

        /* 3.5s: 최종 충돌 — 맞붙은 상태로 유지 + 충격파 */
        setTimeout(() => {{
            _impact();
            createSparks(16);
            screenShake(22, 300);
            shock1.classList.add('active');
            setTimeout(() => shock2.classList.add('active'), 100);
        }}, 3500);

        /* 3.9s: 화이트아웃 (맞붙은 상태에서) + BGM 페이드아웃 */
        setTimeout(() => {{
            whiteout.classList.add('active');
            if (bgm) {{
                var fadeOut = setInterval(() => {{
                    if (bgm.volume > 0.05) {{ bgm.volume -= 0.05; }}
                    else {{ bgm.pause(); clearInterval(fadeOut); }}
                }}, 100);
            }}
        }}, 3900);
    </script>
    </body>
    </html>
    """

    components.html(html, height=460, scrolling=False)


def render_loading_animation(
    player_name: str,
    opponent_name: str,
) -> None:
    """탑블레이드 스타일 로딩 애니메이션

    두 이름이 원형 디스크로 궤도를 돌며 계속 충돌하고 튕깁니다.
    AI 생성이 완료될 때까지 무한 루프합니다.
    """

    loading_bgm_uri = load_bgm_data_uri("loading_bgm.mp3")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&display=swap');
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            background: #0E1117;
            overflow: hidden;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Black Han Sans', sans-serif;
        }}
        .loading-arena {{
            position: relative;
            width: 100%;
            height: 350px;
            overflow: hidden;
        }}
        .disc {{
            position: absolute;
            width: 120px;
            height: 120px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10;
            will-change: left, top;
        }}
        .disc-left {{
            background: radial-gradient(circle at 35% 35%, #FF6B6B, #CC0000, #8B0000);
            border: 3px solid rgba(255,255,255,0.3);
            box-shadow: 0 0 25px rgba(255,75,75,0.6), inset 0 0 15px rgba(0,0,0,0.3);
        }}
        .disc-right {{
            background: radial-gradient(circle at 35% 35%, #FFD700, #FF8C00, #B8860B);
            border: 3px solid rgba(255,255,255,0.3);
            box-shadow: 0 0 25px rgba(255,215,0,0.6), inset 0 0 15px rgba(0,0,0,0.3);
        }}
        .disc-spin {{
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background-image: repeating-conic-gradient(
                transparent 0deg, transparent 20deg,
                rgba(255,255,255,0.12) 20deg, rgba(255,255,255,0.12) 40deg
            );
            animation: selfSpin 0.4s linear infinite;
        }}
        @keyframes selfSpin {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        .disc-name {{
            position: relative;
            z-index: 2;
            color: #fff;
            font-size: 0.9rem;
            text-shadow: 0 0 8px rgba(0,0,0,0.9), 0 0 16px rgba(0,0,0,0.5);
            max-width: 100px;
            text-align: center;
            word-break: break-all;
            line-height: 1.2;
            pointer-events: none;
        }}
        .disc-glow {{
            position: absolute;
            width: 150px;
            height: 150px;
            border-radius: 50%;
            top: -15px;
            left: -15px;
            filter: blur(18px);
            opacity: 0.35;
            pointer-events: none;
        }}
        .disc-left .disc-glow {{
            background: #FF4B4B;
        }}
        .disc-right .disc-glow {{
            background: #FFD700;
        }}
        .center-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 2.8rem;
            color: #FF4B4B;
            font-weight: 900;
            text-shadow: 0 0 30px #ff0000, 0 0 60px rgba(255,0,0,0.4);
            opacity: 0;
            z-index: 20;
            pointer-events: none;
        }}
        .status-text {{
            position: absolute;
            bottom: 15px;
            left: 50%;
            transform: translateX(-50%);
            color: rgba(255,255,255,0.5);
            font-size: 0.85rem;
            letter-spacing: 2px;
            z-index: 5;
        }}
        canvas {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 30;
        }}
    </style>
    </head>
    <body>
    <div class="loading-arena" id="arena">
        <div class="disc disc-left" id="discLeft">
            <div class="disc-spin"></div>
            <span class="disc-name">{player_name}</span>
            <div class="disc-glow"></div>
        </div>
        <div class="disc disc-right" id="discRight">
            <div class="disc-spin"></div>
            <span class="disc-name">{opponent_name}</span>
            <div class="disc-glow"></div>
        </div>
        <div class="center-text" id="centerText"></div>
        <div class="status-text">BATTLE LOADING...</div>
        <canvas id="sparkCanvas"></canvas>
        {"<audio autoplay loop><source src='" + loading_bgm_uri + "' type='audio/mpeg'></audio>" if loading_bgm_uri else ""}
    </div>

    <script>
    window.onload = function() {{
        var arena = document.getElementById('arena');
        var dL = document.getElementById('discLeft');
        var dR = document.getElementById('discRight');
        var vsEl = document.getElementById('centerText');
        var cvs = document.getElementById('sparkCanvas');
        var c = cvs.getContext('2d');

        /* 효과음 초기화 */
        {AUDIO_INIT_JS}
        {SFX_CLASH_JS}

        cvs.width = arena.offsetWidth || 600;
        cvs.height = arena.offsetHeight || 350;
        var W = cvs.width, H = cvs.height;
        var mx = W / 2, my = H / 2 - 10;
        var oR = Math.min(110, mx - 80);
        if (oR < 50) oR = 50;

        var colors = ['#FFD700','#FF4B4B','#FF6B6B','#FFA500','#FFF'];
        var sparks = [];
        var sx = 0, sy = 0;
        var lastHit = 0;

        function boom(x, y) {{
            for (var i = 0; i < 18; i++) {{
                var a = Math.random() * 6.28;
                var v = 3 + Math.random() * 7;
                var l = 18 + Math.random() * 22;
                sparks.push({{x:x,y:y,vx:Math.cos(a)*v,vy:Math.sin(a)*v,s:2+Math.random()*4,c:colors[(Math.random()*5)|0],l:l,m:l}});
            }}
        }}

        function drawSparks() {{
            c.clearRect(0, 0, W, H);
            var alive = [];
            for (var i = 0; i < sparks.length; i++) {{
                var p = sparks[i];
                p.x += p.vx; p.y += p.vy; p.vy += 0.12; p.l--;
                if (p.l <= 0) continue;
                alive.push(p);
                var a = p.l / p.m;
                c.globalAlpha = a;
                c.fillStyle = p.c;
                c.beginPath();
                c.arc(p.x, p.y, p.s * a, 0, 6.28);
                c.fill();
            }}
            sparks = alive;
            c.globalAlpha = 1;
        }}

        /*
         * 중력 기반 팽이 배틀
         *
         * - 중앙 방향 인력으로 서로 끌려옴
         * - 쾅! 충돌 후 멀리 날아감
         * - 감속 → 다시 끌려옴 → 쾅!
         * - 가끔 한쪽이 크게 밀림
         */
        var x1 = 70, y1 = my, vx1 = 0, vy1 = 1.5;
        var x2 = W - 70, y2 = my, vx2 = 0, vy2 = -1.5;
        var minD = 120;
        var hitCount = 0;
        var ATTRACT = 0.005;
        var DAMPING = 0.993;
        var BOUNCE = 8;
        var MARGIN = 55;

        function tick() {{
            try {{
                var now = Date.now();

                /* 중앙 방향 인력 */
                vx1 += (mx - x1) * ATTRACT;
                vy1 += (my - y1) * ATTRACT;
                vx2 += (mx - x2) * ATTRACT;
                vy2 += (my - y2) * ATTRACT;

                /* 곡선 궤적을 위한 약한 회전력 */
                var tc1x = mx - x1, tc1y = my - y1;
                var tc2x = mx - x2, tc2y = my - y2;
                vx1 += -tc1y * 0.0008;
                vy1 += tc1x * 0.0008;
                vx2 += tc2y * 0.0008;
                vy2 += -tc2x * 0.0008;

                /* 감속 */
                vx1 *= DAMPING; vy1 *= DAMPING;
                vx2 *= DAMPING; vy2 *= DAMPING;

                /* 이동 */
                x1 += vx1; y1 += vy1;
                x2 += vx2; y2 += vy2;

                /* 충돌 감지 */
                var dx = x2 - x1;
                var dy = y2 - y1;
                var dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < minD && dist > 0.1) {{
                    hitCount++;
                    var nx = dx / dist, ny = dy / dist;

                    /* 겹침 분리 */
                    var overlap = (minD - dist) / 2;
                    x1 -= nx * overlap; y1 -= ny * overlap;
                    x2 += nx * overlap; y2 += ny * overlap;

                    /* 반발력 계산 */
                    var force = BOUNCE + Math.random() * 3;
                    var scatter = (Math.random() - 0.5) * 4;
                    var isBig = (hitCount % 4 === 0);

                    /* 비대칭 밀림 */
                    var r1, r2;
                    if (isBig) {{
                        if (Math.random() < 0.5) {{ r1 = 0.2; r2 = 1.2; }}
                        else {{ r1 = 1.2; r2 = 0.2; }}
                        force *= 1.3;
                    }} else {{
                        r1 = 0.7 + Math.random() * 0.3;
                        r2 = 0.7 + Math.random() * 0.3;
                    }}

                    vx1 = -nx * force * r1 + ny * scatter;
                    vy1 = -ny * force * r1 - nx * scatter;
                    vx2 = nx * force * r2 - ny * scatter;
                    vy2 = ny * force * r2 + nx * scatter;

                    /* 스파크 & 화면 흔들림 */
                    if (now - lastHit > 200) {{
                        lastHit = now;
                        var hx = (x1 + x2) / 2, hy = (y1 + y2) / 2;
                        boom(hx, hy);
                        if (isBig) {{ boom(hx, hy); boom(hx, hy); }}
                        _clash();
                        var shakeAmt = isBig ? 35 : 18;
                        sx = (Math.random() - 0.5) * shakeAmt;
                        sy = (Math.random() - 0.5) * shakeAmt;
                    }}
                }}

                /* 벽 바운드 (부드럽게) */
                if (x1 < MARGIN) {{ x1 = MARGIN; vx1 = Math.abs(vx1) * 0.3; }}
                if (x1 > W - MARGIN) {{ x1 = W - MARGIN; vx1 = -Math.abs(vx1) * 0.3; }}
                if (y1 < MARGIN) {{ y1 = MARGIN; vy1 = Math.abs(vy1) * 0.3; }}
                if (y1 > H - MARGIN) {{ y1 = H - MARGIN; vy1 = -Math.abs(vy1) * 0.3; }}
                if (x2 < MARGIN) {{ x2 = MARGIN; vx2 = Math.abs(vx2) * 0.3; }}
                if (x2 > W - MARGIN) {{ x2 = W - MARGIN; vx2 = -Math.abs(vx2) * 0.3; }}
                if (y2 < MARGIN) {{ y2 = MARGIN; vy2 = Math.abs(vy2) * 0.3; }}
                if (y2 > H - MARGIN) {{ y2 = H - MARGIN; vy2 = -Math.abs(vy2) * 0.3; }}

                /* 디스크 위치 */
                dL.style.left = (x1 - 60) + 'px';
                dL.style.top = (y1 - 60) + 'px';
                dR.style.left = (x2 - 60) + 'px';
                dR.style.top = (y2 - 60) + 'px';

                /* 흔들림 감쇠 */
                sx *= 0.78; sy *= 0.78;
                if (Math.abs(sx) > 0.3 || Math.abs(sy) > 0.3) {{
                    arena.style.transform = 'translate(' + sx + 'px,' + sy + 'px)';
                }} else {{
                    arena.style.transform = '';
                }}

                drawSparks();
            }} catch(e) {{}}
        }}

        setInterval(tick, 16);
    }};
    </script>
    </body>
    </html>
    """

    components.html(html, height=380, scrolling=False)
