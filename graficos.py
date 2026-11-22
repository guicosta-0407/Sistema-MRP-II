import utils
from mps import HORIZONTE

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
except ImportError:
    plt = None

PASTA = "graficos"
AZUL = "#2a78b5"
LARANJA = "#e08a1e"
VERMELHO = "#c0392b"
VERDE = "#3a9a5b"


class GraficosGestao:
    def __init__(self, repositorio, cadastro_itens, estoque, mrp, ordens,
                 crp):
        self.repositorio = repositorio
        self.cadastro = cadastro_itens
        self.estoque = estoque
        self.mrp = mrp
        self.ordens = ordens
        self.crp = crp

    @staticmethod
    def _exigir_matplotlib():
        if plt is None:
            raise ValueError(
                "matplotlib nao esta instalado (pip install matplotlib)"
            )

    def _finalizar(self, figura, nome):
        self.repositorio.pasta(PASTA)
        caminho = self.repositorio.caminho(f"{PASTA}/{nome}")
        figura.savefig(caminho, dpi=150, bbox_inches="tight")
        print(f"Grafico salvo em {caminho}")
        plt.show()
        plt.close(figura)

    def posicao_estoque(self):
        self._exigir_matplotlib()
        posicao = self.estoque.posicao()
        if not posicao:
            raise ValueError("nenhum item cadastrado")
        codigos = [item.codigo for item, _ in posicao]
        saldos = [saldo for _, saldo in posicao]
        seguranca = [item.estoque_seguranca for item, _ in posicao]
        cores = [
            VERMELHO if saldo < minimo else AZUL
            for saldo, minimo in zip(saldos, seguranca)
        ]
        indices = list(range(len(codigos)))
        largura = 0.4
        figura, eixo = plt.subplots(figsize=(11, 5.5))
        eixo.bar([i - largura / 2 for i in indices], saldos, largura,
                 color=cores)
        eixo.bar([i + largura / 2 for i in indices], seguranca, largura,
                 color=LARANJA)
        eixo.set_xticks(indices)
        eixo.set_xticklabels(codigos, rotation=45, ha="right")
        eixo.set_yscale("symlog", linthresh=10)
        eixo.set_ylabel("Quantidade (escala simlog)")
        eixo.set_title("Posicao de estoque: saldo atual x estoque de "
                       "seguranca")
        eixo.grid(axis="y", alpha=0.3)
        eixo.legend(handles=[
            Patch(color=AZUL, label="Saldo atual"),
            Patch(color=VERMELHO, label="Saldo abaixo da seguranca"),
            Patch(color=LARANJA, label="Estoque de seguranca"),
        ])
        self._finalizar(figura, "posicao_estoque.png")

    def estoque_projetado(self, codigo):
        self._exigir_matplotlib()
        item = self.cadastro.obter(codigo)
        registro = self.mrp.registros.get(codigo)
        if registro is None:
            raise ValueError("execute o MRP antes de gerar este grafico")
        semanas = list(range(1, HORIZONTE + 1))
        projetado = registro.estoque_projetado
        figura, eixo = plt.subplots(figsize=(9, 5))
        seguranca = utils.formatar_quantidade(item.estoque_seguranca)
        eixo.plot(semanas, projetado, marker="o", color=AZUL,
                  label="Estoque projetado")
        eixo.axhline(item.estoque_seguranca, color=VERMELHO, linestyle="--",
                     label=f"Estoque de seguranca ({seguranca})")
        abaixo = [(s, p) for s, p in zip(semanas, projetado)
                  if p < item.estoque_seguranca]
        if abaixo:
            eixo.scatter([s for s, _ in abaixo], [p for _, p in abaixo],
                         color=VERMELHO, zorder=3,
                         label="Abaixo da seguranca")
        eixo.set_ylim(bottom=min(0, min(projetado)))
        eixo.set_xticks(semanas)
        eixo.set_xlabel("Semana")
        eixo.set_ylabel(f"Quantidade ({item.unidade})")
        eixo.set_title(f"Estoque projetado - {item.codigo} "
                       f"{item.descricao}")
        eixo.grid(alpha=0.3)
        eixo.legend()
        self._finalizar(figura, f"estoque_projetado_{codigo}.png")

    def ordens_por_semana(self):
        self._exigir_matplotlib()
        producao = [0] * HORIZONTE
        compra = [0] * HORIZONTE
        for ordem in self.ordens.listar():
            semana = max(ordem.semana_entrega, 1)
            if semana > HORIZONTE:
                continue
            alvo = producao if ordem.tipo == "OP" else compra
            alvo[semana - 1] += 1
        totais = [p + c for p, c in zip(producao, compra)]
        if not any(totais):
            raise ValueError("nao ha ordens em aberto; execute o MRP")
        semanas = list(range(1, HORIZONTE + 1))
        figura, eixo = plt.subplots(figsize=(9, 5))
        eixo.bar(semanas, producao, color=AZUL,
                 label="Ordens de producao (OP)")
        eixo.bar(semanas, compra, bottom=producao, color=LARANJA,
                 label="Ordens de compra (OC)")
        passo = max(1, max(totais) // 10)
        eixo.set_yticks(range(0, max(totais) + 1, passo))
        eixo.set_xticks(semanas)
        eixo.set_xlabel("Semana de entrega")
        eixo.set_ylabel("Numero de ordens")
        eixo.set_title("Ordens em aberto por semana de entrega")
        eixo.grid(axis="y", alpha=0.3)
        eixo.legend()
        self._finalizar(figura, "ordens_por_semana.png")

    def carga_capacidade(self, codigo_centro):
        self._exigir_matplotlib()
        centro = self.crp.capacidade.obter_centro(codigo_centro)
        carga = self.crp.carga_semanal(codigo_centro)
        semanas = list(range(1, HORIZONTE + 1))
        cores = [
            VERMELHO if horas > centro.capacidade else VERDE
            for horas in carga
        ]
        figura, eixo = plt.subplots(figsize=(9, 5))
        eixo.bar(semanas, carga, color=cores)
        eixo.axhline(centro.capacidade, color="black", linestyle="--")
        for semana, horas in zip(semanas, carga):
            if horas > centro.capacidade:
                eixo.annotate("SOBRECARGA", (semana, horas),
                              ha="center", va="bottom", fontsize=8,
                              color=VERMELHO)
        eixo.set_ylim(top=max(max(carga), centro.capacidade) * 1.2)
        eixo.set_xticks(semanas)
        eixo.set_xlabel("Semana")
        eixo.set_ylabel("Horas")
        eixo.set_title(f"Carga x capacidade - {centro.codigo} "
                       f"{centro.descricao}")
        eixo.grid(axis="y", alpha=0.3)
        eixo.legend(handles=[
            Patch(color=VERDE, label="Dentro da capacidade"),
            Patch(color=VERMELHO, label="Sobrecarga"),
            plt.Line2D([0], [0], color="black", linestyle="--",
                       label="Capacidade ("
                             f"{utils.formatar_decimal(centro.capacidade)}"
                             " h/semana)"),
        ])
        self._finalizar(figura, f"carga_capacidade_{codigo_centro}.png")

    def estoque_projetado_interativo(self):
        codigo = utils.ler_codigo(">> Codigo do item: ")
        self.estoque_projetado(codigo)

    def carga_capacidade_interativo(self):
        self.crp.capacidade.exibir_centros()
        codigo = utils.ler_codigo_centro(">> Codigo do centro: ")
        self.carga_capacidade(codigo)
