# Ficha da CitizenTech — SombraViva

- **Nome:** SombraViva — Inteligência Climática Urbana
- **Cidade e bairro:** Osasco, São Paulo. Estudo inicial: região central/Calçadão da Rua Antônio Agú; pontos exatos de sensoriamento a definir em pesquisa de campo.
- **Cidadãos beneficiados:** pedestres, trabalhadores ao ar livre, idosos, comerciantes e gestores públicos.
- **Problema (uma frase):** a população e os gestores carecem de informação localizada e confiável para identificar e reduzir a exposição ao calor em áreas urbanas com diferentes condições de sombra e vegetação.
- **Como funciona:** uma API REST recebe leituras autenticadas de sensores, registra os dados em banco e disponibiliza séries de temperatura; um website apresenta comparações e contexto meteorológico externo; um módulo de Cybersecurity monitora acesso e fluxo de PII.
- **SOA:** API FastAPI, SQLAlchemy, Alembic, Swagger e testes automatizados.
- **Cybersecurity:** autenticação de administradores e dispositivos, logs sem dados sensíveis, identificação PII, rastreabilidade de dados contaminados, painel e tradução de achados por LLM quando habilitado.
- **IoT:** ESP32 e DHT22 no Wokwi; cenário inicial e sensores são simulados.
- **Indicadores de impacto (futuros):** número de pontos monitorados, cobertura temporal de leituras válidas, locais de estudo cadastrados, visitas ao portal e diferença entre estações comparáveis controlando fatores externos.
- **ODS:** 3 (Saúde e bem-estar), 11 (Cidades e comunidades sustentáveis) e 13 (Ação contra a mudança global do clima).
- **Repositório:** inserir URL do GitHub após a publicação.

## Hipótese de estudo

A retirada de vegetação pode modificar o microclima local, mas **o efeito térmico de uma intervenção específica de Osasco não está demonstrado neste protótipo**. É necessário caracterizar sombra, materiais, horários, precipitação, vento, posicionamento dos sensores, calibração e dias comparáveis. A plataforma permite construir evidência futura.

## Pesquisa com moradores (a realizar)

Entrevistar pelo menos um pedestre ou trabalhador do Centro: quanto tempo permanece exposto ao sol, como escolhe rotas e onde encontra sombra/hidratação. Registrar consentimento e evitar dados pessoais identificáveis no repositório.
