from app.corvo.scanner import parse_attachment

SAMPLE = (
    '[{"title": "*Diversos IPs de float do Cluster_2_TESP3 apresentando alta latência*",'
    '"text": ":globe_with_meridians: *Edge:* TESP3\\n:bricks: *Cluster:* Cluster_2\\n'
    ':white_check_mark: *Sucesso:* 5301\\n:x: *Falha:* 128\\n:warning: *Alta Latência:* 369"}]'
)
STORM = SAMPLE.replace("alta latência", "alta latência e perda de pacote").replace("369", "3286")


def test_parse_alert_completo():
    a = parse_attachment(SAMPLE)
    assert a == {
        "edge": "TESP3",
        "cluster": "2",
        "success": 5301,
        "failure": 128,
        "high_latency": 369,
        "packet_loss": False,
        "degraded_pct": 8.6,
        "severity": "warn",
    }


def test_severidade_emergency_por_perda_de_pacote():
    a = parse_attachment(STORM)
    assert a["packet_loss"] is True
    assert a["severity"] == "emergency"


def test_mensagem_irma_sem_campos_retorna_none():
    assert parse_attachment('[{"title": "arquivo floating_result.log"}]') is None
