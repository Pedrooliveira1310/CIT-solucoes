"""Real Chromium end-to-end checks against an isolated database, never the demo instance."""
import io
import os
from pathlib import Path
import threading
import wave
import pytest
from werkzeug.serving import make_server
expect=pytest.importorskip('playwright.sync_api').expect
from app import create_app, initialize, seed

pytestmark=pytest.mark.skipif(os.environ.get('RUN_BROWSER_TESTS')!='1',reason='Use RUN_BROWSER_TESTS=1 and install requirements-dev.txt + Chromium')

@pytest.fixture(scope='module')
def site(tmp_path_factory):
    root=tmp_path_factory.mktemp('browser')
    os.environ['AUDIO_TEMP_DIR']=str(root/'audio')
    os.environ['ANALYSIS_MODE']='demo';os.environ['TRANSCRIPTION_MODE']='demo'
    app=create_app({'TESTING':True,'DATABASE':str(root/'browser.sqlite')})
    initialize(app);seed(app,'BrowserTest!2026')
    server=make_server('127.0.0.1',0,app,threaded=True)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield 'http://127.0.0.1:'+str(server.server_port),root
    server.shutdown();thread.join()

@pytest.fixture(scope='module')
def browser():
    playwright=pytest.importorskip('playwright.sync_api')
    with playwright.sync_playwright() as p:
        instance=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream'])
        yield instance
        instance.close()

@pytest.fixture
def page(browser,site):
    context=browser.new_context(viewport={'width':1440,'height':1000},permissions=['microphone'],locale='pt-BR')
    p=context.new_page();errors=[];p.on('pageerror',lambda error:errors.append(str(error)))
    yield p
    context.close()
    assert not errors, errors

def login(page,url,role):
    page.goto(url+'/login');page.fill('#email',role+'@demo.cti.local');page.fill('#password','BrowserTest!2026');page.click('button[type=submit]');page.wait_for_url(url+'/'+role);page.wait_for_selector('#workspace[aria-busy=false]')

@pytest.mark.parametrize('role,tabs',[('cliente',['atendimentos','enviar','feedbacks']),('atendente',['atendimentos','registrar','feedbacks']),('supervisor',['dashboard','atendimentos','feedbacks','criticos']),('gestor',['dashboard','tendencias','equipes','relatorios'])])
def test_navigation_and_exclusive_menu(page,site,role,tabs):
    url,_=site;login(page,url,role)
    assert page.locator('nav a').count()==len(tabs)
    for tab in tabs:
        page.click(f'nav a[href="/{role}/{tab}"]');page.wait_for_selector('#workspace[aria-busy=false]')
        assert page.locator('h1').inner_text()
        assert page.locator('#retry-page').count()==0
    foreign='gestor' if role!='gestor' else 'cliente'
    response=page.goto(url+'/'+foreign)
    assert response.status==403

def test_text_send_and_client_privacy(page,site):
    url,_=site;login(page,url,'cliente');page.goto(url+'/cliente/enviar');page.select_option('#ticket','1');page.fill('#feedback-text','Excelente atendimento pela interface.');page.check('#confirmed');page.click('#send-button');page.wait_for_selector('text=Obrigado por compartilhar sua experiência.');page.click('text=Ver meus feedbacks');page.wait_for_selector('.detail-button');page.locator('.detail-button').first.click();page.wait_for_selector('dialog[open]');assert 'Excelente atendimento pela interface.' in page.locator('#detail').inner_text();assert 'Análise automática' not in page.locator('#detail').inner_text()

def test_audio_attachment_review(page,site):
    url,root=site;login(page,url,'cliente');page.goto(url+'/cliente/enviar');page.select_option('#ticket','1');page.click('[data-origin=anexado]')
    output=io.BytesIO()
    with wave.open(output,'wb') as audio:
        audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(8000);audio.writeframes(b'\0\0'*8000)
    page.set_input_files('#audio-file',{'name':'teste.wav','mimeType':'audio/wav','buffer':output.getvalue()});page.click('#transcribe');expect(page.locator('#feedback-text')).to_be_enabled()
    assert 'DEMONSTRAÇÃO' in page.input_value('#feedback-text')
    assert list((root/'audio').iterdir())==[]
    page.fill('#feedback-text','Texto revisado após anexo de áudio.');page.check('#confirmed');page.click('#send-button');page.wait_for_selector('text=Obrigado por compartilhar sua experiência.')

def test_browser_recording_review(page,site):
    url,root=site;login(page,url,'cliente');page.goto(url+'/cliente/enviar');page.select_option('#ticket','1');page.click('[data-origin=gravado]');page.click('#record');expect(page.locator('#stop-record')).to_be_enabled();page.wait_for_timeout(1200);page.click('#stop-record');expect(page.locator('#transcribe')).to_be_enabled();page.click('#transcribe');expect(page.locator('#feedback-text')).to_be_enabled(timeout=30000);assert list((root/'audio').iterdir())==[];page.fill('#feedback-text','Texto confirmado da gravação no navegador.');page.check('#confirmed');page.click('#send-button');page.wait_for_selector('text=Obrigado por compartilhar sua experiência.')

def test_human_review_ui(page,site):
    url,_=site;login(page,url,'supervisor');page.goto(url+'/supervisor/feedbacks');page.wait_for_selector('.detail-button');page.locator('.detail-button').first.click();page.wait_for_selector('#review-form');page.select_option('#review-sentiment','neutro');page.fill('#justification','Revisão de teste com avaliação humana.');page.fill('#action','Entrar em contato com o cliente.');page.locator('#review-form button').click();expect(page.locator('#detail-dialog')).not_to_be_visible();assert 'Revisão registrada' in page.locator('#notice').inner_text()

def test_mobile_and_operational_registration(page,site):
    url,_=site;page.set_viewport_size({'width':390,'height':844});login(page,url,'atendente');page.goto(url+'/atendente/registrar');page.select_option('#client','1');page.fill('#subject','Suporte registrado no celular.');page.locator('#new-ticket button').click();page.wait_for_selector('#notice:not(:empty)');assert 'Atendimento registrado' in page.locator('#notice').inner_text();assert page.evaluate('document.documentElement.scrollWidth <= innerWidth');page.goto(url+'/atendente/atendimentos');page.wait_for_selector('.edit-ticket');page.locator('.edit-ticket').first.click();page.select_option('#status','resolvido');page.locator('#ticket-status button').click();expect(page.locator('#detail-dialog')).not_to_be_visible();assert 'Atendimento atualizado' in page.locator('#notice').inner_text()
