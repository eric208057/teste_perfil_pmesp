# -*- coding: utf-8 -*-
"""
Gera os PDFs de exemplo (Autoavaliacao PLUS + Avaliacao do Comando/Gestor PLUS) rodando o app
de verdade num Chrome headless via Chrome DevTools Protocol, sem clicar manualmente em cada
rodada do questionario: o estado global do app (plusAnswers, cmdPlusAssess, etc.) e injetado
direto via Runtime.evaluate, pulando pras funcoes que renderizam a tela de resultado, e o
relatorio final e exportado com Page.printToPDF (que aplica @media print de verdade).

Uso:
  pip install websocket-client
  python generate_pdf_via_cdp.py --variant civil   # index_civil.html
  python generate_pdf_via_cdp.py --variant pm       # index.html (PMESP)

Requer Chrome instalado em CHROME_PATH abaixo (ajustar se necessario).
Ver CLAUDE.md (raiz do repo) para o porque de cada detalhe (beforeprint, printBackground,
--remote-allow-origins, etc.).
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

import websocket  # pip install websocket-client

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 9333

VARIANTS = {
    "civil": {
        "html": "index_civil.html",
        "posto_self": "Sênior",
        "posto_avaliado": "Sênior",
        "self_fields": {
            "plusNome": "Ana Paula Ferreira",
            "plusRE": "123.456.789-00",
            "plusOPM": "Comercial",
            "plusData_": "11/08/2026",
        },
        "cmd_fields": {
            "cmdPlusAvaliadorNome": "Marcos Andrade",
            "cmdPlusAvaliadorPosto": "Gerente Comercial",
            "cmdPlusAvaliadorRE": "987.654.321-00",
            "cmdPlusAvaliadoNome": "Ana Paula Ferreira",
            "cmdPlusAvaliadoRE": "123.456.789-00",
            "cmdPlusEquipe": "Comercial - Time Norte",
            "cmdPlusDataCampo": "11/08/2026",
        },
    },
    "pm": {
        "html": "index.html",
        "posto_self": "Cabo",
        "posto_avaliado": "Cabo",
        "self_fields": {
            "plusNome": "Cb PM Ferreira",
            "plusRE": "123.456-7",
            "plusOPM": "46ºBPM/M",
            "plusData_": "11/08/2026",
        },
        "cmd_fields": {
            "cmdPlusAvaliadorNome": "3º Sgt PM Andrade",
            "cmdPlusAvaliadorPosto": "3º Sargento",
            "cmdPlusAvaliadorRE": "987.654-3",
            "cmdPlusAvaliadoNome": "Cb PM Ferreira",
            "cmdPlusAvaliadoRE": "123.456-7",
            "cmdPlusEquipe": "ROCAM 12",
            "cmdPlusDataCampo": "11/08/2026",
        },
    },
}

# Personas ipsativas (mesmos valores usados no simulate_prisma.py, pra consistencia entre as
# duas ferramentas de QA) -- so preferencia relativa entre A/C/R/F, nao pontuacao absoluta.
PREF_STRUCT = {"A": 9, "C": 7, "R": 2, "F": 1}
PREF_PERCEP = {"A": 3, "C": 5, "R": 4, "F": 9}
PREF_KNOW = {"E": 8, "G": 3, "N": 2}
PREF_OP = {"FIS": 8, "TIR": 9, "ABR": 8, "COM": 3, "JUR": 2, "DIR": 6, "SOC": 3, "LID": 4}
PREF_OBS = {"A": 6, "C": 8, "R": 3, "F": 3}
FC_SCORES = {
    "op": [8, 7, 6, 7, 3, 8, 7, 8],
    "postura": [8, 7, 8, 7, 6, 8, 7],
    "lid": [7, 8, 6, 7, 7, 6, 8],
    "m30": [8, 7, 8, 8],
}


def wait_devtools(port, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def new_tab(port):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/json/new?about:blank", method="PUT")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


class CDP:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=30)
        self._id = 0

    def send(self, method, params=None):
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method} failed: {msg['error']}")
                return msg.get("result", {})

    def wait_event(self, method, timeout=30):
        t0 = time.time()
        while time.time() - t0 < timeout:
            self.ws.settimeout(max(0.1, timeout - (time.time() - t0)))
            try:
                msg = json.loads(self.ws.recv())
            except Exception:
                continue
            if msg.get("method") == method:
                return msg.get("params", {})
        raise TimeoutError(f"timed out waiting for {method}")

    def eval(self, expr):
        r = self.send("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
        if r.get("exceptionDetails"):
            raise RuntimeError(json.dumps(r["exceptionDetails"]))
        return r.get("result", {}).get("value")


def js_set_fields(field_map):
    lines = []
    for fid, val in field_map.items():
        lines.append(f"document.getElementById({json.dumps(fid)}).value = {json.dumps(val)};")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=list(VARIANTS.keys()), default="civil")
    ap.add_argument("--out-dir", default=os.path.join(REPO, "_simulacao"))
    args = ap.parse_args()
    cfg = VARIANTS[args.variant]

    html_path = os.path.join(REPO, cfg["html"])
    file_url = "file:///" + html_path.replace("\\", "/")
    os.makedirs(args.out_dir, exist_ok=True)
    profile_dir = os.path.join(args.out_dir, f"_chrome_profile_{args.variant}")
    os.makedirs(profile_dir, exist_ok=True)

    proc = subprocess.Popen([
        CHROME, "--headless=new", "--disable-gpu",
        f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
        f"--user-data-dir={profile_dir}",
        "--no-first-run", "--no-default-browser-check", "--disable-extensions",
        "--window-size=1400,2000", "about:blank",
    ])
    try:
        if not wait_devtools(PORT):
            print("ERROR: devtools did not come up"); sys.exit(1)

        tab = new_tab(PORT)
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cdp.send("Page.enable")
        cdp.send("Runtime.enable")
        cdp.send("Page.navigate", {"url": file_url})
        cdp.wait_event("Page.loadEventFired")
        time.sleep(0.3)

        self_js = f"""
        (async () => {{
          try {{
            choosePlus();
            {js_set_fields(cfg['self_fields'])}
            const sel = document.getElementById('plusPosto');
            if (!sel.options.length) fillRankSelect(sel);
            sel.value = {json.dumps(cfg['posto_self'])};
            submitPlusData();
            startPlusTest();

            const PREF_STRUCT = {json.dumps(PREF_STRUCT)};
            const PREF_PERCEP = {json.dumps(PREF_PERCEP)};
            const PREF_KNOW = {json.dumps(PREF_KNOW)};
            const PREF_OP = {json.dumps(PREF_OP)};
            function personaFor(front){{
              if(front==='pstruct') return PREF_STRUCT;
              if(front==='ppercep') return PREF_PERCEP;
              if(front==='pknow') return PREF_KNOW;
              return PREF_OP;
            }}
            for (let i = 0; i < PLUS_TOTAL; i++) {{
              const q = PLUS_ALL_QUESTIONS[i];
              const persona = personaFor(q.front);
              const scored = q.keys.map(k => ({{k, v: (persona[k] !== undefined ? persona[k] : 5) + Math.random()*3}}));
              scored.sort((a,b) => b.v - a.v);
              plusAnswers[i] = {{most: scored[0].k, least: scored[scored.length-1].k}};
            }}
            renderPlusLikert();
            showScreen('screen-plus-likert');
            plusLikertAnswers = {{pond0:4,pond1:2,pond2:4,pond3:2,persp0:4,persp1:4,persp2:2}};
            showPlusResults();

            window.__selfPayload = (function(){{
              const r = lastPlusResult;
              return {{
                kind: 'prisma-autoavplus', version: 1, plusData,
                structNorm: r.structNorm, percepNorm: r.percepNorm,
                axes: r.axes.map(a => ({{name:a.name, dominant:a.dominant, strength:a.strength}})),
                spreadLevel: r.spreadLevel, suporteLevel: r.suporteLevel, conflito: r.conflito,
                ponderacao: r.ponderacao, perspectiva: r.perspectiva,
                mudancas: r.mudancas, aproveitamento: r.aproveitamento, arquetipo: r.arquetipo, patProfile: r.patProfile.nome,
                knowScore: r.knowNorm, knowRank: r.knowRank, userVec: r.userVec,
                top3: r.ranked.slice(0,3).map(p => ({{code:p.code, title:p.title, pct:p.pct}})),
              }};
            }})();

            return 'SELF_OK';
          }} catch (e) {{
            return 'SELF_ERR: ' + e.message + '\\n' + e.stack;
          }}
        }})()
        """
        result = cdp.eval(self_js)
        print("PHASE1:", result)
        if result != "SELF_OK":
            raise RuntimeError("Self-assessment phase failed: " + str(result))

        # Real print-media emulation (not a faked 'beforeprint' event) -- this is what makes
        # getComputedStyle() return the print-safe CSS var values inside repaintChartsForMedia(),
        # and the forced reflow it triggers is what the radar/star chart's ResizeObserver needs
        # to redraw the dataset polygons with real (non-zero) canvas dimensions.
        cdp.send("Emulation.setEmulatedMedia", {"media": "print"})
        cdp.eval("if (typeof repaintChartsForMedia === 'function') repaintChartsForMedia(); 'ok';")
        time.sleep(0.3)
        # The print<->screen media switch changes .wrap's max-width, which resizes the chart's
        # canvas -- that resize is handled asynchronously by Chart.js's own ResizeObserver, so a
        # manual update('none') issued right after switching media can race it and get printed
        # mid-transition (dataset polygon points land off their correct axis/value position even
        # though chart.data and the scale's own geometry are both already correct -- verified by
        # comparing actual vs Chart.js's own scale.getPointPositionForValue()). animation:false is
        # now set on the chart itself so any redraw is instant with no tween to be mid-flight of,
        # but resize()+update('none') here is kept as a deterministic belt-and-suspenders settle.
        cdp.eval("if (plusOpChart) { plusOpChart.resize(); plusOpChart.update('none'); } 'ok';")
        time.sleep(0.2)

        pdf = cdp.send("Page.printToPDF", {
            "printBackground": True, "preferCSSPageSize": False,
            "marginTop": 0.4, "marginBottom": 0.4, "marginLeft": 0.4, "marginRight": 0.4, "scale": 1,
        })
        out1 = os.path.join(args.out_dir, f"{args.variant}_autoavaliacao_plus.pdf")
        with open(out1, "wb") as f:
            f.write(base64.b64decode(pdf["data"]))
        print("Saved:", out1)

        cdp.send("Emulation.setEmulatedMedia", {"media": ""})

        cmd_js = f"""
        (async () => {{
          try {{
            goMenu();
            chooseCmdPlus();
            {js_set_fields(cfg['cmd_fields'])}
            const sel2 = document.getElementById('cmdPlusAvaliadoPosto');
            if (!sel2.options.length) fillRankSelect(sel2);
            sel2.value = {json.dumps(cfg['posto_avaliado'])};
            importedSelfPlus = window.__selfPayload || null;
            submitCmdPlusData();
            startCmdPlusStructQuiz();

            const PREF_OBS = {json.dumps(PREF_OBS)};
            for (let i = 0; i < PAT_STRUCT_OBS_BLOCKS.length; i++) {{
              const q = PAT_STRUCT_OBS_BLOCKS[i];
              const scored = q.keys.map(k => ({{k, v: (PREF_OBS[k] !== undefined ? PREF_OBS[k] : 5) + Math.random()*3}}));
              scored.sort((a,b) => b.v - a.v);
              cmdPlusStructAnswers[i] = {{most: scored[0].k, least: scored[scored.length-1].k}};
            }}

            cmdPlusAssess = freshCmdPlusAssess();

            function fillFC(fc, itemScores, arr){{
              fc.rounds.forEach((idxs, r) => {{
                const scored = idxs.map(k => ({{k, v: (itemScores[k] !== undefined ? itemScores[k] : 5) + Math.random()*2}}));
                scored.sort((a,b) => b.v - a.v);
                arr[r] = {{most: scored[0].k, least: scored[scored.length-1].k}};
              }});
            }}
            fillFC(OP_FC, {json.dumps(FC_SCORES['op'])}, cmdPlusAssess.op);
            fillFC(POSTURA_FC, {json.dumps(FC_SCORES['postura'])}, cmdPlusAssess.postura);
            cmdPlusAssess.comandaEquipe = true;
            fillFC(LID_FC, {json.dumps(FC_SCORES['lid'])}, cmdPlusAssess.lid);
            fillFC(M30_FC, {json.dumps(FC_SCORES['m30'])}, cmdPlusAssess.m30);
            cmdPlusAssess.geral = {{op:4, postura:5, lid:4, m30:4}};
            cmdPlusAssess.perfil = 'N';
            cmdPlusAssess.funcaoAdequada = true;
            cmdPlusAssess.observacoes = 'Boa evolucao no periodo; acompanhar de perto o uso correto de equipamentos/ferramentas.';

            showCmdPlusResult();
            return 'CMD_OK';
          }} catch (e) {{
            return 'CMD_ERR: ' + e.message + '\\n' + e.stack;
          }}
        }})()
        """
        result2 = cdp.eval(cmd_js)
        print("PHASE2:", result2)
        if result2 != "CMD_OK":
            raise RuntimeError("Manager-assessment phase failed: " + str(result2))

        cdp.send("Emulation.setEmulatedMedia", {"media": "print"})
        cdp.eval("if (typeof repaintChartsForMedia === 'function') repaintChartsForMedia(); 'ok';")
        time.sleep(0.3)

        pdf2 = cdp.send("Page.printToPDF", {
            "printBackground": True, "preferCSSPageSize": False,
            "marginTop": 0.4, "marginBottom": 0.4, "marginLeft": 0.4, "marginRight": 0.4, "scale": 1,
        })
        out2 = os.path.join(args.out_dir, f"{args.variant}_avaliacao_comando_plus.pdf")
        with open(out2, "wb") as f:
            f.write(base64.b64decode(pdf2["data"]))
        print("Saved:", out2)
    finally:
        try:
            proc.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    main()
