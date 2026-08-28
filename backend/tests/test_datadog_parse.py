"""Parser das mensagens do Datadog On-Call — fixtures copiadas do #datadog-redes (28/08/2026)."""

from app.corvo.datadog import (
    attachment_text,
    extract_dc,
    is_handover,
    normalize_dc,
    parse_datadog_page,
    parse_handover,
)

AUTO = {
    "user": "U07Q4UQU0GM",
    "bot_id": "B07PT8LLSUX",
    "ts": "1787891648.678409",
    "attachments": [
        {
            "title": "Page #52488: LEAF1001TESP03 Interface Ethernet1/21 on cherwellincidentid:21714051",  # noqa: E501
            "title_link": "https://app.datadoghq.com/on-call/pages/52488",
            "text": (
                "*Status:*\n:white_check_mark: Resolved\n*Urgency:*\nHigh\n*Team:*\nInfraOPS Redes\n"  # noqa: E501
                "*Responder:*\n<@U08D079PFST>\n*Description:*\n"
                "- Servidor: LEAF1001TESP03\n- Evento: Interface Ethernet1/21\n"
                "- Descrição: [NSX-EDGE-NODE06 - fp-eth1, Ethernet1/21], (up), Speed: 10 GBit/s, "
                "Out: 9.07 GBit/s (warn/crit at 8 GBit/s/9 GBit/s) (90.74%)(!!)\n"
                "- INC: 21714051\n- Status: error\n- Origem: checkmk_redes\n- Team: infra_redes\n\n"
                "@oncall-infraops-redes\n\nThe monitor was last triggered at Fri Aug 28 2026 04:32:36 UTC.\n\n"  # noqa: E501
                "- - -\n\n<https://app.datadoghq.com/monitors/162116916?group=cherwellincidentid%3A21714051"
                "&from_ts=1787890656000&to_ts=1787891856000&event_id=8785033160175833885|[Monitor Status>]"  # noqa: E501
            ),
        }
    ],
}

FLOAT_IP = {
    "bot_id": "B07PT8LLSUX",
    "ts": "1787876320.588999",
    "attachments": [
        {
            "title": "Page #52477: Alertas de InfraOPS Redes Float IP - CHECK_FLOATING 21712865",
            "title_link": "https://app.datadoghq.com/on-call/pages/52477",
            "text": (
                "*Status:*\nTriggered\n*Urgency:*\nLow\n*Team:*\nTeam Float IP\n*Description:*\n"
                "Status: *error*\n\n- Origem: checkmk_tesp3_float\n- Servidor: tesp3cmk1p00004-floating\n"  # noqa: E501
                "- Evento: CHECK_FLOATING\n- Descrição: Diversos IPs de float do Cluster_4_TESP3 "
                "apresentando alta latência: Sucesso:3894 Falha:43 Hosts_Alta_Latência:509(!!)\n"
                "- INC: 21712865\n- Team: infra_redes\n\n@oncall-team-float-ip"
            ),
        }
    ],
}

MANUAL = {
    "bot_id": "B07PT8LLSUX",
    "ts": "1787880626.314969",
    "attachments": [
        {
            "title": "Page #52481: Acionamento para InfraOPS Redes (Incidente: INC13450)",
            "title_link": "https://app.datadoghq.com/on-call/pages/52481",
            "text": (
                "*Status:*\nAcknowledged\n*Urgency:*\nHigh\n*Team:*\nInfraOPS Redes\n*Responder:*\n"
                "<@U08D079PFST>\n*Description:*\nIncidente: INC13450\n\nJustificativa: Boa noite\n"
                "Estamos com intermitência no firewall do cliente GAFOR-SA, precisamos de apoio. "
                "estamos na sala WR: <https://meet.google.com/zyp-vqwt-ryp>\n\n"
                "(Acionamento solicitado por: diego.alima)"
            ),
        }
    ],
}

HANDOVER = {
    "bot_id": "B07PT8LLSUX",
    "ts": "1787864411.674799",
    "text": (
        ":arrows_counterclockwise: Handover Summary\n"
        "<https://app.datadoghq.com/on-call/schedules/ce1e9e5e|Plantao Redes Interna>: (Empty) "
        ":arrow_right: <@U08D079PFST|Junovan Fantin>\n"
        "<https://app.datadoghq.com/on-call/schedules/7ed99642|Plantao Redes Externa>: "
        "<@U0716KT4HG8|Davi Rovare> :arrow_right: <@U053RFRVBE1|Max Ferreira>"
    ),
}

BLOCKS_VARIANT = {
    "bot_id": "B07PT8LLSUX",
    "ts": "1787887868.467889",
    "attachments": [
        {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<https://app.datadoghq.com/on-call/pages/52486|Page #52486: "
                        "monitoring-redes-1-tece01 CHECK PALO ALTO FW01TECE01_FW02TECE01 CPU DATAPLANE "  # noqa: E501
                        "on cherwellincidentid:21713741>",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Status:*\n:white_check_mark: Resolved"},
                        {"type": "mrkdwn", "text": "*Urgency:*\nHigh"},
                        {"type": "mrkdwn", "text": "*Team:*\nInfraOPS Redes"},
                        {"type": "mrkdwn", "text": "*Responder:*\n<@U053RFRVBE1>"},
                    ],
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_list",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [
                                        {
                                            "type": "text",
                                            "text": "Servidor: monitoring-redes-1-tece01",
                                        }
                                    ],
                                },
                                {
                                    "type": "rich_text_section",
                                    "elements": [
                                        {
                                            "type": "text",
                                            "text": "Evento: CHECK PALO ALTO FW01TECE01_FW02TECE01 CPU DATAPLANE",  # noqa: E501
                                        }
                                    ],
                                },
                                {
                                    "type": "rich_text_section",
                                    "elements": [{"type": "text", "text": "INC: 21713741"}],
                                },
                            ],
                        }
                    ],
                },
            ]
        }
    ],
}


def test_page_auto_completa():
    p = parse_datadog_page(attachment_text(AUTO))
    assert p["page_id"] == 52488
    assert p["page_url"] == "https://app.datadoghq.com/on-call/pages/52488"
    assert p["title"] == "LEAF1001TESP03 Interface Ethernet1/21"
    assert p["kind"] == "auto"
    assert p["status"] == "Resolved"
    assert p["urgency"] == "High"
    assert p["team"] == "InfraOPS Redes"
    assert p["responder"] == "U08D079PFST"
    assert p["servidor"] == "LEAF1001TESP03"
    assert p["evento"] == "Interface Ethernet1/21"
    assert p["descricao"].startswith("[NSX-EDGE-NODE06")
    assert p["inc"] == "21714051"
    assert p["origem"] == "checkmk_redes"
    assert p["team_tag"] == "infra_redes"
    assert p["monitor_id"] == "162116916"
    assert p["monitor_group"] == "cherwellincidentid:21714051"
    assert p["last_triggered_at"] == "2026-08-28T04:32:36+00:00"
    assert p["dc"] == "TESP03"
    assert p["requested_by"] is None


def test_page_team_float_ip_sem_responder():
    p = parse_datadog_page(attachment_text(FLOAT_IP))
    assert p["page_id"] == 52477
    assert p["status"] == "Triggered"
    assert p["urgency"] == "Low"
    assert p["team"] == "Team Float IP"
    assert p["responder"] is None
    assert p["servidor"] == "tesp3cmk1p00004-floating"
    assert p["evento"] == "CHECK_FLOATING"
    assert p["inc"] == "21712865"
    assert p["origem"] == "checkmk_tesp3_float"
    assert p["dc"] == "TESP03"
    assert p["monitor_id"] is None


def test_page_acionamento_manual():
    p = parse_datadog_page(attachment_text(MANUAL))
    assert p["page_id"] == 52481
    assert p["kind"] == "manual"
    assert p["status"] == "Acknowledged"
    assert p["inc"] == "INC13450"
    assert p["requested_by"] == "diego.alima"
    assert p["justificativa"].startswith("Boa noite\nEstamos com intermitência")
    assert p["servidor"] is None
    assert p["dc"] is None


def test_page_em_blocks_dentro_do_attachment():
    p = parse_datadog_page(attachment_text(BLOCKS_VARIANT))
    assert p["page_id"] == 52486
    assert p["title"].startswith("monitoring-redes-1-tece01 CHECK PALO ALTO")
    assert p["status"] == "Resolved"
    assert p["responder"] == "U053RFRVBE1"
    assert p["servidor"] == "monitoring-redes-1-tece01"
    assert p["inc"] == "21713741"
    assert p["dc"] == "TECE01"


def test_mensagem_sem_page_retorna_none():
    assert parse_datadog_page(attachment_text(HANDOVER)) is None
    assert parse_datadog_page("Analisando") is None


def test_handover():
    blob = attachment_text(HANDOVER)
    assert is_handover(blob)
    h = parse_handover(blob)
    assert h["schedules"] == {"Interna": "U08D079PFST", "Externa": "U053RFRVBE1"}
    assert h["names"]["U053RFRVBE1"] == "Max Ferreira"
    assert parse_handover("nada a ver") is None


def test_handover_schedule_vazio():
    blob = ":arrows_counterclockwise: Handover Summary\n<u|Plantao Redes Interna>: <@U1|A> :arrow_right: (Empty)"  # noqa: E501
    assert parse_handover(blob)["schedules"] == {"Interna": None}


def test_extract_dc():
    assert extract_dc("LEAF1001TESP03") == "TESP03"
    assert extract_dc("FW01TECE01") == "TECE01"
    assert extract_dc("tesp3cmk1p00004-floating") == "TESP03"
    assert extract_dc("monitoring-redes-1-tece01") == "TECE01"
    assert extract_dc("NSX-EDGE-NODE06-TESP6-X") == "TESP06"
    assert extract_dc("srv-generico-01") is None
    assert extract_dc(None) is None


def test_normalize_dc():
    assert normalize_dc("TESP3") == "TESP03"
    assert normalize_dc("tece01") == "TECE01"
    assert normalize_dc("TESP") is None
    assert normalize_dc("") is None


def test_acionamento_com_url_no_lugar_do_inc():
    blob = (
        "Page #51788: Acionamento para InfraOPS Redes (Incidente: https://meet.google.com/fmp-ioiq?hs=1)\n"
        "*Status:*\nResolved\n*Description:*\nIncidente: https://meet.google.com/fmp-ioiq?hs=1\n"
        "(Acionamento solicitado por: cesar.moreno)"
    )
    p = parse_datadog_page(blob)
    assert p["kind"] == "manual" and p["inc"] is None and p["requested_by"] == "cesar.moreno"
