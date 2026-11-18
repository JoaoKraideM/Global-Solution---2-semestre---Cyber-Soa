# Registro de uso de IA — Global Solution CitizenTech

As ferramentas de IA foram utilizadas como apoio ao planejamento do SombraViva, à revisão da estrutura SOA, à discussão de UX/UI e ao estudo dos cenários de Cybersecurity. A equipe é responsável por compreender, testar, validar e apresentar o funcionamento do projeto.

## Temas e solicitações de apoio

1. **Definição da CitizenTech.** Investigação do calor urbano em Osasco, com referência ao Calçadão da Rua Antônio Agú e à substituição de vegetação por estruturas artificiais de sombra; integração entre SOA, IoT e segurança.
2. **Backend e persistência.** Organização de API REST em FastAPI, modelagem relacional MySQL, migrações Alembic, autenticação de usuários e dispositivos, scripts de inicialização e testes automatizados.
3. **Dados climáticos.** Integração à Open-Meteo para consulta de histórico e comparação entre cidades; distinção entre ERA5, leitura pontual, simulação e hipótese científica.
4. **Proteção de dados.** Implementação demonstrativa de detecção de PII, taint analysis, bloqueio de destinos inseguros, trilhas de auditoria e visualização de risco acadêmico.
5. **Análise assistida de segurança.** Interpretação contextual de alertas por LLM, limitada a metadados permitidos; tratamento de resposta em JSON, revisão humana e fallback por regras locais.
6. **Experiência do usuário.** Organização da navegação e dos gráficos, identificação de estados de erro, acessibilidade e apresentação do território de estudo.

## Exemplo de instrução utilizada no módulo de segurança

> A partir exclusivamente dos metadados de um evento de segurança, explique o fato observado, hipóteses de impacto, verificações manuais recomendadas e evidências ausentes. Não presuma comprometimento, não solicite credenciais e não exponha informações pessoais.

As instruções técnicas efetivas de remediação e validação de saída estão no código de `app/llm.py` e `app/security_intelligence.py`.

## Validação

O módulo de LLM é opcional e só pode ser tratado como utilizado em execução real quando a configuração e o retorno efetivo forem confirmados. Respostas de regras locais são identificadas separadamente. Os dados pessoais empregados nos testes são fictícios. O uso de ferramentas de IA não substitui as evidências de execução, testes, banco MySQL e demonstrações exigidas pelas disciplinas.
