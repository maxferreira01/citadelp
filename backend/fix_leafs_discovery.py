"""Aceita a descoberta (fix_all) nos leafs/spines sem serviço de Interface e ativa por site.

Uso (na dev-redes, com CITADEL_CHECKMK_SITES no ambiente):
    ../.venv/bin/python fix_leafs_discovery.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fallback: herdar CITADEL_CHECKMK_SITES do uvicorn em execução, se não estiver no env.
if "CITADEL_CHECKMK_SITES" not in os.environ:
    import subprocess

    pids = subprocess.run(["pgrep", "-f", "uvicorn"], capture_output=True, text=True).stdout.split()
    for pid in pids:
        try:
            for item in open(f"/proc/{pid}/environ", "rb").read().split(b"\0"):
                if item.startswith(b"CITADEL_CHECKMK_SITES="):
                    os.environ["CITADEL_CHECKMK_SITES"] = item.split(b"=", 1)[1].decode()
                    break
        except OSError:
            continue
        if "CITADEL_CHECKMK_SITES" in os.environ:
            break

from app.checkmk.gateway import CheckmkError, Gateway, load_sites  # noqa: E402

PLAN = {
    "tesp4": [
        "LEAF1003TESP04",
        "LEAF1007TESP04",
        "LEAF1008TESP04",
        "LEAF1009TESP04",
        "LEAF1010TESP04",
        "SPINE102TESP04",
    ],
    "tesp5": [f"LEAF{n}TESP05" for n in range(1026, 1038)],
    "tece1": ["LEAF1022TECE01", "LEAF1023TECE01", "LEAF1024TECE01", "LEAF1025TECE01"],
}


def wait_job(gw: Gateway, host: str, tmo: int = 300) -> str:
    """Termina quando o job reporta finished OU quando a check_table fica estável
    (CMK 2.1 nem sempre atualiza o job)."""
    t0 = time.time()
    last = None
    stable = 0
    while time.time() - t0 < tmo:
        try:
            j = gw._req("GET", f"/objects/service_discovery_run/{host}")["extensions"]
        except CheckmkError as e:
            return f"poll err {e}"
        if j.get("state") in ("finished", "exception", "stopped") and not j.get("active"):
            return j["state"]
        c = counts(gw, host)
        if c and c == last:
            stable += 1
            if stable >= 2:
                return "stable"
        else:
            stable = 0
        last = c
        time.sleep(10)
    return "timeout"


def counts(gw: Gateway, host: str) -> dict:
    ct = gw._req("GET", f"/objects/service_discovery/{host}")["extensions"]["check_table"]
    items = list(ct.values()) if isinstance(ct, dict) else ct
    c: dict = {}
    for i in items:
        c[i.get("value")] = c.get(i.get("value"), 0) + 1
    return c


def main() -> None:
    sites = load_sites()
    only = sys.argv[1:]  # ex.: LEAF1003TESP04 LEAF1007TESP04 (limita o plano)
    for sid, hosts in PLAN.items():
        if only:
            hosts = [h for h in hosts if h in only]
        if not hosts:
            continue
        gw = Gateway(sites[sid], timeout=60)
        ok = 0
        for h in hosts:
            try:
                gw.discover(h, mode="refresh")
                st1 = wait_job(gw, h)
                gw.discover(h, mode="fix_all")
                st2 = wait_job(gw, h)
                c = counts(gw, h)
                ok += st2 == "finished" and not c.get("undecided") and c.get("monitored", 0) > 0
                print(f"[{sid}] {h}: refresh={st1} fix_all={st2} {c}", flush=True)
            except CheckmkError as e:
                print(f"[{sid}] {h}: ERRO {e}", flush=True)
        try:
            r = gw.activate()
            status = r.get("extensions", {}).get("status") or r.get("title") or "ok"
            print(f"[{sid}] activate: {status} ({ok}/{len(hosts)} descobertos)", flush=True)
        except CheckmkError as e:
            print(f"[{sid}] activate ERRO {e}", flush=True)
        gw.close()


if __name__ == "__main__":
    main()
