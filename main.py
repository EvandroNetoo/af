import pandas as pd

# Paths to the folders
folders = {
    'petrobras': 'petrobras',
    'prio': 'prio'
}

# Load data
data = {}
for comp, folder in folders.items():
    data[comp] = {
        'ativos': pd.read_csv(f"{folder}/ativos.csv", index_col=0),
        'passivos': pd.read_csv(f"{folder}/passivos.csv", index_col=0),
        'dre': pd.read_csv(f"{folder}/dre.csv", index_col=0)
    }

# Standardize column names to datetime strings and pick the most recent period
for comp, dfs in data.items():
    for key, df in dfs.items():
        # Convert column names to datetime and sort descending
        cols = pd.to_datetime(df.columns, dayfirst=True)
        cols_sorted = sorted(cols, reverse=True)
        df.columns = [dt.strftime('%Y-%m-%d') for dt in cols]
        dfs[key] = df.reindex(columns=[dt.strftime('%Y-%m-%d') for dt in cols_sorted])

# Function to compute indicators for a given company
def compute_indicators(dfs):
    # Use most recent period
    period = dfs['ativos'].columns[0]

    # Extract asset values
    ac = dfs['ativos'].at['Ativo Circulante', period]
    estoque = dfs['ativos'].at['Estoques', period]
    disponivel = dfs['ativos'].at['Caixa e equivalentes de caixa', period]
    aplic_temp = dfs['ativos'].at['Títulos e valores mobiliários', period] if 'Títulos e valores mobiliários' in dfs['ativos'].index else 0
    imobilizado = dfs['ativos'].at['Imobilizado', period]
    intangivel = dfs['ativos'].at['Intangível', period]
    nao_circ = dfs['ativos'].at['Ativo Não Circulante', period]
    realiz_lp = nao_circ - (imobilizado + intangivel)
    at = dfs['ativos'].at['Total do Ativo', period]

    # Extract liability and equity
    pc = dfs['passivos'].at['Total Passivo Circulante', period]
    elp = dfs['passivos'].at['Total Passivo Não Circulante', period]
    pass_tot = pc + elp
    pl_items = [
        'Capital social realizado', 'Reservas de capital', 'Reservas de lucros',
        'Ajuste acumulado de conversão', 'Ajuste de avaliação patrimonial', 'Resultado do período'
    ]
    pl = sum(dfs['passivos'].at[item, period] for item in pl_items if item in dfs['passivos'].index)

    # DRE values
    receita = dfs['dre'].at['Receita líquida (Receita de vendas)', period]
    cpv = abs(dfs['dre'].at['Custo dos produtos e serviços vendidos', period])
    lucro_bruto = dfs['dre'].at['Lucro bruto', period]
    lucro_liquido = dfs['dre'].at['Lucro líquido do período', period]
    ebit = dfs['dre'].at['Resultado operacional antes do resultado financeiro', period]
    desp_fin = abs(dfs['dre'].at['Despesas financeiras', period])
    depr_amort = abs(dfs['dre'].at['Despesa de depreciação e amortização', period])

    # Shares
    lpa = dfs['dre'].at['Lucro por ação - básico', period]
    n_acoes = lucro_liquido / lpa if lpa != 0 else None

    # Calculate ratios
    ratios = {
        'IL Geral': (ac + realiz_lp) / (pc + elp),
        'IL Corrente': ac / pc,
        'IL Seca': (ac - estoque) / pc,
        'IL Imediata': (disponivel + aplic_temp) / pc,
        'Margem Bruta': lucro_bruto / receita,
        'Margem Líquida': lucro_liquido / receita,
        'ROE': lucro_liquido / pl,
        'ROA': lucro_liquido / at,
        'Grau Alav. Financeira (DFL)': (lucro_liquido / pl) / (lucro_liquido / at),
        'I Giro Ativo Total': receita / at,
        'I Giro Ativo Fixo': receita / imobilizado,
        'I Giro Estoques': receita / estoque,
        'I Giro Contas a Receber': receita / dfs['ativos'].at['Contas a receber', period],
        'Giro Estoque (CPV/Estoque)': cpv / estoque,
        'PME (dias)': 365 / (cpv / estoque),
        'PMC (dias)': 365 * dfs['ativos'].at['Contas a receber', period] / receita,
        'I Endividamento': pass_tot / at,
        'I Cobertura Juros': ebit / desp_fin if desp_fin != 0 else None,
        'EBITDA': lucro_liquido + depr_amort
    }

    # Include direct values
    values = {
        'Lucro Bruto': lucro_bruto,
        'Vendas': receita,
        'Lucro Líquido': lucro_liquido,
        'Patrimônio Líquido': pl,
        'Ativo Total': at,
        'Lucro por Ação (básico)': lpa,
        'Lucro dispon. acionistas': lucro_liquido,
        'Nº ações emitidas': n_acoes
    }

    return pd.Series({**ratios, **values})

# Compute for each company and display result
df_indicadores = pd.DataFrame({comp: compute_indicators(dfs) for comp, dfs in data.items()}).T

df_indicadores.to_csv('indicadores_empresas.csv', index=True)
print("Indicadores salvos em 'indicadores_empresas.csv'")
