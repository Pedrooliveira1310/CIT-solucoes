"""Functional smoke check of the local demonstration instance; never prints cookies."""
import os
import time
import requests
url='http://127.0.0.1:5000'
for attempt in range(30):
    try:
        response=requests.get(url+'/login',timeout=2)
        if response.status_code==200: break
    except requests.RequestException:
        pass
    time.sleep(.5)
else:
    raise SystemExit('Servidor não ficou disponível.')
with requests.Session() as session:
    response=session.post(url+'/api/login',json={'email':'supervisor@demo.cti.local','password':os.environ.get('DEMO_PASSWORD','LocalDemo!2026')},timeout=10)
    response.raise_for_status()
    assert response.json()['redirect']=='/supervisor'
    response=session.get(url+'/api/metrics',timeout=5);response.raise_for_status()
    data=response.json()
    assert data['received']==data['analyzed']+data['pending']
    assert session.get(url+'/gestor',timeout=5).status_code==403
    assert session.get(url+'/api/reports',timeout=5).status_code==403
print('Smoke OK: login, indicadores e bloqueio entre perfis.')
