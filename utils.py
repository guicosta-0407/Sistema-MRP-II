import re
from datetime import date, datetime

PADRAO_CODIGO = re.compile(r"^(PA|SA|MP)-\d{3,}$")
TIPOS_VALIDOS = ["PA", "SA", "MP"]


def normalizar_codigo(texto):
    return texto.trip().upper()

def codigo_valido(codigo):
    return bool(PADRAO_CODIGO.match(codigo))

def tipo_do_codigo(codigo):
    return codigo.split("-")[0]

def formatar_decimal(valor, casas=1):
    return f"{valor:.{casas}f}".replace(".", ",")

def formatar_moeda(valor):
    return formatar_decimal(valor, 2)

def formatar_data(data):
    return data.strftime("%d/%m/%Y")

def data_hoje():
    return formatar_data(date.today())

def ler_texto(mensagem, obrigatorio=True):
    while True:
        texto = input(mensagem).strip()
        # Retorna o texto se ele estiver preenchido ou se o campo nao for obrigatorio.
        if texto or not obrigatorio:
            return texto
        print("ERRO: o campo nao pode ficar vazio.")

def ler_inteiro(mensagem, minimo=None, maximo=None):
    while True:
        entrada = input(mensagem).strip()
        try:
            valor = int(entrada)
        except ValueError:
            print("ERRO: digite um numero inteiro.")
            continue
        # Checa se o limite foi informado.
        if minimo is not None and valor < minimo:
            print(f"ERRO: o valor minimo e {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"ERRO: o valor maximo e {maximo}.")
            continue
        return valor

def ler_decimal(mensagem, minimo=None):
    while True:
        # Troca a vírgula por ponto antes de usar float.
        entrada = input(mensagem).strip().replace(",", ".")
        try:
            valor = float(entrada)
        except ValueError:
            print("ERRO: digite um numero valido.")
            continue
        if minimo is not None and valor < minimo:
            print(f"ERRO: o valor minimo e {formatar_decimal(minimo)}.")
            continue
        return valor

def ler_opcao(mensagem, opcoes):
    opcoes = [opcao.upper() for opcao in opcoes]
    while True:
        entrada = input(mensagem).strip().upper()
        if entrada in opcoes:
            return entrada
        print(f"ERRO: opcoes validas: {', '.join(opcoes)}.")

def ler_codigo(mensagem, tipos=TIPOS_VALIDOS):
    while True:
        codigo = normalizar_codigo(input(mensagem))
        # Valida o formato do código e se o tipo é válido.
        if not codigo_valido(codigo):
            print("ERRO: formato invalido. Use Tipo-Numero (ex.: PA-001).")
            continue
        if tipo_do_codigo(codigo) not in tipos:
            print(f"ERRO: o tipo deve ser um destes: {', '.join(tipos)}.")
            continue
        return codigo

def ler_data(mensagem):
    while True:
        entrada = input(mensagem).strip()
        # Enter em branco assume a data de hoje.
        if not entrada:
            return data_hoje()
        try:
            # O strptime valida se a data existe.
            data = datetime.strptime(entrada, "%d/%m/%Y")
            return formatar_data(data)
        except ValueError:
            print("ERRO: use o formato DD/MM/AAAA.")