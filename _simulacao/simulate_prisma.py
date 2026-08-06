# -*- coding: utf-8 -*-
"""
Porta em Python (só para simulação/QA) da engine do PRISMA index.html:
  - Autoavaliação PLUS (perfil estrutural A/C/R/F + eixos derivados + índices + GU matching)
  - Avaliação do Comando (checklists ipsativos + Nine Box + sugestão automática),
    importando o JSON exportado pela Autoavaliação PLUS, igual ao fluxo real do app.

Não é o app - é uma reimplementação fiel da lógica em Python só para gerar e
inspecionar os relatórios finais sem precisar rodar no navegador.
"""
import json
import random
import sys
import statistics
sys.stdout.reconfigure(encoding="utf-8")

# ============================= AUTOAVPLUS: DADOS =============================

PAT_KEYS = ["A", "C", "R", "F"]
PAT_POLES = {
    "A": {"nome": "Iniciativa & Análise", "hi": "Intuitivo", "lo": "Sensorial"},
    "C": {"nome": "Fonte Motivadora", "hi": "Expressão Verbal", "lo": "Próprias Ideias"},
    "R": {"nome": "Estratégia no Tempo", "hi": "Amanhã Melhor", "lo": "Hoje Melhor"},
    "F": {"nome": "Conforto no Ambiente", "hi": "Estruturado", "lo": "Livre"},
}
PAT_ARCH_LABELS = {
    "A": {"hi": "Iniciativa", "lo": "Observação"},
    "C": {"hi": "Comunicação", "lo": "Reflexão"},
    "R": {"hi": "Constância", "lo": "Resposta Rápida"},
    "F": {"hi": "Estrutura", "lo": "Flexibilidade"},
}

def block(situacao, **opts):
    return {"situacao": situacao, "keys": list(opts.keys()), "opts": opts}

PAT_STRUCT_BLOCKS = [
    block("Numa ocorrência nova, sem procedimento claro definido, o que mais e o que menos te representa:",
          A="Decido na hora, confiando no instinto, mesmo sem ter todos os dados.",
          C="Chamo a equipe pelo rádio e resolvemos juntos, conversando enquanto agimos.",
          R="Espero alguns segundos a mais, deixando a situação se definir antes de agir.",
          F="Busco mentalmente o procedimento ou protocolo mais parecido antes de agir."),
    block("Ao assumir uma viatura ou equipe nova, o que mais e o que menos te representa:",
          A="Já vou testando meu próprio jeito de trabalhar, sem esperar todo mundo se ajustar.",
          C="Converso bastante nos primeiros dias pra criar entrosamento rápido.",
          R="Prefiro observar o ritmo da equipe por um tempo antes de mudar qualquer coisa.",
          F="Pergunto logo quais são as regras e rotinas já estabelecidas naquela guarnição."),
    block("Diante de uma tarefa administrativa chata mas necessária, o que mais e o que menos te representa:",
          A="Faço rápido, do meu jeito, mesmo que não siga o passo a passo à risca.",
          C="Prefiro fazer conversando com alguém, nem que seja só pra não ficar monótono.",
          R="Faço com calma, sem pressa, no meu tempo.",
          F="Sigo o modelo/formulário certinho, do jeito que deve ser feito."),
    block("Quando um colega discorda da sua forma de agir numa ocorrência, o que mais e o que menos te representa:",
          A="Defendo minha posição com firmeza, sem duvidar muito de mim.",
          C="Prefiro conversar bastante até a gente entender o lado um do outro.",
          R="Deixo o assunto esfriar antes de continuar a conversa.",
          F="Busco o que está escrito no procedimento pra resolver a divergência."),
    block("No planejamento de uma ação com prazo curto, o que mais e o que menos te representa:",
          A="Prefiro agir logo e ajustar o plano no caminho.",
          C="Prefiro alinhar verbalmente com todo mundo antes de sair.",
          R="Prefiro esperar mais informação antes de definir qualquer coisa.",
          F="Prefiro montar uma checklist antes de sair, mesmo com o tempo curto."),
    block("Ao lidar com um equipamento ou sistema novo (rádio, app, viatura), o que mais e o que menos te representa:",
          A="Vou mexendo, testando, sem ler manual.",
          C="Pergunto pra alguém que já usa, ao vivo.",
          R="Vou usando aos poucos, sem pressa de dominar tudo de uma vez.",
          F="Leio o manual ou instrução antes de usar."),
    block("Numa reunião de passagem de serviço, o que mais e o que menos te representa:",
          A="Vou direto ao ponto, sem enrolar em detalhes.",
          C="Gosto de comentar e trocar impressões, não só passar a informação seca.",
          R="Prefiro deixar quem está mais afobado falar primeiro, e entro com calma.",
          F="Sigo a ordem e o formato padrão de passagem, sem pular etapas."),
    block("Quando percebe um erro num relatório ou procedimento de outro colega, o que mais e o que menos te representa:",
          A="Aponto na hora, direto, sem rodeio.",
          C="Comento com jeito, numa conversa, pra não constranger.",
          R="Deixo pra falar num momento mais tranquilo, sem pressa.",
          F="Registro formalmente / sigo o canal correto para reportar."),
    block("Ao encarar uma mudança de escala ou rotina de última hora, o que mais e o que menos te representa:",
          A="Me adapto na hora, sem muito questionamento.",
          C="Preciso conversar sobre o motivo da mudança pra me sentir bem com ela.",
          R="Preciso de um tempo pra me ajustar mentalmente à mudança.",
          F="Fico incomodado quando a mudança quebra uma rotina já organizada."),
    block("No meio de uma abordagem que está indo bem, o que mais e o que menos te representa:",
          A="Sigo o instinto pra decidir os próximos passos, mesmo fora do script.",
          C="Uso a conversa como principal ferramenta pra manter o controle da situação.",
          R="Mantenho o ritmo calmo, sem acelerar desnecessariamente.",
          F="Sigo rigorosamente a sequência de segurança que aprendi no procedimento."),
    block("Quando alguém pede sua opinião sobre um problema complexo, o que mais e o que menos te representa:",
          A="Dou minha visão geral rápida, mesmo sem ter pensado em todos os ângulos.",
          C="Prefiro pensar em voz alta, junto com a pessoa.",
          R="Peço um tempo pra pensar com calma antes de responder.",
          F="Busco dados e critérios concretos antes de opinar."),
    block("Ao organizar seu material/equipamento de serviço, o que mais e o que menos te representa:",
          A="Não ligo muito pra organização, contanto que funcione.",
          C="Gosto de comentar/mostrar como organizei pros colegas.",
          R="Vou arrumando aos poucos, sem me apressar.",
          F="Gosto de tudo no lugar certo, seguindo um padrão fixo."),
    block("Diante de uma ordem que não faz muito sentido pra você, o que mais e o que menos te representa:",
          A="Questiono na hora, mesmo sabendo que pode gerar atrito.",
          C="Busco entender conversando com quem deu a ordem.",
          R="Cumpro por ora e só levanto o ponto depois, com calma.",
          F="Cumpro porque é a ordem, mesmo sem concordar totalmente."),
    block("No fim de um plantão puxado, o que mais e o que menos te representa:",
          A="Já penso na próxima ação/plantão, sem parar muito pra processar o que passou.",
          C="Preciso comentar o plantão com alguém antes de ir embora.",
          R="Preciso de um tempo sozinho pra desacelerar antes de qualquer coisa.",
          F="Reviso e fecho certinho tudo que precisa ser registrado antes de sair."),
    block("Ao aprender uma nova técnica ou tática, o que mais e o que menos te representa:",
          A="Prefiro já ir pra prática, aprendendo fazendo.",
          C="Aprendo melhor discutindo e trocando ideia sobre a técnica.",
          R="Prefiro repetir várias vezes, com calma, até internalizar.",
          F="Prefiro entender toda a lógica/passo a passo antes de praticar."),
    block("Quando o comando pede uma sugestão de melhoria para a rotina da equipe, o que mais e o que menos te representa:",
          A="Sugiro algo ousado, mesmo que mude bastante o jeito atual de trabalhar.",
          C="Prefiro reunir a equipe pra construir a sugestão junto.",
          R="Prefiro uma mudança gradual, testada aos poucos.",
          F="Sugiro algo que melhora o controle/organização sem bagunçar o que já funciona."),
]

PAT_PERCEP_BLOCKS = [
    block("Quando sente que está sendo avaliado por superiores, o que mais e o que menos passa a valer para você:",
          A="Tomo a frente e mostro iniciativa, mesmo sob os olhares de todos.",
          C="Procuro me comunicar mais e mostrar que estou alinhado com a equipe.",
          R="Fico mais cauteloso, evitando qualquer decisão precipitada.",
          F="Capricho ainda mais em seguir o procedimento à risca."),
    block("Num ambiente de trabalho novo e mais rígido, o que mais e o que menos passa a valer para você:",
          A="Seguro minha vontade de agir por conta própria até entender o terreno.",
          C="Procuro me expor menos até conhecer melhor as pessoas.",
          R="Passo a agir com ainda mais calma do que o normal.",
          F="Passo a seguir as regras à risca, mesmo sem concordar com todas."),
    block("Quando a cobrança por resultado aumenta, o que mais e o que menos passa a valer para você:",
          A="Assumo mais riscos e decido mais rápido do que faria normalmente.",
          C="Busco mais apoio da equipe, conversando mais que o de costume.",
          R="Mantenho o mesmo ritmo, resistindo à pressão pra acelerar.",
          F="Aumento o controle e a checagem de detalhes, com medo de errar."),
    block("Numa equipe que valoriza muito hierarquia e formalidade, o que mais e o que menos passa a valer para você:",
          A="Ainda assim, ajo pela própria conta quando julgo necessário.",
          C="Adapto minha forma de falar, ficando mais formal do que o habitual.",
          R="Espero mais antes de agir, respeitando os canais certos.",
          F="Sigo os protocolos formais rigorosamente, mesmo os que acho excessivos."),
    block("Quando o ambiente está tenso entre os colegas, o que mais e o que menos passa a valer para você:",
          A="Tomo posição e resolvo, mesmo correndo o risco de desagradar alguém.",
          C="Tento amenizar conversando com as partes envolvidas.",
          R="Fico mais recolhido, evitando entrar no atrito.",
          F="Me apoio nas normas/regras pra evitar decisão pessoal no meio do conflito."),
    block("Quando a rotina muda com frequência e sem aviso, o que mais e o que menos passa a valer para você:",
          A="Encaro numa boa, me adapto rápido sem muito custo.",
          C="Preciso comentar bastante com a equipe pra digerir cada mudança.",
          R="Sinto mais desgaste, precisando de mais tempo pra me ajustar.",
          F="Tento recriar alguma estrutura/rotina fixa, mesmo dentro da bagunça."),
    block("Diante de um superior mais controlador, o que mais e o que menos passa a valer para você:",
          A="Ainda tento manter minha autonomia dentro do possível.",
          C="Procuro manter contato e diálogo frequente pra evitar ruído.",
          R="Fico mais na minha, esperando orientação antes de agir.",
          F="Sigo à risca o que é pedido, sem questionar muito."),
    block("Quando precisa apresentar um resultado/relatório para pessoas de fora da equipe, o que mais e o que menos passa a valer para você:",
          A="Vou com confiança, mesmo sem ter preparado cada detalhe.",
          C="Invisto bastante na forma de comunicar, ensaiando o discurso.",
          R="Prefiro me preparar com calma e antecedência, sem pressa.",
          F="Capricho na formatação/organização do material apresentado."),
    block("Num plantão de alta demanda (muitas ocorrências seguidas), o que mais e o que menos passa a valer para você:",
          A="Decido rápido e sigo pra próxima, no automático.",
          C="Sinto necessidade de comentar/desabafar com a equipe entre uma ocorrência e outra.",
          R="Sinto o cansaço acumulando e preciso desacelerar em algum momento.",
          F="Me policio para não pular etapas dos procedimentos mesmo com pressa."),
    block("Quando percebe que o ambiente está cobrando um comportamento diferente do seu natural, o que mais e o que menos passa a valer para você:",
          A="Insisto no meu jeito, mesmo indo um pouco contra a corrente.",
          C="Tento me adaptar através da conversa, buscando entender a expectativa.",
          R="Levo um tempo pra aceitar e me ajustar à cobrança.",
          F="Me ajusto seguindo a régua/padrão que está sendo pedido."),
]

PONDERACAO_ITEMS = [
    {"text": "Ao decidir algo importante no serviço, me baseio mais nos fatos e nos dados concretos da situação do que no que as pessoas envolvidas estão sentindo.", "reverse": False},
    {"text": "Antes de aplicar uma medida mais dura, considero bastante o impacto emocional que isso vai ter na pessoa.", "reverse": True},
    {"text": "Consigo manter uma decisão mesmo sabendo que ela vai desagradar ou magoar alguém.", "reverse": False},
    {"text": "Tenho dificuldade de ser totalmente objetivo quando a situação envolve alguém que já conheço ou tenho afeto.", "reverse": True},
]
PERSPECTIVA_ITEMS = [
    {"text": "Hoje, consigo enxergar soluções para os principais desafios que estou enfrentando no serviço.", "reverse": False},
    {"text": "Meus objetivos dentro da corporação parecem alcançáveis no médio prazo.", "reverse": False},
    {"text": "Estou desanimado(a) em relação ao que vem pela frente na corporação.", "reverse": True},
]

PAT_AXES = [
    {"name": "Orientação", "a": "A", "b": "C", "aLabel": "Tecnicamente Orientado", "bLabel": "Socialmente Orientado"},
    {"name": "Preferência de Foco", "a": "A", "b": "F", "aLabel": "Generalista", "bLabel": "Especialista"},
    {"name": "Estilo de Ação", "a": "A", "b": "R", "aLabel": "Promovedor de Ações", "bLabel": "Mantenedor de Ações"},
    {"name": "Estilo de Conexão", "a": "C", "b": "R", "aLabel": "Rápida", "bLabel": "Ponderada"},
    {"name": "Tendência no Estilo Relacional", "a": "C", "b": "F", "aLabel": "Mais Informal", "bLabel": "Mais Formal"},
    {"name": "Como Lida com as Regras", "a": "R", "b": "F", "aLabel": "Casual", "bLabel": "Cuidadosa"},
]

PLUS_MUDANCAS_DESC = {
    "Fácil": "Nenhum dos quatro eixos muda de lado da média entre o jeito natural e o jeito adaptado ao ambiente — o ajuste existe, mas dentro do mesmo perfil, com baixo gasto de energia.",
    "Difícil": "Até dois eixos mudam de lado da média entre o estrutural e a percepção — sustentar essa adaptação por muito tempo exige energia real.",
    "Muito Difícil": "Mais de dois eixos mudam de lado da média — o ambiente está exigindo um comportamento bem distante do natural, o que tende a gerar desgaste se mantido por muito tempo.",
    "Insustentável": "Iniciativa (A) e Estrutura (F) se invertem e ficam do mesmo lado na percepção — combinação que costuma gerar insegurança em decisões estratégicas e ambiguidade de comportamento sob pressão. Vale atenção redobrada ao nível de estresse.",
}
PLUS_APROV_DESC = {
    "Sobre Aproveitado": "Na percepção do ambiente, a intensidade do comportamento exigido está bem acima do perfil natural — sinal de que está sendo cobrado mais do que pode ou quer entregar no momento.",
    "Subaproveitado": "Na percepção do ambiente, a intensidade do comportamento exigido está bem abaixo do perfil natural — sinal de subutilização da capacidade, não necessariamente ociosidade.",
    "Equilibrado": "A intensidade do comportamento exigido pelo ambiente está compatível com o perfil natural.",
}

# ---- Perfil de conhecimento (E/G/N) — igual ao módulo original ----
KNOW_BLOCKS = [
    block("Se pudesse escolher uma função por 6 meses, o que mais e o que menos combina com você:",
          E="Aprofundar uma técnica específica até virar referência nela.",
          G="Rodar por várias frentes, adaptando-se ao que aparecer.",
          N="Organizar e conectar pessoas e áreas diferentes em um projeto."),
    block("Quando aparece um problema novo e complexo, o que mais e o que menos te representa:",
          E="Estudar a fundo até dominar aquele problema específico.",
          G="Buscar uma solução prática rápida, mesmo sem dominar tudo.",
          N="Reunir pessoas de áreas diferentes para resolver juntos."),
    block("Seu maior risco de desgaste no serviço, o que mais e o que menos se aplica a você:",
          E="Isolamento, por focar demais em um único assunto.",
          G="Superficialidade, por tentar abraçar tudo ao mesmo tempo.",
          N="Sobrecarga, por assumir múltiplas frentes ao mesmo tempo."),
    block("Colegas normalmente recorrem a você, o que mais e o que menos combina:",
          E="Uma resposta técnica precisa sobre um assunto específico.",
          G="Resolver o que aparecer, sem exigir grande profundidade.",
          N="Juntar as pontas entre pessoas ou setores diferentes."),
    block("Num curso ou instrução, o que mais e o que menos combina com você:",
          E="Se aprofundar num único módulo até dominar de verdade.",
          G="Aprender um pouco de cada assunto, sem travar em nenhum.",
          N="Conectar o conteúdo com outras áreas que você já conhece."),
    block("Se pudesse escolher uma responsabilidade extra, o que mais e o que menos combina:",
          E="Ser referência técnica em um equipamento ou procedimento específico.",
          G="Circular entre setores cobrindo o que for preciso.",
          N="Coordenar um projeto que envolve várias equipes diferentes."),
    block("Depois de um curso ou capacitação, o que mais e o que menos te representa:",
          E="Vira a pessoa mais fundo naquele assunto na sua unidade.",
          G="Aplica o básico no dia a dia sem se aprofundar mais.",
          N="Passa a ensinar e conectar o conteúdo com outras equipes."),
    block("Numa reunião de planejamento, o que mais e o que menos te representa:",
          E="Contribui com um detalhe técnico que só você domina.",
          G="Ajuda a cobrir os pontos gerais que faltam.",
          N="Ajuda a conectar as partes que as outras áreas não estão vendo."),
]

AXES_ORDER = ["FIS", "TIR", "ABR", "COM", "JUR", "SOC", "DIR", "LID"]
AXES_FULL = {
    "FIS": "Físico", "TIR": "Tiro/Armamento", "ABR": "Abordagem", "COM": "Comunicação/Mediação",
    "JUR": "Conhecimento Jurídico", "SOC": "Primeiros Socorros", "DIR": "Direção/Viatura", "LID": "Liderança/Equipe",
}
OP_STATEMENTS = {
    "FIS": "Me sinto bem preparado fisicamente para perseguição, contenção e uso da força quando necessário.",
    "TIR": "Tenho domínio e segurança no manuseio de armamento e na decisão de quando usá-lo.",
    "ABR": "Me sinto confiante conduzindo abordagens a pessoas e veículos suspeitos.",
    "COM": "Consigo acalmar uma situação tensa só pela forma como converso com as pessoas.",
    "JUR": "Domino bem a legislação e os procedimentos aplicáveis às ocorrências que atendo.",
    "SOC": "Me sinto preparado para prestar primeiros socorros a uma vítima até o socorro especializado chegar.",
    "DIR": "Tenho facilidade e segurança para dirigir viatura ou moto em situação de urgência.",
    "LID": "Outros policiais recorrem a mim naturalmente quando é preciso organizar ou decidir algo em equipe.",
}
def op_window(start_idx):
    return [AXES_ORDER[(start_idx + i) % 8] for i in range(4)]
OP_BLOCKS = []
for i, _ in enumerate(AXES_ORDER):
    keys = op_window(i)
    OP_BLOCKS.append({"situacao": "Entre as afirmações abaixo, qual é a mais e a menos parecida com você:",
                       "keys": keys, "opts": {k: OP_STATEMENTS[k] for k in keys}})

CONHECIMENTO = {
    "E": {"nome": "Especialista", "alt": "Executor", "cor": "amber",
          "risco": "Isolamento, dificuldade de trabalhar em equipe, rigidez.",
          "uso": "Instrutor, planejamento operacional (P3/P5), referência técnica, análise de ocorrências complexas.",
          "exemplo": "Policial de Tiro, operador de sistemas do COPOM, mecânico de viatura, especialista em drones."},
    "G": {"nome": "Generalista", "alt": "Gestor", "cor": "green",
          "risco": "Superficialidade, dificuldade em aprofundar temas complexos.",
          "uso": "Coordenação de turno, atendimento ao público, suporte operacional, integração entre setores.",
          "exemplo": "Policial de radiopatrulha, auxiliar de pelotão, base de apoio."},
    "N": {"nome": "Nexialista", "alt": "Negociador", "cor": "steel",
          "risco": "Sobrecarga, dispersão de foco, burnout.",
          "uso": "Comando de equipe, projetos especiais, operações complexas, articulação intersetorial.",
          "exemplo": "Coordenador de grandes eventos, líder de equipe em ocorrência de múltiplas viaturas."},
}

GU_PROFILES = [
    {"code": "GU-01", "title": "Generalista de Patrulha Ostensiva", "w": {"C": 2, "S": 2, "F": 1, "M": 1}, "kv": {"E": 0, "G": 3, "N": 0},
     "vec": [7, 6, 7, 7, 6, 6, 7, 6], "why": "Combina decisão rápida com boa relação com o público — o perfil que sustenta a cobertura contínua do território."},
    {"code": "GU-02", "title": "Comunitário Pacificador", "w": {"C": 0, "S": 3, "F": 2, "M": 0}, "kv": {"E": 0, "G": 3, "N": 0},
     "vec": [5, 3, 4, 10, 6, 4, 4, 6], "why": "Comunicação forte e paciência para manter vínculo de longo prazo com a mesma área."},
    {"code": "GU-03", "title": "Tático de Confronto", "w": {"C": 3, "S": 0, "F": 1, "M": 0}, "kv": {"E": 3, "G": 0, "N": 0},
     "vec": [9, 9, 9, 4, 5, 5, 6, 6], "why": "Decisão sob risco extremo e foco técnico em cenários de confronto armado."},
    {"code": "GU-04", "title": "Motociclista de Ronda", "w": {"C": 2, "S": 0, "F": 2, "M": 0}, "kv": {"E": 0, "G": 3, "N": 0},
     "vec": [7, 6, 7, 5, 4, 4, 10, 4], "why": "Decisão rápida com estabilidade emocional para pilotar sob pressão em áreas de difícil acesso."},
    {"code": "GU-05", "title": "Socorrista Operacional", "w": {"C": 0, "S": 0, "F": 2, "M": 2}, "kv": {"E": 3, "G": 0, "N": 0},
     "vec": [7, 4, 4, 6, 4, 10, 5, 5], "why": "Calma sob pressão somada à atenção técnica exigida para estabilizar vítimas."},
    {"code": "GU-06", "title": "Mediador de Crise", "w": {"C": 0, "S": 1, "F": 3, "M": 0}, "kv": {"E": 0, "G": 0, "N": 3},
     "vec": [5, 3, 5, 10, 7, 7, 4, 6], "why": "Paciência e comunicação para de-escalar crises psicológicas e conflitos domésticos."},
    {"code": "GU-07", "title": "Comandante de Guarnição", "w": {"C": 3, "S": 0, "F": 0, "M": 1}, "kv": {"E": 0, "G": 0, "N": 3},
     "vec": [6, 6, 6, 7, 8, 5, 5, 10], "why": "Decisão firme e capacidade de conectar equipes em ocorrências complexas."},
    {"code": "GU-08", "title": "Apoio a Registro Técnico", "w": {"C": 0, "S": 0, "F": 0, "M": 3}, "kv": {"E": 3, "G": 0, "N": 0},
     "vec": [5, 4, 5, 7, 9, 4, 4, 5], "why": "Precisão analítica para registros que sustentam o trabalho da Polícia Civil."},
    {"code": "GU-09", "title": "Agente de Levantamento de Área", "w": {"C": 0, "S": 0, "F": 0, "M": 3}, "kv": {"E": 2, "G": 0, "N": 3},
     "vec": [5, 3, 6, 8, 8, 4, 5, 5], "why": "Leitura analítica de padrões conectada à inteligência da própria PM — sem substituir a Polícia Civil."},
    {"code": "GU-10", "title": "Policiamento Escolar", "w": {"C": 0, "S": 3, "F": 0, "M": 0}, "kv": {"E": 0, "G": 3, "N": 0},
     "vec": [5, 2, 4, 9, 7, 5, 4, 5], "why": "Comunicação entusiástica, essencial para criar vínculo de confiança com estudantes."},
    {"code": "GU-11", "title": "Cinotécnico (K9)", "w": {"C": 0, "S": 0, "F": 2, "M": 2}, "kv": {"E": 3, "G": 0, "N": 0},
     "vec": [8, 6, 8, 4, 4, 5, 6, 4], "why": "Paciência com o animal somada à precisão técnica do protocolo de faro."},
    {"code": "GU-12", "title": "Policiamento de Trânsito", "w": {"C": 1, "S": 0, "F": 0, "M": 3}, "kv": {"E": 3, "G": 0, "N": 0},
     "vec": [6, 4, 5, 6, 7, 5, 9, 4], "why": "Precisão e conformidade às normas, com firmeza para autuações em confronto."},
]

# ============================= ENGINE (porta fiel da lógica JS) =============================

def pearson(a, b):
    n = len(a)
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    num = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
    da = sum((x - mean_a) ** 2 for x in a)
    db = sum((x - mean_b) ** 2 for x in b)
    if da < 1e-6 or db < 1e-6:
        return 0
    return num / (da * db) ** 0.5

def to01(r):
    return (r + 1) / 2

def simulate_ipsative(blocks, pref, rng, jitter=2.5):
    """pref: dict key->score. Picks most=argmax/least=argmin of pref+jitter per round,
    so a persona doesn't answer the exact same way every single round (more realistic)."""
    answers = []
    for q in blocks:
        keys = q["keys"]
        jittered = {k: pref.get(k, 0) + rng.uniform(-jitter, jitter) for k in keys}
        most = max(keys, key=lambda k: jittered[k])
        least = min(keys, key=lambda k: jittered[k])
        answers.append({"most": most, "least": least})
    return answers

def norm_ipsative(blocks, answers, keys):
    score = {k: 0 for k in keys}
    for q, a in zip(blocks, answers):
        score[a["most"]] += 2
        score[a["least"]] -= 1
    n = len(blocks)
    return {k: (score[k] + n) / (n * 3) for k in keys}

def compute_plus_results(struct_answers, percep_answers, know_answers, op_answers, likert):
    struct_norm = norm_ipsative(PAT_STRUCT_BLOCKS, struct_answers, PAT_KEYS)
    percep_norm = norm_ipsative(PAT_PERCEP_BLOCKS, percep_answers, PAT_KEYS)

    know_score = {"E": 0, "G": 0, "N": 0}
    for q, a in zip(KNOW_BLOCKS, know_answers):
        know_score[a["most"]] += 2
        know_score[a["least"]] -= 1
    know_norm = {k: (know_score[k] + 8) / 24 for k in know_score}
    know_rank = sorted(know_norm, key=lambda k: -know_norm[k])

    op_score = {a: 0 for a in AXES_ORDER}
    for q, a in zip(OP_BLOCKS, op_answers):
        op_score[a["most"]] += 2
        op_score[a["least"]] -= 1
    user_vec = [((op_score[k] + 4) / 12) * 10 for k in AXES_ORDER]

    approx_temp = {"C": struct_norm["A"], "S": struct_norm["C"], "F": struct_norm["R"], "M": struct_norm["F"]}
    user_temp_vec = [approx_temp[k] for k in ["C", "S", "F", "M"]]
    user_know_vec = [know_norm[k] for k in ["E", "G", "N"]]

    scored = []
    for p in GU_PROFILES:
        profile_temp_vec = [p["w"][k] for k in ["C", "S", "F", "M"]]
        temp_component = to01(pearson(user_temp_vec, profile_temp_vec))
        profile_know_vec = [p["kv"][k] for k in ["E", "G", "N"]]
        know_component = to01(pearson(user_know_vec, profile_know_vec))
        op_component = to01(pearson(user_vec, p["vec"]))
        score = 0.5 * op_component + 0.28 * temp_component + 0.22 * know_component
        scored.append({**p, "score": score, "opComponent": op_component, "tempComponent": temp_component, "knowComponent": know_component})
    max_score = max(s["score"] for s in scored)
    min_score = min(s["score"] for s in scored)
    for s in scored:
        s["pct"] = round(((s["score"] - min_score) / (max_score - min_score or 1)) * 45 + 55)
    scored.sort(key=lambda s: -s["score"])

    axes = []
    for ax in PAT_AXES:
        va, vb = struct_norm[ax["a"]], struct_norm[ax["b"]]
        total = va + vb
        pct_a = round((va / total) * 100) if total > 0 else 50
        pct_b = 100 - pct_a
        axes.append({**ax, "pctA": pct_a, "pctB": pct_b,
                     "dominant": ax["aLabel"] if pct_a >= pct_b else ax["bLabel"],
                     "strength": max(pct_a, pct_b)})

    vals = [struct_norm[k] for k in PAT_KEYS]
    spread_pct = round((max(vals) - min(vals)) * 100)
    spread_level = ("Muito Alto" if spread_pct >= 65 else "Alto" if spread_pct >= 45 else
                     "Médio" if spread_pct >= 22 else "Baixo" if spread_pct >= 10 else "Muito Baixo")

    struct_mean = sum(struct_norm[k] for k in PAT_KEYS) / 4
    percep_mean = sum(percep_norm[k] for k in PAT_KEYS) / 4

    suporte_raw = sum(abs(struct_norm[k] - struct_mean) for k in PAT_KEYS)
    suporte_pct = round((suporte_raw / 2) * 100)
    suporte_level = ("Muito Alto" if suporte_pct >= 70 else "Alto" if suporte_pct >= 50 else
                      "Médio" if suporte_pct >= 30 else "Baixo" if suporte_pct >= 15 else "Muito Baixo")

    dA = struct_norm["A"] - struct_mean
    dF = struct_norm["F"] - struct_mean
    conflito = "Sem conflito relevante entre Iniciativa (A) e Estrutura (F)."
    if abs(dA - dF) < 0.08 and abs(dA) > 0.06 and abs(dF) > 0.06 and (dA > 0) == (dF > 0):
        conflito = ("Conflito do lado alto: iniciativa/ousadia (A alto) tensiona com a necessidade de controle e cautela (F alto) — pode gerar indecisão ou estresse diante do inesperado, com baixa tolerância a erro."
                    if dA > 0 else
                    "Conflito do lado baixo: a acomodação (A baixo) tensiona com a resistência a regras (F baixo) — combinação que pode gerar imprevisibilidade de comportamento.")

    pond_sum = 0
    for i, item in enumerate(PONDERACAO_ITEMS):
        v = likert.get(f"pond{i}", 3)
        if item["reverse"]:
            v = 6 - v
        pond_sum += v
    pond_avg = pond_sum / len(PONDERACAO_ITEMS)
    ponderacao = "Emocional" if pond_avg < 2.4 else "Racional" if pond_avg > 3.6 else "Equilibrado"

    persp_sum = 0
    for i, item in enumerate(PERSPECTIVA_ITEMS):
        v = likert.get(f"persp{i}", 3)
        if item["reverse"]:
            v = 6 - v
        persp_sum += v
    persp_avg = persp_sum / len(PERSPECTIVA_ITEMS)
    perspectiva = "Baixa" if persp_avg < 2.4 else "Alta" if persp_avg > 3.6 else "Equilibrada"

    flips = 0
    a_flipped = f_flipped = same_side_after = False
    for k in PAT_KEYS:
        side_before = struct_norm[k] >= struct_mean
        side_after = percep_norm[k] >= percep_mean
        if side_before != side_after:
            flips += 1
            if k == "A":
                a_flipped = True
            if k == "F":
                f_flipped = True
    if a_flipped and f_flipped and (percep_norm["A"] >= percep_mean) == (percep_norm["F"] >= percep_mean):
        same_side_after = True
    if same_side_after:
        mudancas = "Insustentável"
    elif flips == 0:
        mudancas = "Fácil"
    elif flips <= 2:
        mudancas = "Difícil"
    else:
        mudancas = "Muito Difícil"

    percep_suporte_raw = sum(abs(percep_norm[k] - percep_mean) for k in PAT_KEYS)
    energia_diff = round(((percep_suporte_raw - suporte_raw) / 2) * 100)
    aproveitamento = "Equilibrado"
    if energia_diff >= 12:
        aproveitamento = "Sobre Aproveitado"
    elif energia_diff <= -12:
        aproveitamento = "Subaproveitado"

    arch_order = sorted(PAT_KEYS, key=lambda k: -abs(struct_norm[k] - struct_mean))
    def arch_label(k):
        return PAT_ARCH_LABELS[k]["hi" if struct_norm[k] >= struct_mean else "lo"]
    arquetipo = f"{arch_label(arch_order[0])} + {arch_label(arch_order[1])}"

    return {
        "structNorm": struct_norm, "percepNorm": percep_norm, "structMean": struct_mean, "percepMean": percep_mean,
        "knowNorm": know_norm, "knowRank": know_rank, "userVec": user_vec, "ranked": scored, "axes": axes,
        "spreadPct": spread_pct, "spreadLevel": spread_level, "suportePct": suporte_pct, "suporteLevel": suporte_level,
        "conflito": conflito, "ponderacao": ponderacao, "pondAvg": pond_avg, "perspectiva": perspectiva, "perspAvg": persp_avg,
        "mudancas": mudancas, "flips": flips, "aproveitamento": aproveitamento, "energiaDiff": energia_diff, "arquetipo": arquetipo,
    }

# ============================= SIMULAÇÃO: PERSONA "PLUS" =============================
# Persona: iniciativa alta, comunicativo, pouco paciente, resiste a estrutura no natural,
# mas fica mais formal/estruturado quando avaliado (Percepção) -> deve gerar "Mudanças"
# perceptíveis e possivelmente conflito/insustentável se A e F invertem juntos.

RNG = random.Random(42)

PREF_STRUCT = {"A": 9, "C": 7, "R": 2, "F": 1}
PREF_PERCEP = {"A": 3, "C": 5, "R": 4, "F": 9}   # sob avaliação, fica bem mais estruturado/cauteloso
PREF_KNOW = {"E": 8, "G": 3, "N": 2}
PREF_OP = {"FIS": 8, "TIR": 9, "ABR": 8, "COM": 3, "JUR": 2, "DIR": 6, "SOC": 3, "LID": 4}

struct_answers = simulate_ipsative(PAT_STRUCT_BLOCKS, PREF_STRUCT, RNG)
percep_answers = simulate_ipsative(PAT_PERCEP_BLOCKS, PREF_PERCEP, RNG)
know_answers = simulate_ipsative(KNOW_BLOCKS, PREF_KNOW, RNG)
op_answers = simulate_ipsative(OP_BLOCKS, PREF_OP, RNG)
likert = {"pond0": 4, "pond1": 2, "pond2": 4, "pond3": 2, "persp0": 4, "persp1": 4, "persp2": 2}

PLUS_DATA = {"nome": "Cb PM Teste da Silva", "posto": "Cabo", "re": "123.456-7", "opm": "46ºBPM/M", "data": "06/08/2026"}

r = compute_plus_results(struct_answers, percep_answers, know_answers, op_answers, likert)

def pct(v):
    return f"{round(v*100)}%"

def print_header(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)

print_header("RELATÓRIO — AUTOAVALIAÇÃO PLUS")
print(f"Nome: {PLUS_DATA['nome']}  |  Posto: {PLUS_DATA['posto']}  |  RE: {PLUS_DATA['re']}  |  OPM: {PLUS_DATA['opm']}  |  Data: {PLUS_DATA['data']}")

print("\n-- Parte 1: Perfil Estrutural (A·C·R·F) --")
for k in PAT_KEYS:
    pole = PAT_POLES[k]
    v = r["structNorm"][k]
    lean = pole["hi"] if v >= r["structMean"] else pole["lo"]
    print(f"  {k} ({pole['nome']}): {pct(v)}  -> tende a {lean}  [{pole['hi']} <-> {pole['lo']}]")
print(f"  Média do gráfico estrutural: {pct(r['structMean'])}")
print(f"  Arquétipo predominante: {r['arquetipo']}")

print("\n-- Eixos derivados (combinação simples de fatores) --")
for ax in r["axes"]:
    print(f"  {ax['name']:32s} {ax['aLabel']:>24s} {ax['pctA']:3d}% | {ax['pctB']:3d}% {ax['bLabel']:<24s}  => dominante: {ax['dominant']} ({ax['strength']}%)")

print("\n-- Índices --")
print(f"  Spread: {r['spreadLevel']} ({r['spreadPct']}%)")
print(f"  Suporte Estrutural: {r['suporteLevel']} ({r['suportePct']}%)")
print(f"  Conflito: {r['conflito']}")
print(f"  Ponderação: {r['ponderacao']} (média likert {r['pondAvg']:.2f})")
print(f"  Perspectiva: {r['perspectiva']} (média likert {r['perspAvg']:.2f})")

print("\n-- Parte 2: Percepção no Ambiente (A·C·R·F) --")
for k in PAT_KEYS:
    pole = PAT_POLES[k]
    v = r["percepNorm"][k]
    lean = pole["hi"] if v >= r["percepMean"] else pole["lo"]
    print(f"  {k} ({pole['nome']}): {pct(v)}  -> tende a {lean}")
print(f"  Média do gráfico de percepção: {pct(r['percepMean'])}")
print(f"  Mudanças (estrutural -> percepção): {r['mudancas']}  ({r['flips']} eixo(s) mudaram de lado da média)")
print(f"    {PLUS_MUDANCAS_DESC[r['mudancas']]}")
print(f"  Aproveitamento do Potencial: {r['aproveitamento']}  (diff. de energia: {r['energiaDiff']} p.p.)")
print(f"    {PLUS_APROV_DESC[r['aproveitamento']]}")

print("\n-- Parte 4: Perfil de Conhecimento --")
for k in r["knowRank"]:
    print(f"  {CONHECIMENTO[k]['nome']:12s} {pct(r['knowNorm'][k])}")

print("\n-- Parte 5: Perfil Operacional (eixos, 0-10) --")
for a, v in sorted(zip(AXES_ORDER, r["userVec"]), key=lambda x: -x[1]):
    print(f"  {AXES_FULL[a]:24s} {v:4.1f}")

print("\n-- Funções onde tende a render mais (top 3, cruzando com os 12 perfis GU) --")
for i, p in enumerate(r["ranked"][:3]):
    print(f"  {i+1}. {p['code']} — {p['title']}  ({p['pct']}% de aderência)")
    print(f"     Operacional {round(p['opComponent']*100)}% | Temperamento aprox. {round(p['tempComponent']*100)}% | Conhecimento {round(p['knowComponent']*100)}%")
    print(f"     {p['why']}")

plus_json = {
    "kind": "prisma-autoavplus", "version": 1, "plusData": PLUS_DATA,
    "structNorm": r["structNorm"], "percepNorm": r["percepNorm"],
    "axes": [{"name": a["name"], "dominant": a["dominant"], "strength": a["strength"]} for a in r["axes"]],
    "spreadLevel": r["spreadLevel"], "suporteLevel": r["suporteLevel"], "conflito": r["conflito"],
    "ponderacao": r["ponderacao"], "perspectiva": r["perspectiva"],
    "mudancas": r["mudancas"], "aproveitamento": r["aproveitamento"], "arquetipo": r["arquetipo"],
    "knowScore": r["knowNorm"], "knowRank": r["knowRank"], "userVec": r["userVec"],
    "top3": [{"code": p["code"], "title": p["title"], "pct": p["pct"]} for p in r["ranked"][:3]],
}
JSON_PATH = "autoavplus-simulado.json"
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(plus_json, f, ensure_ascii=False, indent=2)
print(f"\n[JSON exportado em: {JSON_PATH}]")

# ============================================================================
# ============================= AVALIAÇÃO DO COMANDO =========================
# ============================================================================
# Porta da FRENTE 2 do index.html — checklists ipsativos (op/postura/liderança),
# método dos 30s, Nine Box automática, sugestão automática de desenvolvimento,
# e o cruzamento com o JSON importado da Autoavaliação (aqui, o PLUS gerado acima).

RANK_ORDER = ["Soldado", "Cabo", "3º Sargento", "2º Sargento/1º Sargento", "Subtenente",
              "Aspirante/2º Tenente", "1º Tenente", "Capitão", "Major", "Tenente-Coronel"]

CHECKLIST_OP = [
    {"label": "Mantém postura e controle emocional",
     "lo": "Perde a compostura ou reage de forma desproporcional sob pressão.",
     "hi": "Mantém-se sereno e no controle mesmo em ocorrências de forte tensão."},
    {"label": "Comunica-se com clareza no rádio",
     "lo": "Transmissões confusas, incompletas ou fora do padrão de procedimento.",
     "hi": "Transmite informação clara, objetiva e no padrão correto, mesmo sob pressão."},
    {"label": "Cumpre exatamente a missão recebida",
     "lo": "Executa de forma diferente do combinado ou ignora parte da missão.",
     "hi": "Executa exatamente o que foi determinado, sem desvios não combinados."},
    {"label": "Mantém atenção situacional",
     "lo": "É pego de surpresa por riscos que já eram perceptíveis no ambiente.",
     "hi": "Antecipa riscos e percebe mudanças no ambiente antes que virem problema."},
    {"label": "Usa corretamente os equipamentos",
     "lo": "Erra o manuseio ou usa o equipamento fora do procedimento padrão.",
     "hi": "Domina o manuseio de todos os equipamentos com segurança e correção."},
    {"label": "Demonstra iniciativa sem quebrar a cadeia de comando",
     "lo": "É passivo demais esperando ordem, ou age por conta própria sem informar o comando.",
     "hi": "Toma iniciativa nos momentos certos, sempre mantendo o comando informado."},
    {"label": "Trabalha em equipe",
     "lo": "Atua de forma isolada, atrapalha ou gera atrito com o restante da guarnição.",
     "hi": "Se integra bem, apoia os colegas e facilita o trabalho conjunto."},
    {"label": "Mantém disciplina e segurança",
     "lo": "Ignora procedimentos de segurança ou normas disciplinares em serviço.",
     "hi": "Segue rigorosamente os protocolos de segurança e disciplina em toda a atuação."},
]
CHECKLIST_POSTURA = [
    {"label": "Pontualidade", "lo": "Chega atrasado ou sai antes do horário com frequência.",
     "hi": "Está sempre no horário, pronto para o início do serviço."},
    {"label": "Uniforme e EPI em ordem", "lo": "Uniforme ou equipamento de proteção incompleto, sujo ou fora do padrão.",
     "hi": "Uniforme e EPI sempre completos, limpos e dentro do padrão."},
    {"label": "Respeito aos superiores e pares", "lo": "Trata superiores ou colegas com grosseria, desrespeito ou insubordinação.",
     "hi": "Trata todos com respeito e mantém boa relação hierárquica e de equipe."},
    {"label": "Organização do material", "lo": "Material pessoal ou da viatura desorganizado, faltando itens ou fora de lugar.",
     "hi": "Mantém material e equipamentos sempre organizados e conferidos."},
    {"label": "Proatividade nas tarefas", "lo": "Só faz o mínimo, espera ser cobrado para executar tarefas de rotina.",
     "hi": "Antecipa tarefas e se oferece para ajudar sem precisar ser cobrado."},
    {"label": "Zelo pelo patrimônio", "lo": "Danifica ou usa mal viatura, armamento ou material da unidade.",
     "hi": "Cuida do patrimônio como se fosse próprio, evitando desgaste evitável."},
    {"label": "Cumprimento das normas", "lo": "Descumpre normas internas com frequência, mesmo após orientação.",
     "hi": "Segue as normas internas de forma consistente, mesmo sem supervisão direta."},
]
CHECKLIST_LID = [
    {"label": "Distribui bem as tarefas", "lo": "Sobrecarrega uns e deixa outros ociosos, ou distribui sem critério.",
     "hi": "Distribui tarefas de forma equilibrada, considerando o perfil de cada um."},
    {"label": "Dá exemplo pessoal", "lo": "Exige da equipe o que ele mesmo não cumpre.",
     "hi": "Faz o que cobra dos outros — a equipe o vê como referência de conduta."},
    {"label": "Mantém a equipe informada", "lo": "Deixa a equipe no escuro sobre decisões ou mudanças que a afetam.",
     "hi": "Comunica decisões e mudanças com clareza e antecedência à equipe."},
    {"label": "Corrige sem humilhar", "lo": "Corrige expondo o subordinado ou de forma agressiva na frente de outros.",
     "hi": "Corrige de forma firme e respeitosa, preservando a dignidade do subordinado."},
    {"label": "Mantém o moral da equipe", "lo": "A equipe se mostra desmotivada ou desgastada sob o comando dele.",
     "hi": "A equipe se mantém motivada e coesa mesmo em momentos difíceis."},
    {"label": "Decide no tempo correto", "lo": "Demora demais para decidir, ou decide de forma precipitada sem necessidade.",
     "hi": "Decide no momento certo, nem cedo nem tarde demais, considerando a situação."},
    {"label": "Assume responsabilidade", "lo": "Transfere a culpa para subordinados ou terceiros diante de um erro da equipe.",
     "hi": "Assume a responsabilidade pelas decisões e resultados da equipe, inclusive falhas."},
]
METHOD_30S = ["Ele fez o que foi mandado", "Ele fez do jeito certo",
              "Ele ajudou a equipe (não atrapalhou)", "Não foi necessário chamar sua atenção"]

NINE_BOX = {
    "Alto|Alto": {"nome": "Top Talent / Futuro líder", "leitura": "Excelente operacional + forte perfil de liderança.",
                  "acao": "Preparar para promoções, desafios maiores e funções de comando."},
    "Alto|Médio": {"nome": "Talento em desenvolvimento", "leitura": "Tem garra e capacidade, mas ainda não entrega no nível máximo.",
                   "acao": "Investir fortemente (mentoria, treinamento, feedback)."},
    "Alto|Baixo": {"nome": "Diamante bruto", "leitura": "Tem potencial, mas está rendendo abaixo do esperado.",
                   "acao": "Investir urgentemente (treinamento, mudança de função, mentoria próxima)."},
    "Médio|Alto": {"nome": "Sólido / Expert", "leitura": "Muito bom no que faz, mas com limite de crescimento.",
                   "acao": "Manter em função estratégica, valorizar, dar reconhecimento."},
    "Médio|Médio": {"nome": "Core / Padrão", "leitura": "Policial médio da tropa.",
                    "acao": "Acompanhar, dar oportunidades proporcionais."},
    "Médio|Baixo": {"nome": "Problema gerenciável", "leitura": "Baixa entrega sem grande perspectiva.",
                    "acao": "Plano de melhoria ou realocação."},
    "Baixo|Alto": {"nome": "Operacional Expert", "leitura": "Excelente executor, mas sem perfil para chefiar.",
                   "acao": "Não colocar em comando de equipe. Manter em função técnica ou operacional de alto impacto."},
    "Baixo|Médio": {"nome": "Questão de atenção", "leitura": "Entrega pouco e tem pouca chance de evoluir.",
                    "acao": "Definir metas claras e prazo. Possível realocação se não melhorar."},
    "Baixo|Baixo": {"nome": "Desalinhado", "leitura": "Não entrega e não demonstra potencial.",
                    "acao": "Realocar de função ou processo de desligamento interno."},
}
PIPELINE = {
    "Soldado": {"para": "Cabo", "mudanca": "Continua executor principal, mas começa a orientar Soldados.",
                "erros": "Querer \"mandar\" sem credibilidade · Centralizar tudo."},
    "Cabo": {"para": "3º Sargento", "mudanca": "Deixa de ser apenas operador e passa a ser responsável por pessoas.",
             "erros": "Continuar como o melhor operacional · Não corrigir subordinados."},
    "3º Sargento": {"para": "2º/1º Sargento", "mudanca": "Continua líder de equipe, mas ganha obrigação de formar outros sargentos.",
                    "erros": "Fazer papel de 3º Sgt · Microgerenciar."},
    "2º Sargento/1º Sargento": {"para": "Subtenente",
                                 "mudanca": "Torna-se referência máxima de liderança entre as praças, responsável por garantir o padrão de comando da fração/subunidade e atuar como elo com os oficiais.",
                                 "erros": "Continuar agindo como Sargento · Resolver ocorrências na mão · Perder o foco estratégico · Desmotivação por \"já ter chegado ao topo\", cair na rotina."},
    "Subtenente": {"para": None, "mudanca": "É o \"Coronel das praças\": seu papel não é mais liderar uma viatura ou equipe específica, mas elevar o nível de todos os líderes à sua volta.",
                   "erros": "Continuar indo pra rua resolver ocorrência como Sargento é desperdiçar o posto."},
    "Aspirante/2º Tenente": {"para": "1º Tenente", "mudanca": "De chefiar fração (equipe) para gerir pessoas (desenvolver subordinados, clima da fração e tomada de decisão).",
                             "erros": "Centralizar todas as decisões · Continuar agindo como Aspirante/2º Ten · Ficar só na operação."},
    "1º Tenente": {"para": "Capitão", "mudanca": "De gerir fração/pelotão para gerir a Companhia (liderar líderes, administrar recursos e processos).",
                   "erros": "Continuar resolvendo problema de pelotão · Entrar na ocorrência · Microgerenciar sargentos."},
    "Capitão": {"para": "Major", "mudanca": "De gestão da Companhia para visão de Batalhão/RMS (planejamento, articulação institucional e resultados sistêmicos).",
                "erros": "Interferir na rotina operacional · Decidir como Capitão · Focar excessivamente em detalhes."},
    "Major": {"para": "Tenente-Coronel", "mudanca": "De comando tático para comando estratégico (gestão de grandes unidades, políticas e visão de longo prazo).",
              "erros": "Continuar atuando como Major · Perder contato com a tropa · Focar apenas no operacional."},
    "Tenente-Coronel": {"para": None, "mudanca": "Comando estratégico de grande unidade.", "erros": ""},
}

TEMPERAMENTOS = {
    "C": {"nome": "Colérico", "disc": "D — Dominância",
          "como": "Decidido, rápido, dominante, objetivo.",
          "rende": "Comando de ocorrência, liderança de equipe, decisões sob pressão, operações táticas.",
          "sofre": "Rotina administrativa detalhista, trabalho repetitivo, excesso de regras.",
          "resumo": "Colérico é o temperamento da ação: decide rápido, assume a frente e não recua diante do difícil. Onde outros hesitam, ele já está executando. O preço dessa velocidade é que a decisão pode sair antes de ouvir todo mundo — e a urgência que o move pode soar como impaciência ou dureza para quem trabalha ao lado dele.",
          "palavras": ["Decidido", "Direto", "Competitivo", "Independente", "Impaciente", "Assertivo"],
          "sugestoes": ["Antes de bater o martelo numa decisão que afeta a equipe, faça uma pergunta a mais do que o instinto pede.",
                        "Peça a alguém de confiança para avisar quando o tom estiver pesado demais — ele raramente percebe sozinho.",
                        "Transforme parte do controle em delegação: escolher o que soltar é tão estratégico quanto decidir sozinho."],
          "gerenciamento": ["Estabeleça metas desafiadoras e dê autonomia real para chegar lá — microgerenciamento o desmotiva rápido.",
                             "Comunique-se em tópicos, não em rodeios; ele decide o que fazer com a informação, não como recebê-la.",
                             "Elogie o resultado, não o esforço — reconhecimento genérico soa vazio para esse perfil.",
                             "Renove o desafio periodicamente; rotina sem meta nova é o caminho mais curto para o desengajamento dele."],
          "alerta": ["Sob pressão, pode tomar decisões unilaterais que deveriam passar pela equipe.",
                     "Tende a ver processo e burocracia como obstáculo, não como proteção — risco em normas de segurança.",
                     "Pode confundir liderança com controle, sufocando a iniciativa de quem está junto."],
          "ambiente": {"preferido": ["Ritmo acelerado", "Autonomia de decisão", "Metas claras e desafiadoras", "Liberdade de ação"],
                       "pressao": "Acelera ainda mais e assume o controle sozinho — o risco é atropelar um consenso que seria necessário."}},
    "S": {"nome": "Sanguíneo", "disc": "I — Influência",
          "como": "Comunicador, articulado, entusiástico.",
          "rende": "Atendimento ao público, instrução, integração da equipe, motivação de tropa.",
          "sofre": "Organização rigorosa, prazos longos, tarefas solitárias.",
          "resumo": "Sanguíneo entra numa sala e muda o clima dela. É o tipo de policial que a comunidade lembra pelo nome, que destrava um clima tenso com uma frase certa. A mesma energia que atrai as pessoas, porém, também dispersa: tarefa que exige silêncio e repetição tende a perder a atenção dele antes da hora.",
          "palavras": ["Extrovertido", "Caloroso", "Convincente", "Otimista", "Espontâneo", "Sociável"],
          "sugestoes": ["Feche o ciclo: pegue uma tarefa administrativa pendente esta semana e leve até o fim, sem pular pra próxima novidade.",
                        "Anote compromissos assim que forem combinados — não confie só na memória para prazos.",
                        "Reserve alguns minutos por plantão sem gente ao redor, só para revisar o que ainda falta fazer."],
          "gerenciamento": ["Reconheça publicamente — é o combustível principal desse perfil, mais até que remuneração ou cargo.",
                             "Combine prazos junto com ele, não apenas comunique; envolvimento aumenta o comprometimento.",
                             "Acompanhe entregas de perto, mas sem parecer fiscalização — enquadre como parceria.",
                             "Use a rede de relacionamento dele a favor da equipe: ele conecta gente como poucos."],
          "alerta": ["Pode assumir mais compromissos do que consegue cumprir no prazo combinado.",
                     "Evita dar feedback duro por medo de desagradar, deixando problemas se arrastarem.",
                     "Em tarefa solitária e repetitiva, o rendimento cai visivelmente."],
          "ambiente": {"preferido": ["Contato constante com pessoas", "Variedade de tarefas", "Reconhecimento visível", "Clima leve de equipe"],
                       "pressao": "Busca apoio verbalizando com a equipe; isolado, tende a se dispersar ainda mais."}},
    "F": {"nome": "Fleumático", "disc": "S — Estabilidade",
          "como": "Calmo, estável, conciliador, paciente.",
          "rende": "ROCAM, viatura em rotina, mediação de conflitos, trabalho em dupla ou equipe.",
          "sofre": "Confronto direto, urgência extrema, pressão alta e constante.",
          "resumo": "Fleumático é o chão firme da equipe: não se abala fácil, não cria clima, e costuma ser o primeiro que os colegas procuram quando algo desanda. Essa estabilidade tem contrapartida — ele evita fricção mesmo quando ela é necessária, e pode carregar insatisfação em silêncio até o ponto de transbordar.",
          "palavras": ["Calmo", "Paciente", "Leal", "Discreto", "Constante", "Conciliador"],
          "sugestoes": ["Treinar dizer \"eu discordo\" no momento da discordância — guardar para depois só aumenta o desgaste.",
                        "Definir uma meta pessoal nova a cada poucos meses; sem estímulo externo, tende a estagnar na zona confortável.",
                        "Praticar decidir com prazo apertado de vez em quando, mesmo sem urgência real, para não travar quando ela aparecer de verdade."],
          "gerenciamento": ["Avise mudanças de plano com antecedência; decisão de última hora o desestabiliza mais que a outros perfis.",
                             "Corrija em particular, nunca na frente do grupo — exposição pública pesa muito para ele.",
                             "Reconheça a consistência dele com a mesma força que se reconhece um resultado espalhafatoso de outros.",
                             "Puxe a opinião dele ativamente em reunião — ele raramente vai se impor sozinho, mesmo discordando."],
          "alerta": ["Evita confronto necessário para não gerar atrito, mesmo quando a situação pede posicionamento.",
                     "Demora para se posicionar em decisões urgentes, o que pode custar tempo em ocorrência.",
                     "Acumula insatisfação sem verbalizar, até atingir um ponto de ruptura difícil de prever."],
          "ambiente": {"preferido": ["Rotina previsível", "Equipe fixa e estável", "Baixo nível de conflito", "Ritmo constante"],
                       "pressao": "Fica mais quieto e estável na superfície, mas pode se fechar por completo se pressionado além do limite."}},
    "M": {"nome": "Melancólico", "disc": "C — Conformidade",
          "como": "Analítico, detalhista, perfeccionista.",
          "rende": "Planejamento operacional (P3/P5), análise de dados, instrução técnica, relatórios.",
          "sofre": "Improviso, pressão caótica, ambientes desorganizados.",
          "resumo": "Melancólico entrega o trabalho mais bem-feito do plantão — o relatório sem furo, o procedimento seguido à risca, o detalhe que ninguém mais notou. O contraponto é a dificuldade de avançar sem ter certeza suficiente: enquanto ele analisa, o relógio corre, e o padrão que impõe a si mesmo pode se voltar contra ele em forma de autocrítica.",
          "palavras": ["Analítico", "Preciso", "Criterioso", "Reservado", "Disciplinado", "Perfeccionista"],
          "sugestoes": ["Estabelecer um prazo-limite pessoal de análise antes de decidir, mesmo sem 100% dos dados.",
                        "Compartilhar o raciocínio ainda parcial com a equipe antes de fechar a conclusão — ganha-se velocidade coletiva.",
                        "Tratar pequenos erros como parte esperada do trabalho operacional, não como falha pessoal."],
          "gerenciamento": ["Explique o porquê por trás da ordem — regra sem lógica visível gera resistência silenciosa dele.",
                             "Dê prazo e dados suficientes antes de cobrar posição; pressioná-lo a improvisar reduz a qualidade da entrega.",
                             "Valorize a exatidão do trabalho entregue, mesmo quando o volume for menor que o de outros.",
                             "Evite mudança de última hora sem explicação — ele precisa reorganizar o raciocínio, não só a agenda."],
          "alerta": ["Pode travar diante de ambiente caótico ou pouco estruturado, perdendo tempo de reação.",
                     "Tende à autocrítica desproporcional diante de erros pequenos.",
                     "Corre risco de isolamento ao mergulhar fundo demais em detalhe técnico, afastando-se da equipe."],
          "ambiente": {"preferido": ["Critérios explícitos", "Tempo hábil para planejar", "Baixo nível de improviso", "Reconhecimento pela qualidade técnica"],
                       "pressao": "Fica mais cauteloso e analítico — pode travar diante de uma decisão que exige dado que ele ainda não tem."}},
}

# Extensão do CONHECIMENTO (Parte 1 já tem nome/alt/cor/risco/uso/exemplo) com o que a
# Avaliação do Comando também usa: resumo, palavras, sugestões, gerenciamento, alerta.
CONHECIMENTO["E"].update({
    "resumo": "O Especialista é quem a unidade chama quando ninguém mais sabe resolver aquele problema específico. Anos de prática concentrada viraram domínio técnico real — mas esse mesmo foco pode se fechar em torno de si, deixando-o menos à vontade fora do próprio terreno.",
    "palavras": ["Técnico", "Profundo", "Preciso", "Meticuloso", "Referência"],
    "sugestoes": ["Aceitar, de vez em quando, uma tarefa fora da própria área de domínio, mesmo que renda menos no curto prazo.",
                  "Praticar traduzir o conhecimento técnico em linguagem simples para quem não é da área.",
                  "Buscar contato regular com outros setores para não perder a visão do todo."],
    "gerenciamento": ["Use-o como referência técnica e formador — instrutor interno, multiplicador de conhecimento.",
                       "Não o desloque constantemente da área de especialização sem necessidade real.",
                       "Reconheça o domínio técnico publicamente; é o que mais motiva esse perfil."],
    "alerta": ["Pode resistir a mudanças que fujam do próprio domínio técnico.",
               "Risco de isolamento e dificuldade de integração com equipes fora da especialidade."],
})
CONHECIMENTO["G"].update({
    "resumo": "O Generalista é quem resolve o que aparece, sem travar esperando o especialista certo. Circula bem entre frentes diferentes e mantém a engrenagem girando — mas a versatilidade tem custo: raramente vai ao fundo de um problema complexo, e pode se sentir perdido quando a situação exige profundidade técnica real.",
    "palavras": ["Versátil", "Adaptável", "Prático", "Resolutivo", "Multitarefa"],
    "sugestoes": ["Escolher uma área recorrente da rotina e ir além do básico nela — uma âncora técnica fortalece o perfil.",
                  "Evitar acumular frentes demais ao mesmo tempo; a qualidade cai quando a atenção se espalha.",
                  "Buscar formação complementar nos temas que mais aparecem no dia a dia."],
    "gerenciamento": ["Use-o para coordenação e integração entre setores — ponto de contato entre áreas diferentes.",
                       "Não exija profundidade técnica extrema onde ela não é o forte dele.",
                       "Varie as tarefas atribuídas; rotina fixa e repetitiva reduz o engajamento desse perfil."],
    "alerta": ["Pode entregar solução superficial diante de um problema realmente complexo.",
               "Risco de dispersão ao assumir frentes demais ao mesmo tempo."],
})
CONHECIMENTO["N"].update({
    "resumo": "O Nexialista enxerga a ligação entre coisas que, à primeira vista, não têm nada a ver — e é por isso que vira o elo entre setores, equipes e projetos que precisam conversar entre si. É um perfil raro e valioso, mas que carrega junto o maior risco de sobrecarga: por conseguir lidar com quase tudo, tende a assumir tudo.",
    "palavras": ["Articulador", "Conector", "Estratégico", "Multifacetado", "Envolvido"],
    "sugestoes": ["Aprender a recusar uma frente nova quando já houver mais de duas em andamento.",
                  "Reservar tempo de descanso real na agenda — o risco de esgotamento é o mais alto entre os três perfis.",
                  "Documentar decisões e combinados por escrito; a quantidade de frentes torna a memória pouco confiável sozinha."],
    "gerenciamento": ["Use-o em projetos que exigem articulação entre equipes ou setores diferentes.",
                       "Fique atento a sinais de sobrecarga e ajude a priorizar quando necessário.",
                       "Dê visibilidade do impacto do trabalho dele no conjunto — ele se motiva por ver o todo, não só a própria tarefa."],
    "alerta": ["Risco real de burnout por acumular frentes demais.",
               "Pode perder o fio de detalhes operacionais do dia a dia enquanto articula o panorama maior."],
})

GERAL_LABELS = ["Muito abaixo do esperado", "Abaixo do esperado", "Dentro do esperado", "Acima do esperado", "Muito acima do esperado"]

def build_fc_rounds(n_items, window):
    w = min(window, n_items)
    if w >= n_items:
        return {"rounds": [list(range(n_items))], "w": 1}
    rounds = [[(start + i) % n_items for i in range(w)] for start in range(n_items)]
    return {"rounds": rounds, "w": w}

OP_FC = build_fc_rounds(len(CHECKLIST_OP), 4)
POSTURA_FC = build_fc_rounds(len(CHECKLIST_POSTURA), 4)
LID_FC = build_fc_rounds(len(CHECKLIST_LID), 4)
M30_FC = build_fc_rounds(len(METHOD_30S), 4)

def fc_simulate(fc, pref, rng, jitter=1.5):
    """pref: list of scores per item index. Returns answers[round] = {most, least} (indices)."""
    answers = []
    for idxs in fc["rounds"]:
        jittered = {i: pref[i] + rng.uniform(-jitter, jitter) for i in idxs}
        most = max(idxs, key=lambda i: jittered[i])
        least = min(idxs, key=lambda i: jittered[i])
        answers.append({"most": most, "least": least})
    return answers

def fc_raw(n_items, fc, answers):
    raw = [0] * n_items
    for a in answers:
        raw[a["most"]] += 2
        raw[a["least"]] -= 1
    return raw

def fc_norm(n_items, fc, answers):
    raw = fc_raw(n_items, fc, answers)
    w = fc["w"]
    return [(v + w) / (3 * w) for v in raw]

def fc_ranked(items, fc, answers, text_of):
    norm = fc_norm(len(items), fc, answers)
    ranked = [{"text": text_of(it), "v": norm[i], "pct": round(norm[i] * 100)} for i, it in enumerate(items)]
    ranked.sort(key=lambda r: -r["pct"])
    return ranked

def geral_norm(v):
    return None if v is None else (v - 1) / 4

def nb_level(v):
    if v is None:
        return None
    return "Baixo" if v < 0.4 else "Médio" if v < 0.7 else "Alto"

def compute_nine_box_auto(geral, comanda_equipe):
    op_n = geral_norm(geral["op"])
    m30_n = geral_norm(geral["m30"])
    postura_n = geral_norm(geral["postura"])
    lid_n = geral_norm(geral["lid"]) if comanda_equipe else None

    desempenho = None
    d_parts = [(v, w) for v, w in [(op_n, 0.65), (m30_n, 0.35)] if v is not None]
    if d_parts:
        w_sum = sum(w for _, w in d_parts)
        desempenho = sum(v * w for v, w in d_parts) / w_sum

    potencial = None
    p_parts = []
    if postura_n is not None:
        p_parts.append((postura_n, 0.4 if (comanda_equipe and lid_n is not None) else 1))
    if comanda_equipe and lid_n is not None:
        p_parts.append((lid_n, 0.6))
    if p_parts:
        w_sum = sum(w for _, w in p_parts)
        potencial = sum(v * w for v, w in p_parts) / w_sum

    return {"desempenho": desempenho, "potencial": potencial, "perf": nb_level(desempenho), "pot": nb_level(potencial)}

def hash_index(s, mod):
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) % 997
    return ((h % mod) + mod) % mod if mod > 0 else 0

def find_weakest_checklist_item(op_answers, postura_answers, lid_answers, comanda_equipe):
    candidates = []
    for norm_v, label in zip(fc_norm(len(CHECKLIST_OP), OP_FC, op_answers), [it["label"] for it in CHECKLIST_OP]):
        candidates.append({"v": norm_v, "label": label, "origem": "checklist operacional"})
    for norm_v, label in zip(fc_norm(len(CHECKLIST_POSTURA), POSTURA_FC, postura_answers), [it["label"] for it in CHECKLIST_POSTURA]):
        candidates.append({"v": norm_v, "label": label, "origem": "checklist de postura"})
    if comanda_equipe:
        for norm_v, label in zip(fc_norm(len(CHECKLIST_LID), LID_FC, lid_answers), [it["label"] for it in CHECKLIST_LID]):
            candidates.append({"v": norm_v, "label": label, "origem": "checklist de liderança"})
    if not candidates:
        return None
    candidates.sort(key=lambda c: c["v"])
    return candidates[0]

def lower_first(s):
    return (s[0].lower() + s[1:]) if s else s

def build_auto_suggestion(t, c, nb, p_step, weakest, cmd_data, cmd_assess, imported_self):
    parts = [t["resumo"]]
    if weakest:
        ti = hash_index(weakest["label"], len(t["alerta"]))
        si = hash_index(weakest["label"] + "·dev", len(t["sugestoes"]))
        parts.append(f'Ponto de atenção prioritário: nos checklists, o item que ficou mais no fundo do ranking foi "{weakest["label"]}" ({weakest["origem"]}). Isso conversa com um risco típico do temperamento {t["nome"]}: {t["alerta"][ti]}')
        parts.append(f'Sugestão de desenvolvimento: {t["sugestoes"][si]}')
    else:
        parts.append(f'Ponto de atenção prioritário (temperamento): {t["alerta"][0]}')
        parts.append(f'Sugestão de desenvolvimento (temperamento): {t["sugestoes"][0]}')

    parts.append(c["resumo"])
    ci = hash_index(weakest["label"] + "·conhec", len(c["alerta"])) if weakest else 0
    parts.append(f'Ponto de atenção prioritário (perfil de conhecimento): {c["alerta"][ci]}')
    parts.append(f'Na Nine Box, está posicionado como {nb["nome"]}: {nb["leitura"]} Ação recomendada: {nb["acao"]}')
    if p_step and p_step.get("para"):
        parts.append(f'Rumo à próxima passagem ({cmd_data["avaliadoPosto"]} → {p_step["para"]}), o foco de desenvolvimento é: {lower_first(p_step["mudanca"])} Erros comuns a evitar nessa transição: {lower_first(p_step["erros"])}')
    elif p_step:
        parts.append(p_step["mudanca"])

    if imported_self and (imported_self.get("selfData") or imported_self.get("plusData")):
        self_temp_key = (imported_self.get("tempRank") or [None])[0]
        if self_temp_key and self_temp_key in TEMPERAMENTOS:
            self_temp_nome = TEMPERAMENTOS[self_temp_key]["nome"]
            if self_temp_key == cmd_assess["temperamento"]:
                parts.append(f"A autoavaliação do próprio policial converge com a observação do comando: ele também se percebe como {self_temp_nome}.")
            else:
                parts.append(f"Divergência de autopercepção: o policial se autoavalia como {self_temp_nome}, enquanto o comando observou {t['nome']} — vale explorar essa diferença na conversa de feedback.")

        self_know_key = (imported_self.get("knowRank") or [None])[0]
        if self_know_key and self_know_key in CONHECIMENTO:
            self_know_nome = CONHECIMENTO[self_know_key]["nome"]
            if self_know_key == cmd_assess["perfil"]:
                parts.append(f"Também há convergência no perfil de uso do conhecimento ({self_know_nome}).")
            else:
                parts.append(f"No perfil de conhecimento há divergência: a autoavaliação aponta {self_know_nome}, o comando observou {c['nome']}.")

        if imported_self.get("top3"):
            top = imported_self["top3"][0]
            parts.append(f"Na autoavaliação, a função de melhor aderência apontada foi {top['code']} — {top['title']} ({top['pct']}% de aderência) — vale considerar isso ao decidir sobre a função atual.")

        if imported_self.get("kind") == "prisma-autoavplus":
            if imported_self.get("arquetipo"):
                parts.append(f"Autoavaliação PLUS — arquétipo estrutural: {imported_self['arquetipo']}. Spread {imported_self.get('spreadLevel','—')}, Suporte Estrutural {imported_self.get('suporteLevel','—')}, Ponderação {imported_self.get('ponderacao','—')}, Perspectiva {imported_self.get('perspectiva','—')}.")
            if imported_self.get("mudancas"):
                parts.append(f"Mudanças (natural → percepção no ambiente): {imported_self['mudancas']}. Aproveitamento do potencial: {imported_self.get('aproveitamento','—')}.")
            if imported_self.get("conflito") and not imported_self["conflito"].startswith("Sem conflito"):
                parts.append(f"A autoavaliação PLUS aponta um conflito estrutural: {imported_self['conflito']}")
    return parts

# ---- simulação: checklist do avaliador (persona: bom operacional, disciplina fraca) ----
RNG2 = random.Random(7)
PREF_OP_CHK = [7, 7, 7, 7, 6, 7, 6, 1]        # item 7 "Mantém disciplina e segurança" = ponto fraco de propósito
PREF_POSTURA_CHK = [7, 6, 8, 5, 6, 6, 4]
PREF_LID_CHK = [6, 8, 6, 5, 7, 6, 7]
PREF_M30_CHK = [8, 8, 6, 7]

op_chk_answers = fc_simulate(OP_FC, PREF_OP_CHK, RNG2)
postura_chk_answers = fc_simulate(POSTURA_FC, PREF_POSTURA_CHK, RNG2)
lid_chk_answers = fc_simulate(LID_FC, PREF_LID_CHK, RNG2)
m30_chk_answers = fc_simulate(M30_FC, PREF_M30_CHK, RNG2)

CMD_DATA = {"avaliadorNome": "Ten Barbosa", "avaliadorPosto": "1º Tenente", "avaliadorRE": "222.333-4",
            "avaliadoNome": PLUS_DATA["nome"], "avaliadoPosto": "3º Sargento", "avaliadoRE": PLUS_DATA["re"],
            "equipe": "ROCAM 12", "data": "06/08/2026"}
CMD_ASSESS = {"comandaEquipe": True, "temperamento": "M", "perfil": "E", "funcaoAdequada": True,
              "geral": {"op": 4, "postura": 3, "lid": 3, "m30": 4}, "observacoes": "Bom desempenho técnico; falta rigor com EPI/procedimentos de segurança em serviços de rotina."}

# importedSelf = o JSON exportado pela Autoavaliação PLUS simulada acima
with open(JSON_PATH, "r", encoding="utf-8") as f:
    imported_self = json.load(f)

nb = compute_nine_box_auto(CMD_ASSESS["geral"], CMD_ASSESS["comandaEquipe"])
nb_info = NINE_BOX[f"{nb['pot']}|{nb['perf']}"]
p_step = PIPELINE.get(CMD_DATA["avaliadoPosto"])
t = TEMPERAMENTOS[CMD_ASSESS["temperamento"]]
c = CONHECIMENTO[CMD_ASSESS["perfil"]]

op_ranked = fc_ranked(CHECKLIST_OP, OP_FC, op_chk_answers, lambda it: it["label"])
postura_ranked = fc_ranked(CHECKLIST_POSTURA, POSTURA_FC, postura_chk_answers, lambda it: it["label"])
lid_ranked = fc_ranked(CHECKLIST_LID, LID_FC, lid_chk_answers, lambda it: it["label"]) if CMD_ASSESS["comandaEquipe"] else []
m30_ranked = fc_ranked(METHOD_30S, M30_FC, m30_chk_answers, lambda it: it)

falhas_op = len([r for r in op_ranked if r["pct"] < 40])
warn_at_op = -(-len(CHECKLIST_OP) // 3)  # ceil
positivos_m30 = len([r for r in m30_ranked if r["pct"] >= 60])

weakest = find_weakest_checklist_item(op_chk_answers, postura_chk_answers, lid_chk_answers, CMD_ASSESS["comandaEquipe"])
suggestion_parts = build_auto_suggestion(t, c, nb_info, p_step, weakest, CMD_DATA, CMD_ASSESS, imported_self)

print_header("RELATÓRIO — AVALIAÇÃO DO COMANDO (com cruzamento da Autoavaliação PLUS)")
print(f"Avaliado: {CMD_DATA['avaliadoNome']}  |  Posto: {CMD_DATA['avaliadoPosto']}  |  RE: {CMD_DATA['avaliadoRE']}  |  Equipe: {CMD_DATA['equipe']}")
print(f"Avaliador: {CMD_DATA['avaliadorNome']} ({CMD_DATA['avaliadorPosto']})  |  Data: {CMD_DATA['data']}")

print("\n-- Checklist operacional --")
for r in op_ranked:
    print(f"  {r['pct']:3d}%  {r['text']}")
print(f"  -> {falhas_op} item(ns) no fundo do ranking ({'>=' if falhas_op>=warn_at_op else '<'} limiar {warn_at_op}) — {'PROBLEMA COMPORTAMENTAL CLARO' if falhas_op>=warn_at_op else 'sem sinal de problema comportamental claro'}.")
print(f"  Nível geral informado: {CMD_ASSESS['geral']['op']}/5 — {GERAL_LABELS[CMD_ASSESS['geral']['op']-1]}")

print("\n-- Checklist de postura profissional --")
for r in postura_ranked:
    print(f"  {r['pct']:3d}%  {r['text']}")
print(f"  Nível geral informado: {CMD_ASSESS['geral']['postura']}/5 — {GERAL_LABELS[CMD_ASSESS['geral']['postura']-1]}")

if CMD_ASSESS["comandaEquipe"]:
    print("\n-- Checklist de liderança --")
    for r in lid_ranked:
        print(f"  {r['pct']:3d}%  {r['text']}")
    print(f"  Nível geral informado: {CMD_ASSESS['geral']['lid']}/5 — {GERAL_LABELS[CMD_ASSESS['geral']['lid']-1]}")

print("\n-- Método dos 30 segundos --")
for r in m30_ranked:
    print(f"  {r['pct']:3d}%  {r['text']}")
print(f"  -> {positivos_m30}/{len(METHOD_30S)} pontos fortes — {'bom desempenho' if positivos_m30>=-(-len(METHOD_30S)//2) else 'precisa de orientação'}.")
print(f"  Nível geral informado: {CMD_ASSESS['geral']['m30']}/5 — {GERAL_LABELS[CMD_ASSESS['geral']['m30']-1]}")

print(f"\n-- Temperamento observado: {t['nome']} ({t['disc']}) --")
print(f"  Como é: {t['como']}")
print(f"  Onde rende mais: {t['rende']}")
print(f"  Onde mais sofre: {t['sofre']}")

print(f"\n-- Perfil predominante: {CMD_ASSESS['perfil']} — {c['nome']} ({c['alt']}) --")
print(f"  Melhor uso pelo comandante: {c['uso']}")
print(f"  Risco principal: {c['risco']}")

print(f"\n-- Nine Box (calculada automaticamente) --")
print(f"  Desempenho: {nb['perf']}  |  Potencial: {nb['pot']}")
print(f"  {nb_info['nome']} — {nb_info['leitura']}")
print(f"  Ação recomendada: {nb_info['acao']}")

print(f"\n-- Função atual adequada ao perfil: {'Sim' if CMD_ASSESS['funcaoAdequada'] else 'Não'} --")

print(f"\n-- Cruzamento com a autoavaliação importada --")
id_block = imported_self.get("selfData") or imported_self.get("plusData") or {}
print(f"  Arquivo importado: autoavaliação{' PLUS' if imported_self.get('kind')=='prisma-autoavplus' else ''} de {id_block.get('nome','—')} ({id_block.get('data','—')}).")

print("\n-- Sugestão automática de desenvolvimento --")
for p in suggestion_parts:
    print(f"  • {p}")

print(f"\n-- Pipeline de liderança --")
if p_step and p_step.get("para"):
    print(f"  {CMD_DATA['avaliadoPosto']} → {p_step['para']}")
    print(f"  O que muda: {p_step['mudanca']}")
    print(f"  Erros comuns nessa passagem: {p_step['erros']}")

print(f"\n-- Observações do avaliador --")
print(f"  {CMD_ASSESS['observacoes']}")

print("\n" + "=" * 78)

# ============================================================================
# ======================= AVALIAÇÃO DO COMANDO PLUS =========================
# ============================================================================
# Porta da nova seção "AVALIAÇÃO DO COMANDO PLUS" do index.html — perfil estrutural
# OBSERVADO (A/C/R/F, 12 rodadas em 3ª pessoa) em vez de temperamento C/S/F/M escolhido
# manualmente, reaproveitando os mesmos checklists/Nine Box/Pipeline, com orientação de
# liderança (buildPatGuidance) e comparação direta contra o .json da Autoavaliação PLUS.

PAT_STRUCT_OBS_BLOCKS = [
    block("Numa ocorrência nova, sem procedimento claro definido, o que mais e o que menos representa esse policial:",
          A="Decide na hora, confiando no instinto, mesmo sem ter todos os dados.",
          C="Aciona a equipe pelo rádio e resolve junto, conversando enquanto age.",
          R="Espera alguns segundos a mais, deixando a situação se definir antes de agir.",
          F="Busca o procedimento ou protocolo mais parecido antes de agir."),
    block("Ao assumir uma viatura ou equipe nova, o que mais e o que menos representa esse policial:",
          A="Já vai testando o próprio jeito de trabalhar, sem esperar todo mundo se ajustar.",
          C="Conversa bastante nos primeiros dias pra criar entrosamento rápido.",
          R="Prefere observar o ritmo da equipe por um tempo antes de mudar qualquer coisa.",
          F="Pergunta logo quais são as regras e rotinas já estabelecidas."),
    block("Diante de uma tarefa administrativa chata mas necessária, o que mais e o que menos representa esse policial:",
          A="Faz rápido, do próprio jeito, mesmo que não siga o passo a passo à risca.",
          C="Prefere fazer conversando com alguém por perto.",
          R="Faz com calma, sem pressa, no próprio tempo.",
          F="Segue o modelo/formulário certinho, do jeito que deve ser feito."),
    block("Quando um colega discorda da forma dele agir numa ocorrência, o que mais e o que menos representa esse policial:",
          A="Defende a posição com firmeza, sem duvidar muito de si mesmo.",
          C="Prefere conversar bastante até entenderem o lado um do outro.",
          R="Deixa o assunto esfriar antes de continuar a conversa.",
          F="Busca o que está escrito no procedimento pra resolver a divergência."),
    block("No planejamento de uma ação com prazo curto, o que mais e o que menos representa esse policial:",
          A="Prefere agir logo e ajustar o plano no caminho.",
          C="Prefere alinhar verbalmente com todo mundo antes de sair.",
          R="Prefere esperar mais informação antes de definir qualquer coisa.",
          F="Prefere montar uma checklist antes de sair, mesmo com o tempo curto."),
    block("Numa reunião de passagem de serviço, o que mais e o que menos representa esse policial:",
          A="Vai direto ao ponto, sem enrolar em detalhes.",
          C="Gosta de comentar e trocar impressões, não só passar a informação seca.",
          R="Deixa quem está mais afobado falar primeiro, e entra com calma.",
          F="Segue a ordem e o formato padrão de passagem, sem pular etapas."),
    block("Quando percebe um erro num relatório ou procedimento de outro colega, o que mais e o que menos representa esse policial:",
          A="Aponta na hora, direto, sem rodeio.",
          C="Comenta com jeito, numa conversa, pra não constranger.",
          R="Deixa pra falar num momento mais tranquilo, sem pressa.",
          F="Registra formalmente / segue o canal correto para reportar."),
    block("Ao encarar uma mudança de escala ou rotina de última hora, o que mais e o que menos representa esse policial:",
          A="Se adapta na hora, sem muito questionamento.",
          C="Precisa conversar sobre o motivo da mudança pra se sentir bem com ela.",
          R="Precisa de um tempo pra se ajustar mentalmente à mudança.",
          F="Fica incomodado quando a mudança quebra uma rotina já organizada."),
    block("No meio de uma abordagem que está indo bem, o que mais e o que menos representa esse policial:",
          A="Segue o instinto pra decidir os próximos passos, mesmo fora do script.",
          C="Usa a conversa como principal ferramenta pra manter o controle da situação.",
          R="Mantém o ritmo calmo, sem acelerar desnecessariamente.",
          F="Segue rigorosamente a sequência de segurança do procedimento."),
    block("Ao organizar o material/equipamento de serviço, o que mais e o que menos representa esse policial:",
          A="Não liga muito pra organização, contanto que funcione.",
          C="Gosta de comentar/mostrar como organizou pros colegas.",
          R="Vai arrumando aos poucos, sem se apressar.",
          F="Gosta de tudo no lugar certo, seguindo um padrão fixo."),
    block("Diante de uma ordem que ele não concorda totalmente, o que mais e o que menos representa esse policial:",
          A="Questiona na hora, mesmo sabendo que pode gerar atrito.",
          C="Busca entender conversando com quem deu a ordem.",
          R="Cumpre por ora e só levanta o ponto depois, com calma.",
          F="Cumpre porque é a ordem, mesmo sem concordar totalmente."),
    block("No fim de um plantão puxado, o que mais e o que menos representa esse policial:",
          A="Já pensa na próxima ação/plantão, sem parar muito pra processar o que passou.",
          C="Precisa comentar o plantão com alguém antes de ir embora.",
          R="Precisa de um tempo sozinho pra desacelerar antes de qualquer coisa.",
          F="Revisa e fecha certinho tudo que precisa ser registrado antes de sair."),
]

PAT_GUIDANCE = {
    "A": {
        "hi": {"trait": "Iniciativa alta — decide rápido, assume risco, não espera ordem pra agir.",
               "tips_lead": ["Dê autonomia real e metas claras — microgerenciar essa pessoa gera atrito e desmotivação rápida.",
                              "Aproveite pra colocar em situações que exigem decisão sob pressão — é onde ela rende mais.",
                              "Combine, e não apenas informe, mudanças de plano — envolvimento reduz a resistência."],
               "cuidado": ["Tende a decidir sem consultar a equipe em momentos que pediam consulta — reforce o canal de checagem sem sufocar a autonomia.",
                           "Pode atropelar processo e procedimento por julgar burocracia como obstáculo — reforce o porquê das normas de segurança."]},
        "lo": {"trait": "Cautela e observação altas — prefere checar, confirmar e ir com calma antes de agir.",
               "tips_lead": ["Dê tempo pra essa pessoa se preparar antes de uma ação — decisão de última hora tende a travá-la.",
                              "Reconheça o cuidado e a consistência dela com a mesma força que se reconhece a ousadia de outros perfis.",
                              "Puxe a opinião dela ativamente — dificilmente vai se impor sozinha, mesmo tendo uma leitura boa da situação."],
               "cuidado": ["Pode demorar demais pra agir numa situação que exige resposta imediata — treine cenários de decisão rápida.",
                           "Risco de ficar para trás em ambiente de ritmo acelerado — avalie se a função atual exige mais velocidade do que o perfil confortável."]},
    },
    "C": {
        "hi": {"trait": "Comunicação alta — se energiza falando, pensa em voz alta, gosta de interação constante.",
               "tips_lead": ["Reconheça publicamente — é um dos maiores motivadores pra esse perfil.",
                              "Use a facilidade de comunicação a favor da equipe — ponte entre colegas, integração de gente nova."],
               "cuidado": ["Pode assumir mais compromisso verbal do que consegue entregar no prazo — confirme por escrito o que foi combinado.",
                           "Em tarefa solitária e repetitiva, o rendimento cai — evite escalar essa pessoa pra funções isoladas por muito tempo."]},
        "lo": {"trait": "Reflexão alta — processa por dentro antes de falar, prefere pensar sozinho.",
               "tips_lead": ["Não force exposição em grupo sem preparo prévio — dê o roteiro/pauta com antecedência.",
                              "Valorize contribuições escritas e abra espaço de fala individual, não só em grupo."],
               "cuidado": ["Pode reter informação relevante por não verbalizar espontaneamente — pergunte diretamente, não espere que se ofereça."]},
    },
    "R": {
        "hi": {"trait": "Constância alta (Amanhã Melhor) — pondera, mantém rotina, decide com calma e consistência.",
               "tips_lead": ["Avise mudanças de plano com antecedência — decisão de última hora desestabiliza esse perfil mais que a outros.",
                              "Corrija em particular, nunca na frente do grupo."],
               "cuidado": ["Evita confronto necessário mesmo quando a situação pede posicionamento — puxe a opinião dela ativamente.",
                           "Pode demorar pra se posicionar em decisão urgente — treine cenários de resposta rápida."]},
        "lo": {"trait": "Resposta rápida (Hoje Melhor) — responde de imediato ao estímulo, tolera pouco a espera.",
               "tips_lead": ["Dê tarefas com ação concreta e retorno rápido — rotina lenta e sem retorno visível desmotiva rápido esse perfil.",
                              "Canalize a urgência em prazos desafiadores, não em pressão constante — excesso de pressão vira ansiedade, não produtividade."],
               "cuidado": ["Pode parecer impaciente ou ansioso(a) demais numa situação que exige espera — sinalize quando \"esperar\" é de fato a ação certa."]},
    },
    "F": {
        "hi": {"trait": "Estrutura alta — busca regra, padrão e controle de detalhe, se sente seguro(a) com estrutura clara.",
               "tips_lead": ["Explique o porquê por trás da ordem — regra sem lógica visível gera resistência silenciosa.",
                              "Dê tempo e dados suficientes antes de cobrar decisão em cenário fora do script."],
               "cuidado": ["Pode travar diante de ambiente pouco estruturado ou mudança de última hora — sinalize mudanças com antecedência sempre que possível.",
                           "Risco de autocrítica desproporcional diante de erro pequeno — reforce que erro operacional faz parte do trabalho."]},
        "lo": {"trait": "Flexibilidade alta — delega detalhe, resiste a regra em excesso, se sente sufocado(a) com burocracia.",
               "tips_lead": ["Não sobrecarregue com controle e burocracia desnecessária — foque a régua nos pontos que realmente importam.",
                              "Dê autonomia sobre o método, mantendo claro só o resultado esperado e os pontos não-negociáveis de segurança."],
               "cuidado": ["Pode negligenciar detalhe ou norma que realmente importa (segurança, procedimento formal) — reforce especificamente esses pontos."]},
    },
}

def build_pat_guidance_lead(struct_norm, struct_mean, suporte_level, conflito):
    arch_order = sorted(PAT_KEYS, key=lambda k: -abs(struct_norm[k] - struct_mean))
    items = []
    for k in arch_order[:2]:
        pole = "hi" if struct_norm[k] >= struct_mean else "lo"
        g = PAT_GUIDANCE[k][pole]
        pole_label = PAT_POLES[k]["hi"] if pole == "hi" else PAT_POLES[k]["lo"]
        items.append({"title": f"{PAT_POLES[k]['nome']} — {pole_label}", "trait": g["trait"], "tips": g["tips_lead"], "cuidado": g["cuidado"]})
    notas = []
    if suporte_level in ("Baixo", "Muito Baixo"):
        notas.append("O Suporte Estrutural está baixo — evite empilhar pressão extra nesse momento; monitore sinais de esgotamento.")
    if conflito and not conflito.startswith("Sem conflito"):
        notas.append(f"Foi identificado um conflito estrutural no perfil observado: {conflito}")
    return {"items": items, "notas": notas}

def compute_struct_indices(struct_norm):
    axes = []
    for ax in PAT_AXES:
        va, vb = struct_norm[ax["a"]], struct_norm[ax["b"]]
        total = va + vb
        pct_a = round((va / total) * 100) if total > 0 else 50
        pct_b = 100 - pct_a
        axes.append({**ax, "pctA": pct_a, "pctB": pct_b, "dominant": ax["aLabel"] if pct_a >= pct_b else ax["bLabel"], "strength": max(pct_a, pct_b)})
    vals = [struct_norm[k] for k in PAT_KEYS]
    spread_pct = round((max(vals) - min(vals)) * 100)
    spread_level = ("Muito Alto" if spread_pct >= 65 else "Alto" if spread_pct >= 45 else "Médio" if spread_pct >= 22 else "Baixo" if spread_pct >= 10 else "Muito Baixo")
    struct_mean = sum(struct_norm[k] for k in PAT_KEYS) / 4
    suporte_raw = sum(abs(struct_norm[k] - struct_mean) for k in PAT_KEYS)
    suporte_pct = round((suporte_raw / 2) * 100)
    suporte_level = ("Muito Alto" if suporte_pct >= 70 else "Alto" if suporte_pct >= 50 else "Médio" if suporte_pct >= 30 else "Baixo" if suporte_pct >= 15 else "Muito Baixo")
    dA = struct_norm["A"] - struct_mean
    dF = struct_norm["F"] - struct_mean
    conflito = "Sem conflito relevante entre Iniciativa (A) e Estrutura (F)."
    if abs(dA - dF) < 0.08 and abs(dA) > 0.06 and abs(dF) > 0.06 and (dA > 0) == (dF > 0):
        conflito = ("Conflito do lado alto: iniciativa/ousadia (A alto) tensiona com a necessidade de controle e cautela (F alto)."
                    if dA > 0 else "Conflito do lado baixo: a acomodação (A baixo) tensiona com a resistência a regras (F baixo).")
    arch_order = sorted(PAT_KEYS, key=lambda k: -abs(struct_norm[k] - struct_mean))
    def arch_label(k):
        return PAT_ARCH_LABELS[k]["hi" if struct_norm[k] >= struct_mean else "lo"]
    arquetipo = f"{arch_label(arch_order[0])} + {arch_label(arch_order[1])}"
    return {"axes": axes, "spreadPct": spread_pct, "spreadLevel": spread_level, "suportePct": suporte_pct,
            "suporteLevel": suporte_level, "structMean": struct_mean, "conflito": conflito, "arquetipo": arquetipo}

# ---- simulação: observação do comandante (persona: iniciativa alta, mas MUITO mais formal/estruturado do que a autopercepção) ----
PREF_STRUCT_OBS = {"A": 7, "C": 4, "R": 3, "F": 8}   # o comando enxerga bem mais F (estrutura) do que a pessoa se autoavalia
struct_obs_answers = simulate_ipsative(PAT_STRUCT_OBS_BLOCKS, PREF_STRUCT_OBS, RNG)
struct_norm_obs = norm_ipsative(PAT_STRUCT_OBS_BLOCKS, struct_obs_answers, PAT_KEYS)
idx_obs = compute_struct_indices(struct_norm_obs)
guidance = build_pat_guidance_lead(struct_norm_obs, idx_obs["structMean"], idx_obs["suporteLevel"], idx_obs["conflito"])

CMD_PLUS_DATA = {"avaliadorNome": "Ten Barbosa", "avaliadorPosto": "1º Tenente", "avaliadorRE": "222.333-4",
                  "avaliadoNome": PLUS_DATA["nome"], "avaliadoPosto": "3º Sargento", "avaliadoRE": PLUS_DATA["re"],
                  "equipe": "ROCAM 12", "data": "06/08/2026"}
CMD_PLUS_ASSESS = {"comandaEquipe": True, "perfil": "E", "funcaoAdequada": True,
                    "geral": {"op": 4, "postura": 3, "lid": 3, "m30": 4}}

nb_plus = compute_nine_box_auto(CMD_PLUS_ASSESS["geral"], CMD_PLUS_ASSESS["comandaEquipe"])
nb_plus_info = NINE_BOX[f"{nb_plus['pot']}|{nb_plus['perf']}"]
p_step_plus = PIPELINE.get(CMD_PLUS_DATA["avaliadoPosto"])
c_plus = CONHECIMENTO[CMD_PLUS_ASSESS["perfil"]]

comparison_rows = []
if imported_self.get("structNorm"):
    self_norm = imported_self["structNorm"]
    for k in PAT_KEYS:
        obs_v, self_v = struct_norm_obs[k], self_norm[k]
        comparison_rows.append({"nome": PAT_POLES[k]["nome"], "obsPct": round(obs_v * 100), "selfPct": round(self_v * 100), "diff": round((obs_v - self_v) * 100)})
    max_diff_row = max(comparison_rows, key=lambda r: abs(r["diff"]))

print_header("RELATÓRIO — AVALIAÇÃO DO COMANDO PLUS (nativo A·C·R·F, com comparação direta)")
print(f"Avaliado: {CMD_PLUS_DATA['avaliadoNome']}  |  Posto: {CMD_PLUS_DATA['avaliadoPosto']}  |  Equipe: {CMD_PLUS_DATA['equipe']}")
print(f"Avaliador: {CMD_PLUS_DATA['avaliadorNome']} ({CMD_PLUS_DATA['avaliadorPosto']})  |  Data: {CMD_PLUS_DATA['data']}")

print("\n-- Perfil estrutural OBSERVADO (A·C·R·F) --")
for k in PAT_KEYS:
    pole = PAT_POLES[k]
    v = struct_norm_obs[k]
    lean = pole["hi"] if v >= idx_obs["structMean"] else pole["lo"]
    print(f"  {k} ({pole['nome']}): {pct(v)}  -> observado como {lean}")
print(f"  Arquétipo predominante: {idx_obs['arquetipo']}")

print("\n-- Eixos derivados --")
for ax in idx_obs["axes"]:
    print(f"  {ax['name']:32s} {ax['aLabel']:>24s} {ax['pctA']:3d}% | {ax['pctB']:3d}% {ax['bLabel']:<24s}  => {ax['dominant']} ({ax['strength']}%)")

print("\n-- Índices --")
print(f"  Spread: {idx_obs['spreadLevel']} ({idx_obs['spreadPct']}%)")
print(f"  Suporte Estrutural: {idx_obs['suporteLevel']} ({idx_obs['suportePct']}%)")
print(f"  Conflito: {idx_obs['conflito']}")

if comparison_rows:
    print("\n-- Comparação direta com a Autoavaliação PLUS importada (sem aproximação) --")
    for row in comparison_rows:
        flag = "OK" if abs(row["diff"]) <= 15 else "ATENÇÃO" if abs(row["diff"]) <= 30 else "DIVERGÊNCIA FORTE"
        print(f"  {row['nome']:24s} Comando {row['obsPct']:3d}%  |  Autoavaliação {row['selfPct']:3d}%  (Δ{row['diff']:+d}pp)  [{flag}]")
    print(f"  -> Maior divergência: {max_diff_row['nome']} (Δ{max_diff_row['diff']:+d}pp)")

print("\n-- Como liderar essa pessoa --")
for it in guidance["items"]:
    print(f"\n  * {it['title']} — {it['trait']}")
    print("    Como liderar:")
    for tip in it["tips"]:
        print(f"      - {tip}")
    print("    Ponto de atenção:")
    for cu in it["cuidado"]:
        print(f"      - {cu}")
if guidance["notas"]:
    print("\n  Outros pontos a observar:")
    for nt in guidance["notas"]:
        print(f"    - {nt}")

print(f"\n-- Perfil de conhecimento (manual): {CMD_PLUS_ASSESS['perfil']} — {c_plus['nome']} ({c_plus['alt']}) --")
print(f"\n-- Nine Box: Desempenho {nb_plus['perf']} | Potencial {nb_plus['pot']} -> {nb_plus_info['nome']} --")
print(f"  {nb_plus_info['leitura']}  Ação: {nb_plus_info['acao']}")
if p_step_plus and p_step_plus.get("para"):
    print(f"\n-- Pipeline: {CMD_PLUS_DATA['avaliadoPosto']} → {p_step_plus['para']} --")
    print(f"  {p_step_plus['mudanca']}")

print("\n" + "=" * 78)
