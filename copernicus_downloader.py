import netrc
from pathlib import Path
from typing import Optional

import requests


class CopernicusDownloader:
    """
    Classe responsável por buscar e baixar um produto no catálogo
    Copernicus Data Space Ecosystem.

    A classe centraliza toda a lógica de:
    - leitura de credenciais;
    - autenticação via token;
    - busca de um produto pelo nome;
    - download do arquivo .zip.

    Atributos de classe:
    - TOKEN_URL: endpoint usado para obter o token de autenticação.
    - CATALOGUE_URL: endpoint do catálogo de produtos.
    - DOWNLOAD_URL: endpoint de download do produto selecionado.
    - CLIENT_ID: identificador do cliente usado na autenticação.
    - TIMEOUT: tempo máximo de espera das requisições HTTP.
    - CHUNK_SIZE: tamanho dos blocos usados no download em streaming.
    """

    TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    CATALOGUE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    DOWNLOAD_URL = "https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
    CLIENT_ID = "cdse-public"
    TIMEOUT = 120
    CHUNK_SIZE = 4*1024 * 1024

    def __init__(
        self,
        pasta_destino: str,
        netrc_path: Optional[str] = None,
        machine_name: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        """
        Inicializa o downloader.

        Atributos de instância:
        - self.pasta_destino: pasta onde o arquivo baixado será salvo.
        - self.netrc_path: caminho para o arquivo .netrc com as credenciais.
        - self.machine_name: nome da máquina/host usado para localizar as credenciais.
        - self.session: sessão HTTP reutilizável do requests.
        """
        self.pasta_destino = Path(pasta_destino)
        # Garante que a pasta de destino exista antes do download.
        self.pasta_destino.mkdir(parents=True, exist_ok=True)

        self.netrc_path = Path(netrc_path or Path.home() / ".netrc")
        # Se nenhum nome de máquina for informado, usa a própria URL do token.
        self.machine_name = machine_name or self.TOKEN_URL
        # Reaproveita uma sessão existente ou cria uma nova.
        self.session = session or requests.Session()

    def download(self, nome_imagem: str) -> Path:
        """
        Método principal da classe.

        Recebe o nome da imagem/produto, busca esse produto no catálogo,
        obtém um token de autenticação e faz o download do arquivo.

        Parâmetro:
        - nome_imagem: nome do produto desejado.

        Retorno:
        - caminho completo do arquivo salvo no disco.
        """
        nome_consulta = nome_imagem.strip()
        if not nome_consulta:
            raise ValueError("O nome da imagem nao pode ser vazio.")

        # Busca no catálogo o produto correspondente ao nome informado.
        produto = self._buscar_produto(nome_consulta)
        # Obtém o token de acesso necessário para baixar o arquivo.
        token = self._obter_token()

        nome_arquivo = f"{produto['Name']}.zip"
        caminho_saida = self.pasta_destino / nome_arquivo
        url_download = self.DOWNLOAD_URL.format(product_id=produto["Id"])

        # Faz o download em streaming para evitar carregar tudo na memória.
        with self.session.get(
            url_download,
            headers={"Authorization": f"Bearer {token}"},
            stream=True,
            timeout=self.TIMEOUT,
        ) as response:
            response.raise_for_status()
            with caminho_saida.open("wb") as arquivo:
                for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                    if chunk:
                        arquivo.write(chunk)

        return caminho_saida

    def _obter_token(self) -> str:
        """
        Faz a autenticação no serviço da Copernicus e retorna o access token.

        Função interna da classe.
        Ela usa as credenciais lidas do .netrc para solicitar um token OAuth.
        """
        usuario, senha = self._ler_credenciais()
        response = self.session.post(
            self.TOKEN_URL,
            data={
                "client_id": self.CLIENT_ID,
                "grant_type": "password",
                "username": usuario,
                "password": senha,
            },
            timeout=self.TIMEOUT,
        )
        response.raise_for_status()

        access_token = response.json().get("access_token")
        if not access_token:
            raise RuntimeError("A resposta de autenticacao nao trouxe access_token.")
        return access_token

    def _ler_credenciais(self) -> tuple[str, str]:
        """
        Lê as credenciais do arquivo .netrc.

        A função tenta localizar login e senha usando o nome da máquina.
        Se não encontrar pelo parser padrão da biblioteca netrc, tenta uma
        leitura manual linha por linha.

        Retorno:
        - tupla (login, senha)
        """
        if not self.netrc_path.exists():
            raise FileNotFoundError(f"Arquivo .netrc nao encontrado em: {self.netrc_path}")

        parser_netrc = netrc.netrc(str(self.netrc_path))
        credenciais = parser_netrc.authenticators(self.machine_name)
        if credenciais is None:
            credenciais = parser_netrc.authenticators("identity.dataspace.copernicus.eu")
        if credenciais is None:
            credenciais = self._ler_credenciais_manualmente()

        if credenciais is None:
            raise RuntimeError(
                "Nao encontrei credenciais no .netrc para o endpoint da Copernicus."
            )

        login, _, password = credenciais
        if not login or not password:
            raise RuntimeError("As credenciais no .netrc estao incompletas.")
        return login, password

    def _ler_credenciais_manualmente(self) -> Optional[tuple[str, None, str]]:
        """
        Faz uma leitura manual do arquivo .netrc.

        Essa função serve como alternativa caso o parser padrão não encontre
        corretamente as credenciais.

        Retorno:
        - tupla no formato (login, None, password), para manter compatibilidade
          com a estrutura retornada por netrc.authenticators().
        - None, se nada for encontrado.
        """
        machine_atual = None
        login = None
        password = None

        for linha in self.netrc_path.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue

            partes = linha.split(maxsplit=1)
            if len(partes) != 2:
                continue

            chave, valor = partes
            if chave == "machine":
                # Se já terminou de ler uma máquina válida, retorna suas credenciais.
                if machine_atual == self.machine_name and login and password:
                    return login, None, password
                machine_atual = valor
                login = None
                password = None
            elif machine_atual == self.machine_name and chave == "login":
                login = valor
            elif machine_atual == self.machine_name and chave == "password":
                password = valor

        if machine_atual == self.machine_name and login and password:
            return login, None, password
        return None

    def _buscar_produto(self, nome_imagem: str) -> dict:
        """
        Busca um produto pelo nome exato.

        A função tenta primeiro o nome informado pelo usuário.
        Se ele não terminar em .SAFE, também tenta a versão com esse sufixo.

        Retorno:
        - dicionário com os dados do produto encontrado.
        """
        nomes_tentados = [nome_imagem]
        if not nome_imagem.endswith(".SAFE"):
            nomes_tentados.append(f"{nome_imagem}.SAFE")

        for nome in nomes_tentados:
            produto = self._buscar_por_nome_exato(nome)
            if produto is not None:
                return produto

        raise FileNotFoundError(
            "Produto nao encontrado no catalogo Copernicus. "
            f"Nomes tentados: {', '.join(nomes_tentados)}"
        )

    def _buscar_por_nome_exato(self, nome_imagem: str) -> Optional[dict]:
        """
        Executa uma consulta OData filtrando pelo nome exato do produto.

        Parâmetro:
        - nome_imagem: nome exato do produto no catálogo.

        Retorno:
        - dicionário com os dados do produto, se encontrado;
        - None, se nenhum produto corresponder.
        """
        filtro = f"Name eq '{self._escapar_valor_odata(nome_imagem)}'"
        response = self.session.get(
            self.CATALOGUE_URL,
            params={
                "$filter": filtro,
                "$select": "Id,Name,Online,ContentLength",
                "$top": 2,
            },
            timeout=self.TIMEOUT,
        )
        response.raise_for_status()

        produtos = response.json().get("value", [])
        if not produtos:
            return None

        if len(produtos) > 1:
            raise RuntimeError(
                f"A busca por '{nome_imagem}' retornou mais de um produto, revise o filtro."
            )

        produto = produtos[0]
        if produto.get("Online") is False:
            raise RuntimeError(f"O produto '{nome_imagem}' existe, mas nao esta online para download.")
        return produto

    @staticmethod
    def _escapar_valor_odata(valor: str) -> str:
        """
        Escapa aspas simples para que o valor possa ser usado com segurança
        em um filtro OData.

        Como é um método estático, ele não depende de nenhum atributo da instância.
        """
        return valor.replace("'", "''")


# Constantes de uso direto no script.
# Elas facilitam testes rápidos sem precisar digitar os valores toda vez.
NOME_IMAGEM = "S2A_MSIL2A_20220503T130251_N0510_R095_T23KPS_20241129T025850"
PASTA_IMAGENS = Path(__file__).resolve().parent / "imagens"
ARQUIVO_NETRC = Path.home() / ".netrc"


def main() -> None:
    """
    Função principal do script.

    Cria um objeto da classe CopernicusDownloader usando a pasta de destino
    e o arquivo .netrc definidos acima, depois inicia o download.
    """
    downloader = CopernicusDownloader(
        pasta_destino=str(PASTA_IMAGENS),
        netrc_path=str(ARQUIVO_NETRC),
    )
    caminho = downloader.download(NOME_IMAGEM)
    print(f"Arquivo salvo em: {caminho}")


if __name__ == "__main__":
    main()