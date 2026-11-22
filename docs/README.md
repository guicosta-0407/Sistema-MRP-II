# MRP II - Pedal Forte Bicicletas

Sistema de Planejamento dos Recursos de Manufatura (MRP II) em Python, em
modo texto, para a fábrica fictícia **Pedal Forte Bicicletas**. A cada
execução ele responde: o que produzir ou comprar, quanto, quando e se há
capacidade para isso.

Trabalho individual da disciplina de Programação em Python (Engenharia de
Computação, Campus Divinópolis).

## Requisitos

- Python 3.10 ou superior (validado em Linux com Python 3.12)
- matplotlib (somente para os gráficos do RF16)

## Instalação e execução

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Observações:

- Os gráficos abrem em uma janela e também são salvos em PNG. Em Linux, se a
  janela não abrir, instale o suporte gráfico: `sudo apt install python3-tk`.
- Em máquinas sem tela, use `MPLBACKEND=Agg python main.py`: os PNG continuam
  sendo gerados.
- Sem o matplotlib o sistema funciona normalmente; só o menu de gráficos
  informa que a biblioteca precisa ser instalada.
- O sistema grava tudo em `data/`. Para voltar à base de demonstração
  original, use `git checkout data/`.

## Estrutura do projeto

```
MRP2_PedalForte/
├── main.py            ponto de entrada
├── menu.py            menus e navegação
├── itens.py           cadastro de itens (Item, CadastroItens)
├── estrutura.py       BOM e árvore indentada (Estrutura)
├── estoque.py         movimentações, saldo e kardex (Movimento, Estoque)
├── mps.py             plano mestre de produção (PlanoMestre)
├── mrp.py             cálculo MRP (RegistroMRP, CalculoMRP)
├── ordens.py          OPs, OCs e apontamento (Ordem, GerenciadorOrdens)
├── capacidade.py      centros, roteiros e CRP (CentroTrabalho, Capacidade,
│                      CalculoCRP)
├── custos.py          custo padrão (CalculoCustos)
├── relatorios.py      exportação CSV (Relatorios)
├── graficos.py        gráficos de gestão (GraficosGestao)
├── persistencia.py    leitura e gravação de arquivos (Repositorio)
├── utils.py           validações, leitura de entradas e formatação
├── data/              base de demonstração e dados do sistema
│   ├── exportacoes/   CSVs gerados pelo menu 8
│   └── graficos/      PNGs gerados pelo menu 9
└── docs/
    └── README.md
```

## Requisitos funcionais

| Requisito                                        | Onde está             | Como acessar          |
| ------------------------------------------------ | --------------------- | --------------------- |
| RF01 Menu principal                              | `menu.py`             | ao executar `main.py` |
| RF02 Itens (cadastrar, listar, alterar)          | `itens.py`            | 1 → 1                 |
| RF03 BOM em até 3 níveis, com explosão indentada | `estrutura.py`        | 1 → 2                 |
| RF04 Movimentações de estoque                    | `estoque.py`          | 2 → 1                 |
| RF05 Saldo, kardex e alerta de segurança         | `estoque.py`          | 2 → 2 e 2 → 3         |
| RF06 Centros de trabalho e roteiros              | `capacidade.py`       | 1 → 3                 |
| RF07 Plano Mestre de Produção (8 semanas)        | `mps.py`              | 3                     |
| RF08 Cálculo MRP e registro por item             | `mrp.py`              | 4                     |
| RF09 Ordens planejadas (OP e OC)                 | `mrp.py`, `ordens.py` | 4 → 1 e 5             |
| RF10 Firmar, liberar e encerrar ordens           | `ordens.py`           | 5 → 1                 |
| RF11 Apontamento de produção                     | `ordens.py`           | 5 → 1 (opção A)       |
| RF12 Carga x capacidade (CRP)                    | `capacidade.py`       | 6                     |
| RF13 Custo padrão                                | `custos.py`           | 7                     |
| RF14 Exportação em CSV                           | `relatorios.py`       | 8                     |
| RF15 Persistência em `data/`                     | `persistencia.py`     | automática            |
| RF16 Gráficos com matplotlib                     | `graficos.py`         | 9                     |

## Regras de negócio

| Regra                                    | Onde está implementada                                            |
| ---------------------------------------- | ----------------------------------------------------------------- |
| RN01 Código único no formato Tipo-Número | `utils.PADRAO_CODIGO`, `CadastroItens.adicionar`                  |
| RN02 Saldo nunca negativo                | `Estoque.registrar`                                               |
| RN03 Estrutura de no máximo 3 níveis     | `Estrutura.COMPONENTES_PERMITIDOS`, `Estrutura._validar`          |
| RN04 Processamento por tipo (PA, SA, MP) | `CalculoMRP.ORDEM_DE_PROCESSAMENTO`                               |
| RN05 Necessidade líquida                 | `CalculoMRP._calcular`                                            |
| RN06 Recebimento planejado e lote mínimo | `CalculoMRP._calcular`                                            |
| RN07 Liberação, atraso e exceção         | `CalculoMRP._gerar_ordens`, `GerenciadorOrdens.atrasadas`         |
| RN08 Planejadas apagadas e recalculadas  | `GerenciadorOrdens.apagar_planejadas`, `recebimentos_programados` |
| RN09 Carga do centro e sobrecarga        | `CalculoCRP.carga_semanal`                                        |
| RN10 Kardex permanente                   | `Estoque.registrar` (só acréscimo, sem exclusão)                  |

## Decisões de projeto

1. **Orientação a objetos com dois papéis.** Cada módulo tem entidades
   (`Item`, `Movimento`, `Ordem`, `CentroTrabalho`) e gerenciadores
   (`CadastroItens`, `Estoque`, `GerenciadorOrdens`, `Capacidade`) que guardam
   a coleção, aplicam as regras entre registros e falam com o `Repositorio`.
2. **Lógica separada da interface.** Os métodos de negócio nunca imprimem:
   levantam `ValueError` com a causa. Os métodos `*_interativo` leem do
   teclado, chamam a lógica e capturam o erro. O `Menu` ainda tem uma rede de
   segurança para `ValueError` e `ErroPersistencia`.
3. **Validação em duas camadas.** `utils.ler_*` valida o formato da digitação
   (e repete a pergunta); as classes de negócio validam as regras do domínio.
4. **Dados em JSON e CSV.** Cadastros, saldos e planos ficam em JSON. O kardex
   fica em CSV só de acréscimo (`anexar_csv`), o que garante a RN10. A gravação
   de JSON é atômica: escreve em arquivo temporário e troca o original.
5. **Decimal.** Dentro do sistema e nos JSON o separador é o ponto; a vírgula
   existe apenas na tela e no teclado (`ler_decimal` e `formatar_decimal`).
   Os CSVs exportados usam `;` e vírgula decimal, com UTF-8 com BOM, para
   abrir corretamente no Excel em português.
6. **Recursão sobre a BOM.** A explosão (`Estrutura.explodir`) e o custo
   padrão (`CalculoCustos.custo_padrao`) percorrem a estrutura recursivamente.
   A RN03 é uma tabela (`COMPONENTES_PERMITIDOS`); como o pai é sempre de um
   tipo mais alto que o filho (PA > SA > MP), ciclos são impossíveis.
7. **MRP.** Cada item é calculado semana a semana com
   `NL = max(0, NB + ES - (EP anterior + RP))`, recebimento planejado
   `max(NL, lote mínimo)` e liberação na entrega menos o lead time. A
   necessidade bruta dos componentes é a soma das liberações dos pais vezes a
   quantidade por unidade. O cálculo foi conferido contra o mockup 6.4
   (SA-020), linha por linha.
8. **Ordens atrasadas.** Se a liberação cai antes da semana 1, a ordem é
   marcada ATRASADA e gera mensagem de exceção. Nesse caso a ordem aparece com
   a semana real (S0, S-1), mas conta na **semana 1** do registro MRP, da
   necessidade dos componentes e da carga do CRP, porque precisa dos recursos
   imediatamente.
9. **Ordens firmes e liberadas.** Entram como recebimentos programados na
   semana de entrega (RN08). As liberações delas também geram necessidade
   bruta nos componentes, porque os insumos só saem do estoque no apontamento.
   Quando existem, aparecem na linha extra "Liberacao ord. firmes".
10. **Encerrar uma ordem.** Para OP, encerrar é **apontar a produção** (baixa
    os componentes, dá entrada no produzido e encerra). Para OC, encerrar é
    **receber a compra** (entrada da MP no estoque). Ambos registram o
    documento no kardex (`OP-0015 (SA-020)`, `OC-0011 - recebimento`).
11. **Apontamento em duas fases.** O sistema primeiro verifica todos os
    componentes e só então grava. Se faltar algum, rejeita listando todas as
    faltas e nenhum saldo é alterado.
12. **Interpretação da RN09 (CRP).** A carga de uma semana soma
    `quantidade x tempo unitário` das OPs em aberto (planejadas, firmes e
    liberadas) com liberação naquela semana. OPs encerradas não contam.
13. **Custo padrão.** Soma de `quantidade x custo padrão do componente` (MP
    usa o custo cadastrado, SA recalcula recursivamente) mais a mão de obra do
    roteiro do próprio item (`tempo x custo-hora`). A opção 7 → 3 grava o
    resultado no custo dos itens fabricados.
14. **Numeração das ordens.** O próximo número é o maior existente do tipo
    mais 1, respeitando a numeração inicial do `ordens.json`. Como as
    planejadas são apagadas a cada execução, a numeração não cresce
    indefinidamente, e ordens firmes, liberadas ou encerradas nunca perdem o
    número citado no kardex.
15. **Gráficos.** O de estoque usa escala simlog, porque as quantidades vão de
    dezenas a milhares (MP-201). O de ordens conta **ordens** por semana de
    entrega, já que somar quantidades de OP (bicicletas) e de OC (raios,
    litros) misturaria unidades.

## Base de demonstração

| Tipo    | Itens                                                                                 |
| ------- | ------------------------------------------------------------------------------------- |
| PA      | PA-001 Bicicleta Aro 29 MTB, PA-002 Bicicleta Aro 29 Urbana                           |
| SA      | SA-010 Quadro aro 29 soldado, SA-020 Roda aro 29 montada                              |
| MP      | MP-100, MP-101, MP-200, MP-201, MP-202, MP-300, MP-301, MP-302                        |
| Centros | CT-01 Soldagem e pintura, CT-02 Montagem de rodas, CT-03 Montagem final (16 h/semana) |

O kardex do MP-202 reproduz o mockup 6.3 (saldo 18, abaixo da segurança de
20), e o custo padrão do PA-001 fecha em **R$ 792,60**, como no mockup 6.7.

## Roteiro de uso: ciclo completo

1. **Menu 3 → 2:** exibe o plano mestre (demanda de PA-001 e PA-002).
2. **Menu 4 → 1:** executa o MRP. Resultado esperado: 37 ordens planejadas
   (15 OP e 22 OC) e 5 mensagens de exceção.
3. **Menu 4 → 2:** registro MRP de `PA-001`, `SA-020` ou `MP-201`.
4. **Menu 5 → 1:** tente `F` e `L` em uma OP de SA-020 (por exemplo,
   `OP-0015`) e depois `A`. O apontamento é **rejeitado**, pois falta MP-202
   (necessário 80, saldo 18).
5. Ainda no menu 5 → 1: firme (`F`), libere (`L`) e receba (`R`) a compra
   `OC-0011` (MP-202). Depois firme, libere e aponte (`A`) a `OP-0015`.
   Saldos esperados: SA-020 = 120, MP-202 = 38, MP-200 = 70, MP-201 = 120.
6. **Menu 2 → 2:** kardex de MP-202 com a entrada da compra e a saída da OP.
7. **Menu 4 → 1** de novo: as ordens encerradas permanecem, as planejadas são
   recalculadas (RN08).
8. **Menu 6:** carga x capacidade. O CT-03 fica em sobrecarga nas semanas 4, 5
   e 7, com a sugestão de antecipar OPs ou programar hora extra.
9. **Menu 7:** custo padrão do PA-001 (R$ 792,60) e resumo dos fabricados.
10. **Menu 8:** gera `data/exportacoes/posicao_estoque.csv` e
    `data/exportacoes/lista_ordens.csv`.
11. **Menu 9:** gera os quatro gráficos em `data/graficos/`. O de estoque
    projetado exige o MRP executado nesta sessão; os de ordens e de carga
    usam as ordens gravadas.

## Limitações conhecidas

- As semanas 1 a 8 são fixas: o horizonte não "rola" conforme o calendário.
- Roteiro de operação única, sem calendário de turnos nem filas.
- O MRP não arredonda quantidades fracionárias de matéria-prima para
  múltiplos de embalagem (só aplica o lote mínimo).
- O registro MRP existe apenas na sessão em que o MRP foi executado; as
  ordens, essas sim, ficam gravadas.

## Qualidade de código

O projeto segue a PEP 8 (verificado com `flake8`, sem avisos).
