"""Media helpers retained from the user's 068 audiobook renderer; no TTS entry."""
import json, subprocess

def run(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode:
        raise RuntimeError(f"命令失敗: {' '.join(map(str,cmd))}\n{p.stderr[-3000:]}")
    return p.stdout

def duration(path):
    return float(json.loads(run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(path)]))['format']['duration'])
