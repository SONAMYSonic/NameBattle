"""효과음 모듈 - Web Audio API 합성음 + MP3 파일 재생"""

import base64
import os
from functools import lru_cache

import streamlit.components.v1 as components

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds")


@lru_cache(maxsize=8)
def _load_sound_b64(filename: str) -> str:
    """사운드 파일을 base64로 로드 (캐시)"""
    path = os.path.join(SOUNDS_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def load_bgm_data_uri(filename: str) -> str:
    """BGM 파일을 data URI로 반환 (애니메이션 HTML 삽입용)"""
    b64 = _load_sound_b64(filename)
    if not b64:
        return ""
    return f"data:audio/mpeg;base64,{b64}"


def play_battle_start():
    """대결하기 버튼 클릭 효과음"""
    b64 = _load_sound_b64("battle_start.mp3")
    if not b64:
        return
    html = f"""<audio autoplay><source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg"></audio>"""
    components.html(html, height=0, width=0)


def _play_sfx(js_body: str) -> None:
    """Web Audio API 효과음을 iframe으로 재생 (브라우저 호환)"""
    html = f"""<script>
(function(){{try{{
var A=new(window.AudioContext||window.webkitAudioContext)();
A.resume().then(function(){{
{js_body}
}});
}}catch(e){{}}}})();
</script>"""
    components.html(html, height=0, width=0)


def play_match_found():
    """상대 확정 - 딩 소리"""
    _play_sfx("""
var t=A.currentTime;
[523,659,784].forEach(function(f,i){
  var o=A.createOscillator(),g=A.createGain();
  o.type='sine';o.frequency.value=f;
  g.gain.setValueAtTime(0.2,t+i*0.12);
  g.gain.exponentialRampToValueAtTime(0.001,t+i*0.12+0.4);
  o.connect(g);g.connect(A.destination);
  o.start(t+i*0.12);o.stop(t+i*0.12+0.4);
});
""")


def play_victory():
    """승리 팡파레"""
    _play_sfx("""
var t=A.currentTime;
var notes=[523,659,784,1047,784,1047];
notes.forEach(function(f,i){
  var o=A.createOscillator(),g=A.createGain();
  o.type='square';o.frequency.value=f;
  g.gain.setValueAtTime(0.18,t+i*0.15);
  g.gain.exponentialRampToValueAtTime(0.001,t+i*0.15+0.35);
  o.connect(g);g.connect(A.destination);
  o.start(t+i*0.15);o.stop(t+i*0.15+0.35);
});
""")


def play_defeat():
    """패배 사운드"""
    _play_sfx("""
var t=A.currentTime;
var notes=[392,349,311,262];
notes.forEach(function(f,i){
  var o=A.createOscillator(),g=A.createGain();
  o.type='sine';o.frequency.value=f;
  g.gain.setValueAtTime(0.18,t+i*0.25);
  g.gain.exponentialRampToValueAtTime(0.001,t+i*0.25+0.5);
  o.connect(g);g.connect(A.destination);
  o.start(t+i*0.25);o.stop(t+i*0.25+0.5);
});
""")


# ─── iframe 내부 삽입용 JS 스니펫 ───

AUDIO_INIT_JS = """
var _A=new(window.AudioContext||window.webkitAudioContext)();
_A.resume();
function _noise(dur,vol){
  var n=_A.createBufferSource(),b=_A.createBuffer(1,_A.sampleRate*dur,_A.sampleRate);
  var d=b.getChannelData(0);for(var i=0;i<d.length;i++)d[i]=(Math.random()*2-1);
  n.buffer=b;var g=_A.createGain();g.gain.setValueAtTime(vol,_A.currentTime);
  g.gain.exponentialRampToValueAtTime(0.001,_A.currentTime+dur);
  n.connect(g);g.connect(_A.destination);n.start();
}
function _tone(freq,dur,vol,type){
  type=type||'sine';var o=_A.createOscillator(),g=_A.createGain();
  o.type=type;o.frequency.value=freq;
  g.gain.setValueAtTime(vol,_A.currentTime);
  g.gain.exponentialRampToValueAtTime(0.001,_A.currentTime+dur);
  o.connect(g);g.connect(_A.destination);o.start();o.stop(_A.currentTime+dur);
}
"""

SFX_CLASH_JS = """
function _clash(){_noise(0.12,0.4);_tone(120,0.15,0.3,'square');_tone(80,0.2,0.2,'sine');}
"""

SFX_VS_SLAM_JS = """
function _vsSlam(){_tone(60,0.4,0.35,'square');_noise(0.15,0.3);_tone(40,0.5,0.25,'sine');}
"""

SFX_IMPACT_JS = """
function _impact(){_noise(0.2,0.5);_tone(50,0.3,0.4,'square');_tone(100,0.15,0.25,'sawtooth');}
"""
