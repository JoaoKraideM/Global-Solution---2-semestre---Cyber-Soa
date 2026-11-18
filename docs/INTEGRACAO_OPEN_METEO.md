# Integração Open-Meteo — consulta histórica e outras cidades

## Problema resolvido

O SombraViva tinha uma consulta meteorológica regional para Osasco e um endpoint de histórico sem interface no site. A integração agora permite selecionar datas e cidades diretamente no dashboard e comparar duas séries do mesmo período.

## Fluxo de dados

1. O cidadão digita o nome da cidade no website.
2. O JavaScript solicita `GET /api/v1/weather/places?search=...`.
3. O backend utiliza a Geocoding API da Open-Meteo e devolve até oito sugestões com nome, estado, país e coordenadas.
4. Após a seleção, o site solicita `GET /api/v1/weather/history?latitude=...&longitude=...&start_date=...&end_date=...`.
5. O backend consulta o modelo ERA5 pelo endpoint fixo da Historical Weather API, consolida indicadores, retorna os dados e informa procedência e resolução espacial.
6. O website mostra gráfico, tabela, extremos e CSV. Uma cidade adicional opcional utiliza o mesmo modelo e intervalo.

## Testes pela interface

1. Abrir `http://localhost:8000` após inicializar a API e o MySQL.
2. Ir à seção **Histórico climático**.
3. Selecionar `2025-01-01` a `2025-01-31` e clicar **Consultar histórico**.
4. Buscar `São Paulo` em **Comparar com**, escolher a cidade correta na lista e atualizar.
5. Conferir o gráfico das duas séries, a média de cada cidade e o CSV.
6. Tentar um intervalo maior que 366 dias: o site e a API devem rejeitar o pedido.
7. Repetir com outra cidade (por exemplo, `Barueri`, `Carapicuíba`, `Rio de Janeiro`).

A interface usa dados reais da fonte externa quando há conexão com a internet; os testes automatizados usam respostas simuladas **da API externa** para evitar dependência de rede e não devem ser confundidos com observações climáticas reais.

## Endpoints

```http
GET /api/v1/weather/places?search=Barueri
GET /api/v1/weather/history?latitude=-23.5329&longitude=-46.7917&start_date=2025-01-01&end_date=2025-01-31
GET /api/v1/weather/history/osasco?start_date=2025-01-01&end_date=2025-01-31
```

## Fonte, escala e metodologia

- **Geocodificação:** Open-Meteo Geocoding, com localidades baseadas em GeoNames.
- **Histórico:** Open-Meteo Historical Weather API, modelo ERA5 (reanálise meteorológica, resolução horizontal aproximada de 25 km).
- **Unidades:** °C para temperatura do ar a 2 m, por dia civil no fuso escolhido automaticamente pela fonte.
- **Janelas:** no máximo 366 dias; término pelo menos sete dias antes do dia atual.
- **Banco de dados:** MySQL armazena os registros das estações IoT, autenticação e auditoria; os dados externos são consultados sob demanda e não são gravados como se fossem leituras de sensores.
- **Interpretação:** diferenças entre cidades ou anos não demonstram, isoladamente, o efeito térmico da retirada de árvores no Calçadão. Isso requer levantamento local com instalação e calibração adequadas.
- **Uso comercial:** as condições da Open-Meteo para a API pública gratuita são direcionadas ao uso não comercial. Caso a plataforma seja monetizada, verificar licenças e limites de uso do fornecedor.

## Referências

- https://open-meteo.com/en/docs/geocoding-api
- https://open-meteo.com/en/docs/historical-weather-api
