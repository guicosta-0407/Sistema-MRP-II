import utils
from estoque import Estoque
from estrutura import Estrutura
from itens import CadastroItens
from persistencia import ErroPersistencia

LARGURA = 50


class Menu:
    def __init__(self, repositorio):
        self.itens = CadastroItens(repositorio)
        self.estrutura = Estrutura(repositorio, self.itens)
        self.estoque = Estoque(repositorio, self.itens)

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
            print("0. Sair")
            print("-" * LARGURA)
            opcao = utils.ler_opcao("Escolha uma opcao: ", list("123456780"))
            if opcao == "0":
                print("Ate logo!")
                return
            if opcao == "1":
                self.cadastros()
            elif opcao == "2":
                self.submenu_estoque()
            else:
                print("Opcao ainda nao implementada.")

    def cadastros(self):
        acoes = {
            "1": ("Cadastrar item", self.itens.cadastrar_interativo),
            "2": ("Alterar item", self.itens.alterar_interativo),
            "3": ("Listar itens", self.itens.exibir_lista),
            "4": (
                "Adicionar componente a estrutura",
                self.estrutura.cadastrar_componente_interativo,
            ),
            "5": (
                "Alterar quantidade de componente",
                self.estrutura.alterar_quantidade_interativo,
            ),
            "6": (
                "Remover componente da estrutura",
                self.estrutura.remover_componente_interativo,
            ),
            "7": ("Exibir estrutura (BOM)", self.estrutura.exibir_interativo),
            "8": ("Remover item", self.remover_item),
            "9": ("Onde o item e usado", self.estrutura.onde_usado_interativo),
        }
        self._submenu("CADASTROS", acoes)

    def submenu_estoque(self):
        acoes = {
            "1": ("Movimentar estoque", self.estoque.movimentar_interativo),
            "2": ("Consultar saldo e kardex", self.estoque.consultar_interativo),
            "3": ("Posicao de estoque", self.estoque.exibir_posicao),
        }
        self._submenu("ESTOQUE", acoes)

    def remover_item(self):
        print(">> Remocao de item")
        codigo = utils.ler_codigo(">> Codigo do item: ")
        if not self.itens.existe(codigo):
            print(f"ERRO: o item {codigo} nao esta cadastrado.")
            return
        if self.estrutura.em_uso(codigo):
            pais = self.estrutura.pais_de(codigo)
            if pais:
                print(
                    f"ERRO: {codigo} e componente de: {', '.join(pais)}. "
                    "Remova-o da BOM antes."
                )
            else:
                print(
                    f"ERRO: {codigo} possui estrutura propria. "
                    "Remova os componentes dele antes."
                )
            return
        if self.estoque.possui_movimento(codigo):
            print(
                f"ERRO: {codigo} possui movimentacoes no kardex e nao pode "
                "ser removido (RN10)."
            )
            return
        confirmacao = utils.ler_opcao(
            f">> Remover {codigo}? [S/N]: ", ["S", "N"]
        )
        if confirmacao == "N":
            print("Operacao cancelada.")
            return
        self.itens.remover(codigo)
        print(f"Item {codigo} removido.")