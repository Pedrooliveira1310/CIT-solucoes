# Validação da entrega

Executada em 22/10/2026 na instância de desenvolvimento, com Python 3.12.14, Flask 3.1.2, SQLite, FFmpeg/ffprobe e Chromium. Testes usam bancos isolados; o navegador usa microfone fictício, não grava pessoas.

| Verificação | Resultado |
| --- | --- |
| Backend e adaptadores (`tests/test_platform.py`, `tests/test_services.py`) | 36 testes aprovados |
| Navegador (`tests/test_browser.py`, `RUN_BROWSER_TESTS=1`) | 9 testes aprovados |
| Instalação por `scripts/install.sh`, repetida sobre banco existente | Aprovada; migração e dados preservados |
| Inicialização por `scripts/dev.sh` | Servidor e processo periódico de limpeza iniciados |
| `scripts/smoke.py` contra o serviço em execução | Login, indicadores reais do SQLite e bloqueios entre perfis aprovados |
| `flask cleanup-audio` | Executado com sucesso |
| JavaScript (`node --check`) e compilação Python | Aprovados |
| Inspeção visual de login/dashboard em Chromium | Realizada, interface provisória |

## Cobertura obrigatória

- Os quatro logins redirecionam pelo perfil do banco; cada menu mostra somente abas permitidas.
- URLs e APIs de outros perfis são bloqueadas.
- Consultas e IDs respeitam isolamento entre clientes, atendentes (inclusive na mesma equipe) e supervisores de equipes diferentes.
- Gestor acessa agregados/CSV; não recebe transcrições, evidências ou endpoints operacionais.
- Campos de privilégio extras são rejeitados; não há cadastro público. CSRF e logout são testados.
- Texto exige atendimento próprio e confirmação; retorna protocolo e persiste.
- Gravação MediaRecorder e anexo WAV percorrem preparação de texto, correção explícita e envio no Chromium. No modo de demonstração, o conteúdo retornado é um exemplo identificado, não transcrição do áudio.
- Validação de arquivo testa conteúdo falso, extensão, MIME, tamanho e duração; arquivos temporários são removidos no sucesso e na falha de transcrição. Arquivos abandonados antigos também são limpos.
- Um rascunho não pode ser confirmado por outro cliente nem reutilizado após confirmação.
- Revisão humana exige justificativa/providência e responsável da equipe, mantém análise original e registra autor/data/histórico.
- Falha de análise deixa feedback pendente, sem simular resultado real; indicadores refletem os registros do banco.
- Tela de 390 px: cadastro/atualização de atendimento sem rolagem horizontal do documento.

## Pendências externas e limites

- **Figma:** HTTP 403 pelo proxy; análise visual não realizada. **Site CTI:** HTTP 503 após tentativa de liberação de rede. Logo e cores oficiais não confirmados. Interface identifica lettering e paleta como provisórios; não se afirma fidelidade ao Figma.
- **IA/transcrição reais:** adaptadores implementados e contrato testado com respostas controladas; nenhuma chamada paga ou qualidade do serviço real foi validada. Falta configuração segura de `AI_API_KEY`, liberação de `api.openai.com` e avaliação documentada da política do provedor antes de ativar transcrição real.
- **Retenção:** exclusão local de áudio é implementada; não há garantia de exclusão remota pelo provedor. Infraestrutura deve excluir diretórios temporários de snapshots/backups e restringir logs/APM.
- **Produção:** requer HTTPS/WSGI, cookies Secure, conta/banco sem dados de demo, política LGPD, processo de recuperação de senha e implementação da retenção/anonimização de textos definida pela organização. SQLite/análise síncrona são escolhas de MVP acadêmico.
- **Publicação:** código preparado para entrega no repositório `Pedrooliveira1310/CIT-solucoes` mediante autorização do usuário. Isso não publica o site em uma hospedagem. `install_script`, `start_skill` e domínios CTI/Figma foram salvos no rascunho do ambiente. Publicação e validação numa nova tarefa ainda não executadas.
