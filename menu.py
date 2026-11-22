import utils
from capacidade import CalculoCRP, Capacidade
from custos import CalculoCustos
from estoque import Estoque
from estrutura import Estrutura
from graficos import GraficosGestao
from itens import CadastroItens
from mps import PlanoMestre
from mrp import CalculoMRP
from ordens import GerenciadorOrdens
from persistencia import ErroPersistencia
from relatorios import Relatorios

LARGURA = 50


class Menu:
    def __init__(self, repositorio):
        self.itens = CadastroItens(repositorio)
        self.estrutura = Estrutura(repositorio, self.itens)
        self.estoque = Estoque(repositorio, self.itens)
        self.capacidade = Capacidade(repositorio, self.itens)
        self.mps = PlanoMestre(repositorio, self.itens)
        self.ordens = GerenciadorOrdens(
            repositorio, self.itens, self.estrutura, self.estoque
        )
        self.mrp = CalculoMRP(
            self.itens, self.estrutura, self.estoque, self.mps, self.ordens
        )
        self.crp = CalculoCRP(self.capacidade, self.ordens)
        self.custos = CalculoCustos(
            self.itens, self.estrutura, self.capacidade
        )
        self.relatorios = Relatorios(
            repositorio, self.itens, self.estoque, self.ordens
        )
        self.graficos = GraficosGestao(
            repositorio, self.itens, self.estoque, self.mrp, self.ordens,
            self.crp,
        )

    @staticmethod
    def _cabecalho(titulo):
        print("=" * LARGURA)
        print(titulo)
        print("=" * LARGURA)

    @staticmethod
    def _executar(acao):
        try:
            acao()
        except (ValueError, ErroPersistencia) as erro:
            print(f"ERRO: {erro}.")

    def _submenu(self, titulo, acoes):
        while True:
            self._cabecalho(titulo)
            for chave, (nome, _) in acoes.items():
                print(f"{chave}. {nome}")
            print("0. Voltar")
            print("-" * LARGURA)
            opcao = utils.ler_opcao("Escolha uma opcao: ", [*acoes, "0"])
            if opcao == "0":
                return
            self._executar(acoes[opcao][1])

    def principal(self):
        destinos = {
            "1": self.cadastros,
            "2": self.submenu_estoque,
            "3": self.submenu_mps,
            "4": self.submenu_mrp,
            "5": self.submenu_ordens,
            "6": self.submenu_crp,
            "7": self.submenu_custos,
            "8": self.submenu_relatorios,
            "9": self.submenu_graficos,
        }
        while True:
            self._cabecalho("MRP II - PEDAL FORTE BICICLETAS")
            print("1. Cadastros (itens, estrutura, centros, roteiros)")
            print("2. Estoque (movimentar, saldo, kardex)")
            print("3. Plano Mestre de Producao (MPS)")
            print("4. Executar MRP")
            print("5. Ordens de producao e de compra")
            print("6. Carga x capacidade (CRP)")
            print("7. Custo padrao dos produtos")
            print("8. Relatorios (exportar CSV)")
            print("9. Graficos de gestao (matplotlib)")
            print("0. Sair")
            print("-" * LARGURA)
            opcao = utils.ler_opcao(
                "Escolha uma opcao: ", [*destinos, "0"]
            )
            if opcao == "0":
                print("Ate logo!")
                return
            destinos[opcao]()

    def cadastros(self):
        acoes = {
            "1": ("Itens", self.submenu_itens),
            "2": ("Estrutura de produto (BOM)", self.submenu_estrutura),
            "3": ("Centros de trabalho e roteiros", self.submenu_centros),
        }
        self._submenu("CADASTROS", acoes)

    def submenu_itens(self):
        acoes = {
            "1": ("Cadastrar item", self.itens.cadastrar_interativo),
            "2": ("Alterar item", self.itens.alterar_interativo),
            "3": ("Listar itens", self.itens.exibir_lista),
            "4": ("Remover item", self.remover_item),
        }
        self._submenu("CADASTRO DE ITENS", acoes)

    def submenu_estrutura(self):
        acoes = {
            "1": (
                "Adicionar componente",
                self.estrutura.cadastrar_componente_interativo,
            ),
            "2": (
                "Alterar quantidade de componente",
                self.estrutura.alterar_quantidade_interativo,
            ),
            "3": (
                "Remover componente",
                self.estrutura.remover_componente_interativo,
            ),
            "4": ("Exibir estrutura (BOM)", self.estrutura.exibir_interativo),
            "5": (
                "Onde o item e usado",
                self.estrutura.onde_usado_interativo,
            ),
        }
        self._submenu("ESTRUTURA DE PRODUTO", acoes)

    def submenu_centros(self):
        acoes = {
            "1": (
                "Cadastrar centro de trabalho",
                self.capacidade.cadastrar_centro_interativo,
            ),
            "2": (
                "Alterar centro de trabalho",
                self.capacidade.alterar_centro_interativo,
            ),
            "3": ("Listar centros", self.capacidade.exibir_centros),
            "4": (
                "Remover centro de trabalho",
                self.capacidade.remover_centro_interativo,
            ),
            "5": (
                "Definir roteiro de um item",
                self.capacidade.definir_roteiro_interativo,
            ),
            "6": ("Listar roteiros", self.capacidade.exibir_roteiros),
            "7": (
                "Remover roteiro de um item",
                self.capacidade.remover_roteiro_interativo,
            ),
        }
        self._submenu("CENTROS DE TRABALHO E ROTEIROS", acoes)

    def submenu_estoque(self):
        acoes = {
            "1": ("Movimentar estoque", self.estoque.movimentar_interativo),
            "2": (
                "Consultar saldo e kardex",
                self.estoque.consultar_interativo,
            ),
            "3": ("Posicao de estoque", self.estoque.exibir_posicao),
        }
        self._submenu("ESTOQUE", acoes)

    def submenu_mps(self):
        acoes = {
            "1": (
                "Cadastrar ou alterar demanda de um produto",
                self.mps.definir_interativo,
            ),
            "2": ("Exibir plano mestre", self.mps.exibir),
            "3": ("Remover produto do plano", self.mps.remover_interativo),
        }
        self._submenu("PLANO MESTRE DE PRODUCAO (MPS)", acoes)

    def submenu_mrp(self):
        acoes = {
            "1": (
                "Executar MRP e gerar ordens planejadas",
                self.mrp.executar_interativo,
            ),
            "2": (
                "Exibir registro MRP de um item",
                self.mrp.exibir_registro_interativo,
            ),
            "3": ("Exibir mensagens de excecao", self.mrp.exibir_excecoes),
        }
        self._submenu("MRP - PLANEJAMENTO DAS NECESSIDADES", acoes)

    def submenu_ordens(self):
        acoes = {
            "1": (
                "Ordens em aberto (firmar, liberar, apontar, receber)",
                self.ordens.gerenciar_interativo,
            ),
            "2": ("Listar ordens encerradas", self.ordens.exibir_encerradas),
        }
        self._submenu("ORDENS DE PRODUCAO E DE COMPRA", acoes)

    def submenu_crp(self):
        acoes = {
            "1": (
                "Carga x capacidade de um centro",
                self.crp.exibir_interativo,
            ),
            "2": ("Resumo de todos os centros", self.crp.exibir_resumo),
        }
        self._submenu("CARGA x CAPACIDADE (CRP)", acoes)

    def submenu_custos(self):
        acoes = {
            "1": (
                "Custo padrao de um item fabricado",
                self.custos.exibir_interativo,
            ),
            "2": ("Resumo dos itens fabricados", self.custos.exibir_resumo),
            "3": (
                "Gravar custo padrao nos itens",
                self.custos.atualizar_interativo,
            ),
        }
        self._submenu("CUSTO PADRAO", acoes)

    def submenu_relatorios(self):
        acoes = {
            "1": (
                "Exportar posicao de estoque",
                self.relatorios.exportar_estoque_interativo,
            ),
            "2": (
                "Exportar lista de ordens",
                self.relatorios.exportar_ordens_interativo,
            ),
            "3": (
                "Exportar os dois relatorios",
                self.relatorios.exportar_tudo_interativo,
            ),
        }
        self._submenu("RELATORIOS (CSV)", acoes)

    def submenu_graficos(self):
        acoes = {
            "1": ("Posicao de estoque", self.graficos.posicao_estoque),
            "2": (
                "Estoque projetado de um item",
                self.graficos.estoque_projetado_interativo,
            ),
            "3": (
                "Ordens por semana de entrega",
                self.graficos.ordens_por_semana,
            ),
            "4": (
                "Carga x capacidade de um centro",
                self.graficos.carga_capacidade_interativo,
            ),
        }
        self._submenu("GRAFICOS DE GESTAO", acoes)

    def remover_item(self):
        print(">> Remocao de item")
        codigo = utils.ler_codigo(">> Codigo do item: ")
        if not self.itens.existe(codigo):
            print(f"ERRO: o item {codigo} nao esta cadastrado.")
            return
        motivo = self._motivo_para_nao_remover(codigo)
        if motivo:
            print(f"ERRO: {motivo}")
            return
        confirmacao = utils.ler_opcao(
            f">> Remover {codigo}? [S/N]: ", ["S", "N"]
        )
        if confirmacao == "N":
            print("Operacao cancelada.")
            return
        self.itens.remover(codigo)
        print(f"Item {codigo} removido.")

    def _motivo_para_nao_remover(self, codigo):
        if self.estrutura.em_uso(codigo):
            pais = self.estrutura.pais_de(codigo)
            if pais:
                return (f"{codigo} e componente de: {', '.join(pais)}. "
                        "Remova-o da BOM antes.")
            return (f"{codigo} possui estrutura propria. "
                    "Remova os componentes dele antes.")
        if self.capacidade.roteiro(codigo):
            return (f"{codigo} possui roteiro de fabricacao. "
                    "Remova o roteiro antes.")
        if self.mps.possui_demanda(codigo):
            return f"{codigo} esta no plano mestre. Remova-o do MPS antes."
        if self.ordens.possui_ordem(codigo):
            return (f"{codigo} possui ordens de producao ou de compra "
                    "e nao pode ser removido.")
        if self.estoque.possui_movimento(codigo):
            return (f"{codigo} possui movimentacoes no kardex e nao pode "
                    "ser removido (RN10).")
        return None
