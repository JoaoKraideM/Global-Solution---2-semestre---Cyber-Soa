# SombraViva — Inteligência Climática Urbana

## Ficha CitizenTech · Global Solution 2026.2

A ficha abaixo responde ao briefing comum da equipe e abre o repositório, antes da documentação técnica.

| Campo solicitado | Resposta da equipe |
|---|---|
| **Nome da CitizenTech** | **SombraViva — Inteligência Climática Urbana** |
| **Cidade e bairro** | **Osasco (SP), região central**. Estudo inicial no Calçadão da Rua Antônio Agú; os locais exatos dos futuros sensores ainda dependem de estudo de campo. |
| **Cidadão beneficiado** | Pedestres, trabalhadores expostos ao sol, pessoas idosas, comerciantes e gestores de planejamento urbano. |
| **Problema, em uma frase** | A população e os gestores têm dificuldade de acessar informações contextualizadas e verificáveis sobre exposição ao calor, presença de sombra e vegetação nos espaços públicos. |
| **Como funciona** | Uma API REST integra leituras de sensores, banco de dados e fontes meteorológicas externas; um observatório web apresenta séries, comparações e seus limites de proveniência; um painel administrativo registra e investiga eventos de segurança. |
| **O que cada parte faz** | **SOA:** FastAPI, endpoints REST, autenticação, MySQL, Swagger e migrações. **IoT:** ESP32 e DHT22 (Wokwi) e envio de leituras autenticadas, inicialmente simuladas. **Cybersecurity:** proteção de PII, JWT, auditoria, alertas e triagem. **Web:** visualização de temperaturas e contexto urbano, diferenciando estimativas, dados reais e simulações. |
| **Link do repositório** | https://github.com/JoaoKraideM/sprintSoaCyber |
| **Indicador de impacto** | **Indicador proposto:** quantidade de locais com leituras válidas e cobertura temporal do monitoramento, comparável por período, com base nisso levantamento de dados em tempo real, unificando um desenvolvimento sustentável junto de um futuro verde. Indicadores secundários: estações ativas e utilização do portal. |
| **ODS conectados** | **ODS 3** — Saúde e Bem-Estar; **ODS 11** — Cidades e Comunidades Sustentáveis; **ODS 13** — Ação Contra a Mudança Global do Clima. |

> **Integridade dos dados:** imagens de arquitetura são referências de proposta; valores IoT de demonstração são simulações; dados Open-Meteo/ERA5 são estimativas regionais.

---

**Global Solution FIAP · CitizenTech · Engenharia de Software · 2º semestre de 2026**  
**Cidade de referência:** Osasco (SP), com estudo inicial no Centro e no Calçadão da Rua Antônio Agú  
**Disciplinas contempladas neste repositório:** Arquitetura Orientada a Serviços (SOA) e Web Services; Cybersecurity; protótipo de integração IoT  
**ODS:** 3 — Saúde e Bem-Estar; 11 — Cidades e Comunidades Sustentáveis; 13 — Ação Contra a Mudança Global do Clima

## Sobre o projeto

O **SombraViva** é uma CitizenTech voltada ao estudo do calor urbano, da arborização e da disponibilidade de sombra nos espaços públicos. O projeto parte do contexto de Osasco, incluindo a discussão sobre a revitalização do Calçadão da Rua Antônio Agú, e propõe uma plataforma capaz de integrar informações climáticas, dispositivos de medição e controles de segurança digital.

A solução oferece um **observatório web** com histórico meteorológico, comparação entre cidades, representação territorial, cenários IoT e um painel administrativo de Cybersecurity. A API foi construída em **FastAPI**, com armazenamento **MySQL**, migrações **Alembic**, documentação **OpenAPI/Swagger** e testes automatizados.

**Problema:** cidadãos e gestores nem sempre dispõem de dados acessíveis e adequadamente contextualizados para estudar a exposição ao calor e planejar intervenções de sombreamento e arborização.

**Proposta:** organizar dados e permitir análises transparentes, distinguindo medições locais, estimativas regionais e simulações. O objetivo é dar suporte à investigação e à tomada de decisão, não afirmar uma relação causal sem estudo de campo.

### Cidadãos beneficiados

Pedestres, trabalhadores ao ar livre, pessoas idosas, comerciantes e equipes responsáveis pelo planejamento dos espaços urbanos.

### Limites científicos do protótipo

- **Open-Meteo/ERA5:** dados históricos regionais de reanálise, com resolução espacial aproximada de 25 km; **não são medições na Rua Antônio Agú**.
- **Estações IoT iniciais:** dispositivos e leituras fictícios, identificados como simulação; o projeto também disponibiliza a integração ESP32/DHT22 para testes no Wokwi.
- **Mapa térmico demonstrativo:** grade matemática sintética, sem temperaturas medidas nas ruas de Osasco.
- **Arborização e calor:** a intervenção no Calçadão contextualiza o problema; medir seu efeito térmico exige instrumentos calibrados, locais e horários comparáveis e controle de condições externas.

## Identidade visual e referências arquitetônicas

A interface pública apresenta o SombraViva como **caderno urbano editorial**, com tipografia e hierarquia de portfólio arquitetônico, fotografias documentais do Calçadão de Osasco e um estudo visual de referência. O painel administrativo mantém sua linguagem operacional própria.

O caso de referência é o **projeto nº 18, vencedor do Concurso de Revitalização do Calçadão da Rua Antônio Agú (2019)**, de **Letícia Juliana Pazian e Marina Vasarini Lopes**. São abordados os conceitos de cobertura translúcida, vegetação, piso drenante, espaços de permanência, mobiliário e conectividade, sempre como proposta de projeto, não como prova de execução total ou redução térmica observada.

Fontes usadas na página pública:

- [AEAO — concurso e autoria](https://www.aeaosasco.org.br/concurso-revitalizacao/) e [pranchas originais da proposta](https://www.aeaosasco.org.br/wp-content/uploads/2019/12/concurso_revitalizacao_osasco.pdf): perspectiva de projeto, **não fotografia da obra**;
- [Visão Oeste — fotografia do Calçadão (2022)](https://visaooeste.com.br/osasco-recebe-programa-cidadania-itinerante/): fotografia utilizada na abertura;
- [O Anhanguera — arquivo do Calçadão com coqueiros](https://www.oanhanguera.com.br/noticias/479-calcadao-de-osasco-sera-revitalizado-coberto-e-funcionara-24h): fotografia anterior à intervenção;
- [Agência Mural — reportagem e fotografia (2021)](https://agenciamural.org.br/calcadao-de-osasco-perde-coqueiros-e-divide-opiniao-de-moradores/): imagem durante a transformação;
- [Wikimedia Commons — Parque Ecológico Jardim Piratininga](https://commons.wikimedia.org/wiki/File:Parque_Ecol%C3%B3gico_Jardim_Piratininga_-_panoramio.jpg): fotografia de BêS (2010), CC BY-SA 3.0.

**Proveniência:** imagens jornalísticas e de concurso são de terceiros e permanecem carregadas de seus endereços externos, com links para as publicações e identificação de foto/perspectiva. O projeto não distribui cópias dessas imagens no ZIP. 
## Funcionalidades

| Área | Recursos |
|---|---|
| Observatório público | Indicadores climáticos, localização dos pontos de estudo, fontes e metodologia |
| Histórico climático | Consulta por cidade e período, comparação opcional entre duas cidades, gráficos diários e exportação CSV |
| IoT | Registro autenticado de temperatura/umidade, listagem de estações e histórico de leituras |
| Cartografia | Localização de referências em Osasco, mapa OpenStreetMap sob demanda e cenário térmico sintético |
| Cybersecurity | Login administrativo JWT, auditoria de eventos, alertas, triagem com justificativa e histórico de decisões |
| Proteção de dados | Detecção e mascaramento de PII, demonstração de taint analysis e bloqueio de destinos inseguros |
| Análise assistida | Recomendações de remediação e interpretação de alertas com OpenAI **opcional** ou regras locais identificadas |

Os registros demonstrativos de Cybersecurity são separados dos incidentes observados. Um alerta indica um **sinal a investigar**, não uma invasão confirmada.

## Arquitetura

```text
Navegador / painel público e administrativo
                 |
                 v
          FastAPI / REST
          /      |       \
         /       |        \
     MySQL    Open-Meteo   Cybersecurity
       |      (API externa)   |  JWT / PII / taint / IA opcional
       |
  Estações e leituras
       ^
       |
ESP32/DHT22 (Wokwi) ou simulador Python
```

**Tecnologias principais:** Python 3.12, FastAPI, SQLAlchemy, PyMySQL, MySQL 8.4, Alembic, Pydantic, JWT, HTML/CSS/JavaScript, Docker Compose, pytest e GitHub Actions. O frontend consome os serviços REST; o backend concentra a lógica de validação, persistência, autenticação e integração externa.

### Entidades MySQL

| Tabela | Finalidade |
|---|---|
| `users` | Administradores e hashes de senhas |
| `stations` | Dispositivos, identificação de simulação e hash de chave IoT |
| `readings` | Temperatura, umidade, horário e origem da leitura |
| `security_events` | Eventos de acesso, bloqueios e estado de investigação |
| `audit_findings` | Achados PII/taint com evidências redigidas |
| `security_triage_actions` | Trilha de decisões dos administradores |
| `alembic_version` | Controle da versão das migrações |

**Fonte de verdade do esquema:** `alembic/versions/`. O arquivo `sql/schema_mysql.sql` é apenas uma representação SQL de referência; **não deve ser aplicado manualmente** sobre o banco gerenciado pelo Alembic.

## Execução com Docker

### Pré-requisitos

- Docker Desktop com Docker Compose habilitado;
- Portas `8000` (API) e `3307` (MySQL no computador) livres, ou ajustadas conforme o ambiente;
- Git para versionamento e envio do trabalho.

### 1. Configurar credenciais

Na raiz do projeto, no PowerShell:

```powershell
Copy-Item .env.example .env
```

Edite o `.env` e configure os valores marcados com `SUBSTITUA`, especialmente:

```dotenv
DB_NAME=sombraviva
DB_USER=sombraviva
DB_PASSWORD=SENHA_FORTE_MYSQL
MYSQL_ROOT_PASSWORD=OUTRA_SENHA_FORTE_MYSQL
JWT_SECRET=CHAVE_ALEATORIA_FORTE
ADMIN_EMAIL=admin@sombraviva.local
ADMIN_PASSWORD=SENHA_FORTE_ADMIN
SENSOR_A_KEY=CHAVE_FORTE_ESTACAO_A
SENSOR_B_KEY=CHAVE_FORTE_ESTACAO_B
APP_ENV=development
SEED_DEMO_DATA=true
OPENAI_API_KEY=
```

Os valores acima são **exemplos de configuração, não credenciais utilizáveis**. Segredos da aplicação exigem no mínimo 16 caracteres; use valores aleatórios exclusivos. O usuário MySQL da aplicação **não pode ser `root`**. Não publique `.env` no GitHub.

Para gerar credenciais automaticamente **apenas se ainda não existir `.env`**, também é possível executar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preparar_env.ps1
```

### 2. Iniciar o sistema

```powershell
docker compose up -d --build
docker compose ps
```

Na primeira inicialização, o processo `scripts/start.sh` executa `python -m app.bootstrap`: aplica as migrações Alembic, cria o administrador a partir do `.env`, insere exemplos quando habilitados e verifica as tabelas antes de iniciar o Uvicorn.

A criação de exemplos é **idempotente**: reiniciar não duplica registros nem apaga dados existentes. Com `APP_ENV=production`, a inserção de novos registros fictícios é desabilitada.

| Serviço | Endereço |
|---|---|
| Website | http://localhost:8000 |
| Admin / Cybersecurity | http://localhost:8000/admin |
| Swagger | http://localhost:8000/docs |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| Status da API | http://localhost:8000/api/v1/health |
| Status do banco | http://localhost:8000/api/v1/health/db |

### 3. Verificar banco, migrações e logs

```powershell
docker compose exec api alembic current
docker compose exec api python -m scripts.check_mysql
docker compose logs api --tail=80
```

**Preserve o volume MySQL:** `docker compose down -v` apaga os dados persistidos. Mudar a senha no `.env` depois da primeira criação do usuário MySQL **não** atualiza automaticamente a conta já existente no banco.

### Inicialização automatizada no Windows

Para criar o `.env` quando necessário, iniciar os contêineres, verificar as tabelas e exportar um relatório sintético para `evidencias/`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\iniciar_demo.ps1
```

O script de demonstração não envia ataques e não executa chamadas pagas à OpenAI.

## API REST (prefixo `/api/v1`)

| Método | Rota | Uso |
|---|---|---|
| `GET` | `/stations` | Estações e últimas leituras |
| `GET` | `/stations/{code}/readings` | Leituras de uma estação |
| `POST` | `/stations/{code}/readings` | Receber leitura autenticada com `X-Device-Key` |
| `GET` | `/summary` | Resumo climático das estações |
| `GET` | `/weather/osasco` | Meteorologia externa |
| `GET` | `/weather/places?search=Barueri` | Buscar cidades |
| `GET` | `/weather/history` | Histórico regional por coordenadas e intervalo |
| `GET` | `/heatmap/demo` | Cenário térmico estritamente sintético |
| `POST` | `/auth/login` | Autenticação de administrador |
| `GET` | `/admin/operations` | Contadores operacionais e estado dos dispositivos |
| `GET` | `/admin/events` | Consulta de logs com filtros |
| `PATCH` | `/admin/events/{event_id}/triage` | Registrar decisão e justificativa |
| `GET` | `/admin/security/alerts` | Alertas para investigação |
| `POST` | `/admin/security/alerts/{event_id}/analyze` | Orientação por OpenAI ou regras locais |
| `POST` | `/admin/audit` | Detecção de PII e inspeção de fluxo |
| `POST` | `/admin/remediation` | Sugestões de remediação |

A documentação **completa e atualizada automaticamente a partir do código** está em `/docs`; a tabela acima destaca as operações principais.

### Exemplo: leitura IoT

```http
POST /api/v1/stations/centro-demo/readings
Content-Type: application/json
X-Device-Key: SUA_CHAVE_DO_SENSOR_A

{"temperature_c": 31.2, "humidity_pct": 58.0}
```

A API valida a chave e os campos, persiste a leitura e retorna `201` em caso de sucesso. A ausência de autorização é rejeitada. Consulte também `scripts/simulate_iot.py` e o circuito em `wokwi/`.

## Demonstração de Cybersecurity

1. Inicie a aplicação com `SEED_DEMO_DATA=true` em ambiente de desenvolvimento e abra `/admin`.
2. Entre usando `ADMIN_EMAIL` e `ADMIN_PASSWORD` do seu `.env`.
3. Consulte os alertas, incluindo os casos identificados como fictícios. O painel oferece evidências observadas, hipóteses e histórico de decisões.
4. Em um alerta, clique em **Examinar com IA / regras**. Com `OPENAI_API_KEY` válida, a análise pode utilizar a OpenAI. Sem chave ou em caso de falha, a aplicação indica o uso de regras locais (`ai_used=false`).
5. No **Laboratório PII**, teste com dados **inventados**, como `CPF: 000.000.000-00; senha: EXEMPLO_NAO_REAL`, escolhendo primeiro o destino `log_bruto` e depois `log_redigido` para comparar o bloqueio e a sanitização.
6. Observe a pontuação didática **Risco Cidadão** e os achados registrados sem conteúdo sensível bruto.

A integração com IA utiliza metadados permitidos e respostas estruturadas; **não comprova comprometimento nem realiza alterações automáticas nos sistemas**. A análise por regras locais não deve ser apresentada como resposta real da OpenAI.

## Testes automatizados e integração contínua

```powershell
docker compose exec api python -m pytest -q
```

O workflow **`.github/workflows/devsecops-pipeline.yml`** executa verificações em `push`, `pull_request` e manualmente: **testes e CSS**, **Gitleaks (segredos)**, **Bandit (SAST)**, **pip-audit (SCA)**, **Trivy (contêiner)** e **Resultado DevSecOps**. `tests` e `secrets` iniciam em paralelo; as três análises de segurança dependem dessas duas etapas e produzem status independentes; o resultado final falha caso qualquer etapa falhe ou seja cancelada. O fluxo não publica imagens nem cria infraestrutura. Veja [guia DevSecOps](docs/DEVSECOPS_PIPELINE.md).

Para executar a suíte fora do Docker, instale **`requirements-dev.txt`** (inclui `beautifulsoup4`, necessário para os testes de interface). Os testes usuais usam banco isolado e respostas controladas para serviços externos. Para executar a integração opcional com MySQL, configure `TEST_MYSQL_URL` apontando **somente para uma base de testes separada**, nunca para o banco principal.

```powershell
python -m pytest -m mysql_integration -q
```

## Organização do repositório

```text
SombraViva/
├── app/                 # API, domínio, autenticação, segurança, meteorologia e seed
├── alembic/             # Migrações do MySQL
├── static/              # Website, admin, estilos, JavaScript e imagens do próprio site
├── scripts/             # Bootstrap, simulação IoT, diagnóstico e verificações
├── sql/                 # Esquema de referência do MySQL
├── tests/               # Testes automatizados
├── wokwi/               # ESP32 e DHT22
├── docs/                # Ficha CitizenTech, fontes, impacto e evidências acadêmicas
├── .github/workflows/   # Pipeline DevSecOps em paralelo
├── requirements-dev.txt # Ferramentas necessárias para testes de UI no CI
├── .env.example         # Configuração sem segredos reais
├── compose.yaml         # API + MySQL 8.4
└── README.md
```

## Valor social e modelo de negócio

A consulta pública busca ser gratuita para o cidadão. A sustentabilidade financeira poderia vir de relatórios agregados para instituições, implantação e manutenção de sensores e estudos técnicos com universidades, empresas e governos. **Não há faturamento ou cobrança implementados neste protótipo.** Para uso comercial de dados externos, é preciso observar as condições de licença da fonte meteorológica.

Os possíveis indicadores de impacto incluem número de estações ativas, continuidade das leituras, cobertura de locais estudados, consultas ao portal e capacidade de apoiar políticas de conforto térmico. Nenhuma redução de temperatura é atribuída à intervenção de Osasco sem dados locais comparáveis.

## Documentação acadêmica

- [Ficha CitizenTech](docs/FICHA_CITIZENTECH.md) — público, problema, proposta, ODS e indicadores.
- [Fontes meteorológicas e metodologia](docs/INTEGRACAO_OPEN_METEO.md) — origem e limites do dado regional.
- [Proposta de valor e impacto](docs/NEGOCIO_E_IMPACTO.md) — benefícios e hipóteses de sustentabilidade.
- [Roteiro de evidências](docs/PLANO_EVIDENCIAS.md) — itens que precisam ser demonstrados ao professor.
- [Pipeline DevSecOps](docs/DEVSECOPS_PIPELINE.md) — CI, SAST, dependências, segredos, Trivy e tratamento de falhas.
- [Registro de prompts](prompts.md) — uso e validação de ferramentas de IA, conforme orientação da FIAP.

**Integrantes:** adicionar os nomes completos e RMs da equipe responsável por **esta Global Solution** antes de publicar o repositório. Não foram adicionados integrantes de outros trabalhos.

### Referências

- [Open-Meteo — Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [Open-Meteo — Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
- [OpenStreetMap](https://www.openstreetmap.org/)
- [Nações Unidas — Objetivos de Desenvolvimento Sustentável](https://sdgs.un.org/goals)
