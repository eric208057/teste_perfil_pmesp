# PRISMA — histórico e guia do repositório

Este repo contém o **PRISMA** (Perfil de Risco e Inteligência para Seleção Militar e Atuação /
"Perfil de Referência, Inteligência e Mapeamento de Aptidões" nas telas mais novas), uma
ferramenta de perfil comportamental single-file (HTML+JS+Chart.js embutido, sem build step,
sem dependências externas), criada por 3° Sgt PM Éric (46°BPM/M).

Existem hoje **duas variantes do mesmo app**, cada uma em seu próprio arquivo:

| Arquivo | Público | Linguagem/terminologia |
|---|---|---|
| `index.html` | Policiais militares (PMESP) | "policial", "Comando", "guarnição", RE, postos PM |
| `index_civil.html` | Uso corporativo/civil | "colaborador", "Gestor", CPF, cargos genéricos (Júnior…Diretor) |

Ambos compartilham a mesma engine de scoring (funções e nomes de variáveis quase idênticos),
só muda o texto das perguntas/rótulos e as listas de referência (postos vs. cargos, PIPELINE,
CHECKLIST_*). Ao portar uma mudança de engine/scoring de um arquivo para o outro, comparar as
duas cópias das funções relevantes — elas não são geradas a partir de uma fonte única.

## Estrutura de módulos (dentro de cada arquivo)

Cada arquivo tem uma tela de menu com dois módulos:

1. **Autoavaliação PLUS** — a própria pessoa responde ~42-50 rodadas de escolha forçada
   (ipsativas) + 7 perguntas de concordância (Likert). Mapeia 4 eixos de comportamento
   estrutural A·C·R·F (Iniciativa/Análise, Fonte Motivadora, Estratégia no Tempo, Conforto no
   Ambiente) em duas versões — "estrutural" (natural) e "percepção no ambiente" (sob pressão) —
   mais perfil de conhecimento (Especialista/Generalista/Nexialista) e preferência operacional
   cruzada com os perfis funcionais de referência (GU_PROFILES, 12 no `index.html` / 20 no
   `index_civil.html`). Ao final, gera um relatório e permite exportar um `.json`
   (`kind:'prisma-autoavplus'`) para importar no módulo 2.
2. **Avaliação do Comando PLUS** (`index.html`) / **Avaliação do Gestor PLUS** (`index_civil.html`)
   — o avaliador observa a pessoa: 12 rodadas de escolha forçada nos mesmos eixos A·C·R·F (mas
   observados, não autorrelatados), checklists comportamentais também por escolha forçada
   (operacional, postura, liderança — opcional, só se a pessoa lidera equipe — e "método dos 30
   segundos"), um nível geral 1-5 por checklist (é esse nível geral, não a média ipsativa, que
   alimenta a Nine Box), perfil de conhecimento observado, Nine Box automática
   (`computeNineBoxFrom`), Pipeline de liderança (baseado no cargo/posto atual) e observações
   livres. Se o `.json` da Autoavaliação PLUS da mesma pessoa for importado
   (`importedSelfPlus`), o relatório final ganha uma seção de comparação
   estrutural-observado × autorrelatado (`buildCmdPlusComparison`). Documento de uso interno do
   avaliador — a UI deixa isso explícito ("não deve ser entregue ao avaliado").

Havia originalmente também uma "Autoavaliação" (24 rodadas, temperamento DISC) e uma "Avaliação
do Comando" (checklist Likert com âncoras comportamentais) mais simples/curtas — módulos 01/02
originais, anteriores à versão PLUS. O working tree do `index.html` (não commitado ainda no
momento deste histórico) as remove da tela de menu, deixando só as duas PLUS, renumeradas
01/02. Ver `index_old.html` (arquivo tracked, versão anterior completa) se precisar recuperar a
lógica desses módulos antigos.

### Engine de scoring — por que os dois módulos são diferentes de propósito

Não são inconsistência, é intencional: a Autoavaliação usa escolha forçada/ipsativa
(resiste a bias de auto-favorecimento — a pessoa não consegue se dar nota máxima em tudo) porque
mede *autopercepção*; a avaliação do gestor também virou escolha forçada nos checklists na versão
PLUS (isso é uma mudança em relação à primeira geração do app, que usava Likert 1-5 com âncoras
comportamentais + nota de evidência obrigatória nos extremos — esse mecanismo de âncora+evidência
foi *descartado* na versão PLUS em favor de forçar ranking relativo entre itens do checklist).
A pontuação ipsativa dos checklists mede só *ranking relativo* entre os itens (a soma por rodada
é sempre +2/-1/0/0, então a média através dos itens é ~constante não importa quem é avaliado) —
por isso existe a pergunta extra de "nível geral 1-5" em cada checklist, que é a única fonte de
nível *absoluto* e é o que de fato alimenta a Nine Box (ver comentários em torno de
`computeNineBoxFrom` no código, e `fcNorm`/`geralNorm`).

Se pedirem para "unificar" os dois métodos de novo, ou reintroduzir Likert+âncoras+evidência nos
checklists do avaliador: **essa troca já foi feita e revertida uma vez, na direção oposta à que
se poderia imaginar** — vale não repetir o ciclo sem reler isto. A ordem real dos fatos foi:
1. Geração original: Likert 1-5 com âncoras comportamentais (`lo`/`hi` em `CHECKLIST_OP/POSTURA/
   LID`) + nota de evidência obrigatória nos extremos. Nessa época, ranking/escolha forçada foi
   *proposto* como troca e **rejeitado**, exatamente pelos dois motivos abaixo (ranking força um
   "último colocado" mesmo quando a pessoa é forte em tudo, o que quebraria a lógica de "3+
   itens no fundo do ranking = problema comportamental claro"; e forçar ranking completo é mais
   lento que os 2 taps de um Likert, o que importa porque o instrumento original foi desenhado
   pra uso rápido/rotineiro).
2. Na reescrita pra versão PLUS, essa decisão foi **revertida**: o ranking forçado venceu afinal
   (ver primeiro parágrafo desta seção), pelo ganho de resistência a halo/tendência central que
   Likert simples não tem. O primeiro problema apontado em (1) foi mitigado, não ignorado —
   criando a pergunta separada de "nível geral 1-5" como única fonte de nível *absoluto* pra Nine
   Box (`geralNorm`/`computeNineBoxFrom`), deixando o ranking só com o papel de medir diferenciação
   relativa entre itens. O segundo problema (velocidade) foi um trade-off aceito, não resolvido.
   O mecanismo de âncora+evidência foi removido do fluxo (as classes CSS `.evidence-input`/
   `.evidence-wrap`/`.evidence-note` ficaram órfãs no `<style>`, sem nenhum template JS que as
   use — confirmado em `index_civil.html`) — `lo` de cada item do checklist também ficou órfão,
   só `hi` é mostrado (`itemStatement = it => it.hi`).

Conclusão pra quem for decidir de novo: o estado **atual** é ranking forçado, e essa é a decisão
mais recente, não a rejeitada. Reintroduzir Likert+âncoras+evidência significaria desfazer a
troca de (2), não repetir a lógica de (1). E a mensagem de interpretação "X item(ns) no fundo do
ranking → problema comportamental claro" (`showCmdPlusResult()`, ~linha 2609 em
`index_civil.html`) ainda carrega estruturalmente a limitação apontada em (1) — ela sempre vai
achar um "fundo do ranking" mesmo num checklist parametricamente forte; isso é aceitável porque
ela é só texto interpretativo hoje, não o que decide a Nine Box, mas vale lembrar disso se pedirem
pra tornar essa frase mais assertiva/decisiva.

### Bug de contraste de cor na impressão (se mexer em CSS/tema)

Cores de texto ajustadas pro tema escuro da tela (pastéis claros) não trocam sozinhas quando
`@media print` troca o fundo pra branco — ficam ilegíveis no PDF. O padrão usado pra resolver:
todas as cores de texto passam por CSS custom properties (`--text`, `--muted`, `--ok-text`,
`--warn-text`, `--danger`, `--c-*`), e o bloco `@media print` redefine essas variáveis com
valores próprios, escuros o suficiente pra ler em fundo branco.

Canvas (gráficos radar do Chart.js) é bitmap — não reage a `@media print` sozinho. A correção é
o listener `window.addEventListener('beforeprint'/'afterprint', repaintChartsForMedia)`, que relê
as CSS vars via `getComputedStyle` no momento ativo do print e força `chart.update()`/redesenho.
Qualquer gráfico novo precisa seguir esse mesmo padrão ou volta a sair lavado no PDF.

Também importante: `*{-webkit-print-color-adjust:exact;print-color-adjust:exact;}` dentro do
`@media print` — sem isso o Chrome descarta `background-color`/`box-shadow` ao imprimir sempre
que "Gráficos em segundo plano" estiver desmarcado (padrão do navegador), e os pontos coloridos
do gráfico bipolar e bolinhas de legenda (que são só `background`, sem borda própria) somem do
PDF mesmo com as variáveis de cor certas. Ao gerar PDF via `Page.printToPDF` (CDP), o parâmetro
equivalente é `printBackground: true` — sem ele, o mesmo problema se repete headless.

### Bug real encontrado e corrigido (2026-08-11): gráfico de estrela saía sem os dados

Na Autoavaliação PLUS, "Parte 5 · Perfil operacional" (`showPlusResults()`), o `new Chart(...)`
radar (`plusOpChart`) era criado **antes** do `showScreen('screen-plus-result')` que tira o
container `.hidden` (`display:none`). Um `<canvas>` dentro de um elemento `display:none` mede
`0x0` no momento em que o Chart.js lê o tamanho pra desenhar — o resultado no PDF era a
teia/grade do radar aparecendo normal (ela só depende do número de eixos, não do tamanho real do
canvas nem dos dados), mas **nenhum polígono de dado** (nem "Sua autoavaliação" nem o perfil
ideal comparado) — confirmado renderizando as páginas do PDF pra PNG com PyMuPDF
(`fitz`, já que poppler/`pdftoppm` não está instalado neste ambiente) e inspecionando
visualmente. Em uso real (clique manual no botão "Gerar PDF"), isso quase sempre passa
despercebido porque o `ResizeObserver` interno do Chart.js acaba pegando a mudança de tamanho
depois de alguns milissegundos/segundos de uso real da tela — mas é uma corrida (race condition)
sem garantia, não algo que o código força a acontecer certo.

**Fix aplicado** em `index_civil.html` e `index.html` (`showPlusResults()`): mover
`showScreen('screen-plus-result')` pra logo depois do `el.innerHTML = ...`, **antes** de criar o
`Chart` — assim o canvas já está com layout real (não mais escondido) no instante em que o
Chart.js mede e desenha, sem depender do timing do ResizeObserver. Regra geral pra qualquer
canvas/Chart.js novo neste app: sempre `showScreen(...)` (ou qualquer coisa que tire o
`display:none`) **antes** de instanciar o `Chart`, nunca depois.

De quebra, isso também expôs que a técnica de PDF headless (abaixo) estava recriando o mesmo tipo
de problema por um motivo relacionado mas diferente — ver a seção seguinte.

### Segundo bug relacionado (mesma investigação, 2026-08-11): pontos do gráfico na posição errada

Depois do fix acima, o gráfico passou a sair com dado — mas uma verificação numérica rigorosa
(não só visual) pediu confirmação extra: comparar, pra cada eixo, o valor calculado
(`r.userVec[i]`) contra o pixel realmente desenhado (`chart.getDatasetMeta(0).data[i].x/y`),
usando como gabarito tanto a própria função da lib (`chart.scales.r.getPointPositionForValue`)
quanto um cálculo trigonométrico independente (ângulo = -90° + i·(360°/N), sentido horário a
partir do topo). Descartadas primeiro as hipóteses óbvias: `chart.data.datasets[0].data` batia
exatamente com `r.userVec` (sem bug de dado chegando errado no `data:`), só existe um
`<canvas id="plusOpChart">` no documento e `Chart.getChart(canvas) === plusOpChart` (sem
duplicidade de instância/chart órfão sem `.destroy()`), e o `top.vec` batia com o `GU_PROFILES`/
`PF_PROFILES` certo por `code` (sem índice errado). Ou seja: os dados chegavam certos em todas as
etapas — o problema era só no desenho.

Com um wait curto (~300ms) depois de trocar pra mídia de impressão, os pontos realmente
desenhados **não** batiam com a posição esperada pro valor atual — ex.: o eixo ABR (ângulo 0°,
deveria ficar sempre à direita do centro não importa o valor) apareceu à ESQUERDA do centro, o
que é geometricamente impossível se o desenho estivesse usando o valor/ângulo atuais corretamente.
Aumentando a espera pra 3s e forçando `chart.resize(); chart.update('none');` antes de ler/imprimir,
os pontos passaram a bater exatamente (diff de 0.00px em todos os eixos). Isso isola a causa:
**não é bug de dado nem de duplicidade de chart — é corrida (race condition) entre a animação
padrão do Chart.js e o momento em que o PDF é capturado.** A troca pra mídia de impressão (via
`Emulation.setEmulatedMedia` no script, ou o `window.print()` real no app) muda o `max-width` do
`.wrap`, o que redimensiona o canvas; esse redimensionamento é tratado de forma assíncrona pelo
`ResizeObserver` do Chart.js, e se a captura do PDF acontecer antes desse ciclo terminar, some
capturado um frame no meio da animação de entrada do gráfico (que por padrão anima o polígono
"crescendo" a partir do centro) — os pontos ficam numa posição interpolada que não corresponde
nem ao estado antigo nem ao novo.

**Fix aplicado** (dois níveis, redundantes de propósito):
1. `chartScales()` (`index_civil.html` e `index.html`) ganhou `animation:false` — elimina
   qualquer tween, então não existe mais "meio da animação" pra capturar, nem pro app real nem
   pra qualquer automação futura.
2. `_simulacao/generate_pdf_via_cdp.py` também chama explicitamente
   `plusOpChart.resize(); plusOpChart.update('none');` logo depois de trocar pra mídia de
   impressão, como reforço determinístico (não depende só do `animation:false` do app).

Confirmado depois do fix: reprocessando a mesma verificação com timing normal de produção
(sem esperar os 3s), todos os 8 eixos bateram com diff de 0.00px, e visualmente uma persona
sintética com FIS/TIR/ABR muito altos (e o resto baixo) produziu um polígono que estufa
corretamente pro topo (FIS) e lado direito (TIR/ABR) do octógono — nenhum eixo trocado ou
espelhado.

## `_simulacao/` — porta Python da engine para QA sem abrir navegador

`simulate_prisma.py` é uma reimplementação fiel em Python da engine JS do `index.html` original
(Autoavaliação PLUS + Avaliação do Comando, incluindo o cruzamento via `.json` importado) — não
é o app, é uma cópia da lógica pra inspecionar rapidamente o resultado final de uma persona
simulada sem precisar clicar em ~50 rodadas no navegador a cada teste. Gera `full_output.txt`
(relatório em texto) e `autoavplus-simulado.json`. Como é uma porta manual, pode divergir do
JS real se a engine mudar — não usar como fonte de verdade de scoring, só como ferramenta de
inspeção rápida.

## PDFs de exemplo gerados via Chrome DevTools Protocol (headless)

Para ver o resultado final de um fluxo completo (relatório real, renderizado pelo app, não a
porta Python) sem precisar clicar manualmente em todas as rodadas do questionário, a abordagem
usada é: abrir o arquivo `file://` num Chrome headless com `--remote-debugging-port`, conectar
via WebSocket (CDP), usar `Runtime.evaluate` pra **injetar diretamente o estado global do app**
(`plusAnswers`, `plusData`, `cmdPlusAssess`, `cmdPlusStructAnswers`, etc. — todas variáveis
`let`/`var` no escopo global do `<script>` inline) pulando direto pras funções de render de
resultado (`showPlusResults()`, `showCmdPlusResult()`), depois `Page.printToPDF` (com
`printBackground:true`) pra exportar o relatório sem depender do diálogo nativo de impressão do
Chrome (que não é scriptável de forma confiável via automação de UI).

Isso funciona porque cada round do quiz só grava `{most, least}` num objeto indexado por número
de pergunta (`plusAnswers[i]`) ou numa array por seção do checklist (`cmdPlusAssess.op[r]` etc.)
— não há estado escondido em closures inacessíveis.

**Cuidado que já causou bug (2026-08-11):** a primeira versão do script disparava um evento
`beforeprint` falso (`window.dispatchEvent(new Event('beforeprint'))`) achando que isso bastava
pra acionar `repaintChartsForMedia()` com as cores certas antes do `Page.printToPDF`. Isso está
**errado**: despachar manualmente um `Event('beforeprint')` só chama os listeners JS registrados
com esse nome — não coloca o DOM ativo em `@media print` de verdade. `getComputedStyle()` chamado
dentro desse handler ainda lia as variáveis do tema de tela (escuro), não as print-safe, e —
mais grave — o reflow real necessário pra o `ResizeObserver` do Chart.js perceber que o canvas
mudou de tamanho (ver bug do gráfico de estrela acima) também não era disparado por um evento
falso. O `Page.printToPDF` em si aplica `@media print` corretamente, mas só na sua própria
passada de renderização interna — não retroage pro DOM "ao vivo" que o JS está lendo.

**Fix:** usar `Emulation.setEmulatedMedia({media:'print'})` via CDP *antes* de chamar
`repaintChartsForMedia()` — isso sim comuta o DOM ativo pra `@media print` de verdade (inclusive
forçando um reflow que ajuda o `ResizeObserver` a se atualizar), então esperar um instante (`time.sleep`)
antes do `Page.printToPDF`. Resetar pra `{media:''}` ao trocar de tela/fluxo. Isso está refletido
em `_simulacao/generate_pdf_via_cdp.py`.

O script usado (requer Python 3 + `pip install websocket-client`, e o Chrome instalado em
`C:\Program Files\Google\Chrome\Application\chrome.exe`) está preservado em
`_simulacao/generate_pdf_via_cdp.py` — os IDs de campo (`plusNome`, `cmdPlusAvaliadoNome`, etc.),
nomes de função (`choosePlus`, `submitPlusData`, `startPlusTest`, `chooseCmdPlus`,
`submitCmdPlusData`, `startCmdPlusStructQuiz`, `freshCmdPlusAssess`, `showCmdPlusResult`) e
tamanhos de checklist (`CHECKLIST_OP`=8 itens, `CHECKLIST_POSTURA`=7, `CHECKLIST_LID`=7,
`METHOD_30S`=4) são específicos de cada arquivo — ao reusar em `index.html` (versão PM), conferir
se esses nomes/tamanhos batem antes de rodar, e trocar `cmdPlusAvaliadoPosto`/`plusPosto` pros
valores de posto PM (`RANK_ORDER` do `index.html`) em vez dos cargos civis
(Júnior/Pleno/Sênior/Coordenador/Gerente/Diretor).
Chrome precisa da flag `--remote-allow-origins=*` (ou `--remote-allow-origins=http://127.0.0.1:<porta>`)
além de `--remote-debugging-port`, senão o handshake do WebSocket volta com 403 Forbidden — isso
mudou em versões recentes do Chrome por segurança.

Não há PDF de exemplo commitado no repo (dados fictícios de teste não devem ir pro histórico do
git) — os PDFs gerados ficam em diretórios de scratchpad por sessão, que são temporários. Se
precisar de um exemplo permanente, gerar de novo com o script e salvar deliberadamente num lugar
persistente.

## `apostila_pat_completa.json` — apostila oficial do método PAT® (fonte dos 59 perfis de família)

Conversão estruturada em JSON da apostila "Analista PAT® I — Apostila Criativa Humana" (111
páginas escaneadas, PDF via CamScanner fornecido pelo usuário — não é um dos três PDFs originais
da raiz do repo, é fonte nova). Estrutura:

- `meta` — título/descrição/origem.
- `sumario` — os 36 capítulos oficiais do livro, com página.
- `familias_perfis` — dado **estruturado e verificado manualmente** (não é OCR): as 9 famílias
  oficiais do método (Criativos Inovadores, Criativos Comunicadores, Analíticos, Executivos,
  Pesquisadores, Versáteis, Treinadores, Gestores, Realizadores), 61 perfis ao todo, cada um com
  `code` (Pxx), `name` e `graph_points_ACRF` — um vetor `{A,C,R,F}` lido por visão computacional
  (OpenCV, detecção da caixa e dos 4 pontos impressos) do gráfico impresso de cada perfil.
  **Cuidado:** esses valores são normalizados (0-1) **relativos à própria caixa do gráfico** —
  não há eixo numérico impresso no livro — servem pra comparar *formato* entre perfis, não são a
  mesma escala 0-100 absoluta usada no gráfico "Estrutural e Percepção" do relatório individual.
  P22 e P24 aparecem impressos em duas famílias (Criativos Inovadores *e* Analíticos); a apostila
  marca isso com "*" e diz que a família verdadeira é Analíticos — por isso só entram uma vez
  (61 → 59 perfis únicos) onde essa dedup é aplicada no app.
- `paginas_ocr` — as 111 páginas em texto corrido via `tesseract`, best-effort (pode ter ruído/
  erro de reconhecimento) — não usar como fonte canônica sem revisão humana, só pra busca rápida
  de conteúdo. Os três PDFs já listados no fim deste documento continuam sendo a fonte canônica
  de conteúdo pra checklists/perfis; este JSON é canônico especificamente pra `familias_perfis`
  (dado estruturado, não OCR).

### Integrado em ambos os arquivos (portado pra `index.html` em 2026-08-14)

Ambos `index.html` e `index_civil.html` têm `PAT_FAMILY_PROFILES` (os 59 perfis únicos,
`{code, name, family, vec:{A,C,R,F}}`) e `PAT_FAMILY_DESC` (texto de cada família) copiados
diretamente de `familias_perfis`, e `patProfileName(structNorm)` fazendo correlação de Pearson
(`pearson()`, já usada em `GU_PROFILES`) do vetor ACRF da pessoa contra os 59 vetores reais da
apostila — compara o *formato* do gráfico da pessoa contra os formatos oficiais do método PAT,
igual ao roteiro do analista PAT faria manualmente, em vez de reduzir a leitura a só 2 eixos.
Isso substituiu, nos dois arquivos, o critério antigo de "arquétipo" (par dos 2 eixos mais
intensos, tabela `PAT_PROFILES` com 24 combinações hi/lo *inventadas*, `patProfileName(structNorm,
structMean)` com 2 argumentos) — essa tabela antiga não existe mais em nenhum dos dois arquivos.
`PAT_ARCH_LABELS`/`PAT_POLES` (usados só pro texto "Combinação de eixos: X + Y", conceito
diferente de `patProfileName`) não mudaram e continuam iguais nos dois arquivos.

Testado no `index.html` via injeção de estado (mesmo mecanismo do
`_simulacao/generate_pdf_via_cdp.py`) nos dois módulos (Autoavaliação PLUS e Avaliação do Comando
PLUS) — ambos mostram corretamente o novo formato `"Nome do Perfil (Pxx)"` / `"Família X — ..."`,
sem erro de console, com a terminologia PM (postos, RE, OPM, "Comando") intacta.

## Estado no momento deste histórico (2026-08-11)

- `index.html`: modificado no working tree (não commitado) — remove os módulos originais
  01/02 (Autoavaliação e Avaliação do Comando "clássicas") da tela de menu, ficando só com as
  duas versões PLUS, renumeradas 01/02; texto "12 perfis operacionais" → "20 perfis
  operacionais"; ajustes de contraste de impressão do gráfico bipolar novo (dumbbell
  estrutural×percepção); no relatório da Avaliação do Comando PLUS (`showCmdPlusResult()`), o
  card "Perfil dominante" agora vem **antes** do card com os eixos A·C·R·F (antes vinha depois,
  inconsistente com a ordem do relatório da Autoavaliação); e o fix do gráfico de estrela
  descrito acima (`showScreen()` antes de criar o `Chart`).
- `index_civil.html`: novo, ainda não commitado — adaptação civil/corporativa do mesmo app
  (só os dois módulos PLUS, já nascem numerados 01/02, terminologia "colaborador"/"Gestor"/CPF).
  Mesmos dois fixes acima (ordem do "Perfil dominante" e gráfico de estrela) já aplicados aqui
  também.
- Os três PDFs fonte na raiz (`Apostila de Liderança...pdf`, `Avaliação Individual Rápida...pdf`,
  `perfis-pm-radar.pdf`) continuam sendo a fonte de conteúdo canônica pra qualquer checklist ou
  perfil novo — extrair texto com `pypdf` antes de inventar conteúdo (poppler/`pdftoppm` não
  está instalado neste ambiente, então a renderização nativa de página de PDF falha em PDFs de
  10+ páginas com imagem; usar extração de texto via `pypdf`, escrevendo em UTF-8 pra arquivo em
  vez de imprimir no console do Windows, que quebra em cp1252).

## Estado no momento deste histórico (2026-08-14)

- `apostila_pat_completa.json`: novo, ainda não commitado — ver seção acima. Já vetorizado em
  `index_civil.html` (`PAT_FAMILY_PROFILES`/`patProfileName`); `index.html` continua com o
  método antigo de arquétipo por par de eixos, ainda não portado.
- Nenhuma das mudanças listadas na entrada de 2026-08-11 acima foi commitada ainda — `index.html`
  modificado, `index_civil.html` e `_simulacao/generate_pdf_via_cdp.py` continuam untracked.
