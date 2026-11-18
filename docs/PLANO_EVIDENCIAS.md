# Roteiro de entrega e evidências para a GS

## SOA (página 27 do enunciado)

- [x] Domínio com `User`, `Station`, `Reading`, `SecurityEvent` e `AuditFinding`
- [x] Configuração MySQL 8.4 + PyMySQL + SQLAlchemy; `docker compose` com banco persistente
- [ ] Capturar evidência de conexão real MySQL (`python scripts/check_mysql.py`) e tabelas no Workbench
- [x] Migração `alembic/versions/001_initial.py` preparada para o dialeto MySQL
- [ ] Capturar `SELECT * FROM alembic_version` após a migração aplicada no servidor MySQL
- [x] Documentação automática em `/docs`
- [x] Testes `python -m pytest -q` (unitários; integração real MySQL pendente)
- [ ] Capturar prints reais da aplicação, Swagger, testes e banco após executar
- [ ] Publicar GitHub com integrantes e README revisado

## Cybersecurity (páginas 28-29)

- [x] Padrões de detecção PII: CPF, e-mail, telefone, marcadores de senha/chave
- [x] Trilha explícita `TaintedValue` → sanitização → sink; bloqueio demonstrativo para destinos não redigidos
- [x] Dashboard de risco cidadão DEMO com fórmula pública
- [x] Registros de bloqueio de autenticação IoT e login sem conteúdo bruto
- [x] Opção de tradução dos achados por LLM, com fallback claramente identificado como regras
- [ ] Configurar e demonstrar uma chave válida de LLM, se exigida para pontuação completa
- [ ] Evidenciar os testes positivos/negativos do parser, caminhos permitidos e bloqueados
- [ ] Gravar vídeo curto da auditoria, dashboard e indicar riscos remanescentes
- [ ] Empacotar versão final ZIP para entrega do módulo

## IoT e demais disciplinas

- [x] Sketch ESP32 + DHT22 em `wokwi/`
- [ ] Importar no Wokwi e obter link do projeto após validar circuito e comunicação
- [ ] Ligar gateway privado local ou API publicamente acessível por HTTPS de testes
- [ ] Machine Learning: coletar séries reais públicas, preparar dataset, treinar/avaliar 10 combinações de 3 hiperparâmetros (dados simulados não aceitos em ML)
- [ ] Mobile: desenvolver cliente Expo se a equipe incluir a disciplina
- [ ] C#: criar serviço .NET separado se a equipe incluir a disciplina
- [ ] Sistemas Operacionais: provisionar Linux e monitorar os serviços (systemd, script e logs)
- [ ] Testing: criar Features e Test Cases positivos/negativos no Azure Boards

## Pitch de até 4 minutos

0:00–0:40: cidadão e problema, estudo de caso de Osasco e hipótese.
0:40–1:30: simulação de dados IoT e tela com comparação.
1:30–2:20: chamadas REST, Swagger e persistência.
2:20–3:10: PII, taint analysis, eventos e indicador de risco.
3:10–4:00: benefícios, limites, proposta de negócio e ODS.

**Importante:** nesta versão há infraestrutura de protótipo local; nenhum deploy ou link real do Wokwi/GitHub foi criado automaticamente.
