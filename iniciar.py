"""Iniciador local para Windows, macOS e Linux. Somente dados fictícios."""
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
import venv
import webbrowser

ROOT=Path(__file__).resolve().parent

def main():
    os.chdir(ROOT)
    if sys.version_info<(3,12):
        raise RuntimeError('Instale Python 3.12 ou mais recente e tente novamente.')
    if not shutil.which('ffprobe') or not shutil.which('ffmpeg'):
        raise RuntimeError('FFmpeg não encontrado. Consulte LEIA-PRIMEIRO.txt e reabra o terminal depois de instalar.')
    with socket.socket() as check:
        if check.connect_ex(('127.0.0.1',5000))==0:
            raise RuntimeError('A porta 5000 já está ocupada. Feche a outra aplicação antes de iniciar.')
    python=ROOT/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not python.exists():
        print('Preparando ambiente Python...')
        venv.EnvBuilder(with_pip=True).create(ROOT/'.venv')
    print('Verificando dependências...')
    probe=subprocess.run([str(python),'-c','import flask, requests'],capture_output=True)
    if probe.returncode:
        subprocess.run([str(python),'-m','pip','install','--disable-pip-version-check','-r','requirements.lock'],check=True)
    config=os.environ.copy()
    config.setdefault('ANALYSIS_MODE','demo')
    config.setdefault('TRANSCRIPTION_MODE','demo')
    config['COOKIE_SECURE']='false'  # Execução HTTP exclusivamente local.
    subprocess.run([str(python),'-m','flask','--app','run','init-db'],env=config,check=True)
    database=Path(config.get('DATABASE_PATH',str(ROOT/'instance/cti.sqlite')))
    with sqlite3.connect(database) as connection:
        empty=connection.execute('SELECT count(*) FROM users').fetchone()[0]==0
    if empty:
        config.setdefault('DEMO_PASSWORD','LocalDemo!2026')
        subprocess.run([str(python),'-m','flask','--app','run','seed-demo'],env=config,check=True)
    children=[]
    try:
        children.append(subprocess.Popen([str(python),'-m','flask','--app','run','cleanup-loop'],env=config))
        server=subprocess.Popen([str(python),'-c',"from run import app; app.run(host='127.0.0.1',port=5000)"],env=config)
        children.append(server)
        for _ in range(60):
            if server.poll() is not None:
                raise RuntimeError('O servidor encerrou antes de iniciar. Veja a mensagem acima.')
            with socket.socket() as check:
                if check.connect_ex(('127.0.0.1',5000))==0:
                    break
            time.sleep(.5)
        else:
            raise RuntimeError('O servidor não iniciou no prazo esperado.')
        print('\nCTI Escuta está em execução local. Abrindo o navegador...')
        print('Mantenha esta janela aberta. Pressione Ctrl+C para encerrar.')
        webbrowser.open('http://127.0.0.1:5000/login')
        server.wait()
    except KeyboardInterrupt:
        print('\nEncerrando...')
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()

if __name__=='__main__':
    try:
        main()
    except (RuntimeError,subprocess.CalledProcessError,OSError) as error:
        print('\nNão foi possível iniciar:',error,file=sys.stderr)
        sys.exit(1)
