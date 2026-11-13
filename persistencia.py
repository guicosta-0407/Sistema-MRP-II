import csv
import json
from pathlib import Path


class ErroPersistencia(Exception):
    pass


class Repositorio:
    def __init__(self, diretorio=None):
        # Usa data/ relativa a este arquivo, independentemente do diretório de execução.
        base = Path(__file__).resolve().parent
        self.diretorio = Path(diretorio) if diretorio else base / "data"
        self.diretorio.mkdir(parents=True, exist_ok=True)

    def caminho(self, nome):
        return self.diretorio / nome

    def carregar_json(self, nome, padrao=None):
        arquivo = self.caminho(nome)
        # Se ausente, retorna o padrão informado ou {}.
        if not arquivo.exists():
            return {} if padrao is None else padrao
        try:
            with arquivo.open(encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as erro:
            raise ErroPersistencia(f"Arquivo {nome} corrompido: {erro}")

    def salvar_json(self, nome, dados):
        arquivo = self.caminho(nome)
        temporario = arquivo.with_suffix(".tmp")
        # Substitui o original somente após concluir a gravação temporária.
        with temporario.open("w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        temporario.replace(arquivo)

    def carregar_csv(self, nome):
        arquivo = self.caminho(nome)
        if not arquivo.exists():
            return []
        with arquivo.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f, delimiter=";"))

    def anexar_csv(self, nome, campos, linha):
        arquivo = self.caminho(nome)
        novo = not arquivo.exists()
        with arquivo.open("a", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=campos, delimiter=";")
            if novo:
                escritor.writeheader()
            escritor.writerow(linha)

    def salvar_csv(self, nome, campos, linhas):
        arquivo = self.caminho(nome)
        with arquivo.open("w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=campos, delimiter=";")
            escritor.writeheader()
            escritor.writerows(linhas)