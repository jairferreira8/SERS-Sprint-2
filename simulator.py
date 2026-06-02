# ChargeGrid Intelligence - Simulador de Energia
# Grupo 05 - Turma 1CCPY - FIAP - EV Challenge 2026 - GoodWe
# Jair Fereira Dos Santos Neto RM 569682
# Matheus da Costa Goncalves RM 570756
# Yan Luiz Neves Lemos RM 571717
# Arthur dos Santos Bezerra RM 569721
# Carlos Henrique Fratezi RM 571792

import numpy as np
import pandas as pd
import random

LIMITE_DEMANDA_KW   = 80.0
GATILHO_REDUCAO     = 0.90
CAPACIDADE_BATERIA  = 50.0
BATERIA_MINIMA      = 5.0
POTENCIA_CARREGADOR = 22.0
MINIMO_CARREGADOR   = 7.0
NUM_CARREGADORES    = 4
TARIFA_PICO         = 0.85
TARIFA_NORMAL       = 0.42
MARGEM_RECARGA      = 0.20
CO2_POR_KWH         = 0.09


def calcular_solar(hora):
    if hora < 6 or hora > 20:
        return 0.0
    geracao_base = 120.0 * np.exp(-0.5 * ((hora - 13.0) / 3.5) ** 2)
    variacao = random.gauss(0, 2.5)
    return max(0.0, geracao_base + variacao)


def calcular_consumo_base(hora):
    consumo = 22.0 + 8.0 * np.sin((hora - 7.0) * np.pi / 11.0)
    variacao = random.gauss(0, 1.2)
    return max(10.0, consumo + variacao)


def horario_pico(hora):
    return 17.0 <= hora < 21.0


def tarifa_atual(hora):
    if horario_pico(hora):
        return TARIFA_PICO
    return TARIFA_NORMAL


def simular_passo(hora, bateria_kwh, carregadores):
    dt = 0.25

    solar_kw   = calcular_solar(hora)
    consumo_kw = calcular_consumo_base(hora)
    threshold  = LIMITE_DEMANDA_KW * GATILHO_REDUCAO

    for c in carregadores:
        c["potencia_kw"] = POTENCIA_CARREGADOR

    ev_kw      = sum(c["potencia_kw"] for c in carregadores if c["ativo"])
    demanda_kw = consumo_kw + ev_kw

    peak_shaving_ativo = False

    if demanda_kw > threshold:
        peak_shaving_ativo = True
        ev_disponivel = threshold - consumo_kw
        ativos = [c for c in carregadores if c["ativo"]]

        if ativos and ev_disponivel > 0:
            potencia_por_carregador = max(MINIMO_CARREGADOR, ev_disponivel / len(ativos))
            for c in ativos:
                c["potencia_kw"] = min(POTENCIA_CARREGADOR, potencia_por_carregador)
        elif ativos:
            for c in ativos:
                c["potencia_kw"] = MINIMO_CARREGADOR

        ev_kw      = sum(c["potencia_kw"] for c in carregadores if c["ativo"])
        demanda_kw = consumo_kw + ev_kw

    delta_bateria      = 0.0
    bateria_contrib_kw = 0.0

    if solar_kw > demanda_kw:
        excedente_kwh  = (solar_kw - demanda_kw) * dt
        espaco_bateria = CAPACIDADE_BATERIA - bateria_kwh
        carregado      = min(excedente_kwh * 0.95, espaco_bateria)
        delta_bateria  = carregado
        bateria_kwh    = min(CAPACIDADE_BATERIA, bateria_kwh + carregado)

    elif horario_pico(hora) and bateria_kwh > BATERIA_MINIMA:
        descarga_kwh       = min(5.0, bateria_kwh - BATERIA_MINIMA)
        delta_bateria      = -descarga_kwh
        bateria_contrib_kw = descarga_kwh / dt
        bateria_kwh        = max(BATERIA_MINIMA, bateria_kwh - descarga_kwh)

    solar_usado_kw = min(solar_kw, demanda_kw)
    rede_kw        = max(0.0, demanda_kw - solar_usado_kw - bateria_contrib_kw)

    for c in carregadores:
        if c["ativo"]:
            c["kwh_sessao"] += c["potencia_kw"] * dt

    autoconsumo_pct = (solar_usado_kw + bateria_contrib_kw) / max(demanda_kw, 0.1) * 100
    co2_evitado_kg  = (solar_usado_kw + bateria_contrib_kw) * dt * CO2_POR_KWH
    tarifa          = tarifa_atual(hora)
    receita_ev      = ev_kw * dt * (tarifa + MARGEM_RECARGA)

    hh = int(hora)
    mm = int((hora % 1) * 60)

    resultado = {
        "hora":           hora,
        "horario":        f"{hh:02d}:{mm:02d}",
        "solar_kw":       round(solar_kw, 2),
        "consumo_kw":     round(consumo_kw, 2),
        "ev_kw":          round(ev_kw, 2),
        "demanda_kw":     round(demanda_kw, 2),
        "solar_usado_kw": round(solar_usado_kw, 2),
        "bateria_contrib":round(bateria_contrib_kw, 2),
        "rede_kw":        round(rede_kw, 2),
        "bateria_kwh":    round(bateria_kwh, 2),
        "bateria_pct":    round(bateria_kwh / CAPACIDADE_BATERIA * 100, 1),
        "peak_shaving":   peak_shaving_ativo,
        "autoconsumo_pct":round(autoconsumo_pct, 1),
        "co2_evitado_kg": round(co2_evitado_kg, 4),
        "receita_r":      round(receita_ev, 2),
        "horario_pico":   horario_pico(hora),
        "tarifa":         round(tarifa, 2),
    }

    return resultado, bateria_kwh


def simular_dia(seed=42):
    random.seed(seed)
    np.random.seed(seed)

    bateria_kwh = 15.0

    carregadores = [
        {
            "id":          f"CHG-0{i+1}",
            "veiculo":     f"EV-{100 + i * 11}",
            "potencia_kw": POTENCIA_CARREGADOR,
            "ativo":       True,
            "kwh_sessao":  0.0,
        }
        for i in range(NUM_CARREGADORES)
    ]

    historico = []

    for hora in np.arange(6.0, 23.0, 0.25):
        resultado, bateria_kwh = simular_passo(hora, bateria_kwh, carregadores)
        historico.append(resultado)

    df = pd.DataFrame(historico)
    return df, carregadores


def calcular_kpis(df):
    dt = 0.25

    solar_kwh   = (df["solar_usado_kw"] * dt).sum()
    bateria_kwh = (df["bateria_contrib"] * dt).sum()
    rede_kwh    = (df["rede_kw"] * dt).sum()
    ev_kwh      = (df["ev_kw"] * dt).sum()
    co2_kg      = df["co2_evitado_kg"].sum()
    receita_r   = df["receita_r"].sum()
    interv_ps   = int(df["peak_shaving"].sum())
    demanda_max = df["demanda_kw"].max()
    total_kwh   = solar_kwh + bateria_kwh + rede_kwh
    autoconsumo = (solar_kwh + bateria_kwh) / max(total_kwh, 0.1) * 100
    multa_evitada = 125.0 if interv_ps > 0 else 0.0

    return {
        "solar_kwh":      round(solar_kwh, 1),
        "bateria_kwh":    round(bateria_kwh, 1),
        "rede_kwh":       round(rede_kwh, 1),
        "ev_kwh":         round(ev_kwh, 1),
        "co2_kg":         round(co2_kg, 2),
        "receita_r":      round(receita_r, 2),
        "interv_ps":      interv_ps,
        "demanda_max_kw": round(demanda_max, 1),
        "autoconsumo_pct":round(autoconsumo, 1),
        "multa_evitada_r":round(multa_evitada, 2),
    }


if __name__ == "__main__":
    print("Testando o simulador ChargeGrid...\n")

    df, carregadores = simular_dia()
    kpis = calcular_kpis(df)

    print(f"{'Horário':<10} {'Solar':>8} {'Bateria':>9} {'Rede':>7} {'EV':>7} {'Demanda':>9} {'PS':>4}")
    print("-" * 60)

    for _, linha in df.iterrows():
        ps = "⚠️" if linha["peak_shaving"] else "  "
        print(
            f"{linha['horario']:<10}"
            f"{linha['solar_kw']:>7.1f}kW"
            f"{linha['bateria_pct']:>8.1f}%"
            f"{linha['rede_kw']:>7.1f}kW"
            f"{linha['ev_kw']:>6.1f}kW"
            f"{linha['demanda_kw']:>7.1f}kW"
            f"  {ps}"
        )

    print("\n── Resumo do dia ──────────────────────")
    print(f"  Solar aproveitado:    {kpis['solar_kwh']} kWh")
    print(f"  Bateria descarregada: {kpis['bateria_kwh']} kWh")
    print(f"  Consumo da rede:      {kpis['rede_kwh']} kWh")
    print(f"  EVs carregados:       {kpis['ev_kwh']} kWh")
    print(f"  CO2 evitado:          {kpis['co2_kg']} kg")
    print(f"  Autoconsumo solar:    {kpis['autoconsumo_pct']}%")
    print(f"  Interv. peak shaving: {kpis['interv_ps']}")
    print(f"  Demanda maxima:       {kpis['demanda_max_kw']} kW (limite: 80 kW)")
    print(f"  Receita de recarga:   R$ {kpis['receita_r']}")
    print(f"  Multa evitada:        R$ {kpis['multa_evitada_r']}")
