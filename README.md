# Downloader Copernicus

Aplicacao em Python para buscar e baixar produtos Sentinel no Copernicus Data Space Ecosystem (CDSE), com autenticacao via `.netrc` e interface grafica em Qt.

O projeto possui dois pontos principais:

- [`main.py`](./main.py): inicia a interface grafica do downloader
- [`copernicus_downloader.py`](./copernicus_downloader.py): contem a classe responsavel pela autenticacao, busca do produto e download do arquivo

## Funcionalidades

- autenticacao no CDSE com credenciais locais em `.netrc`
- busca do produto pelo nome exato no catalogo OData
- tentativa automatica com e sem o sufixo `.SAFE`
- download do produto em `.zip`
- interface grafica para informar o nome da imagem e acompanhar mensagens
- salvamento automatico na pasta `imagens/`

## Estrutura do projeto

```text
downloadercopernicus/
|-- imagens/
|-- ui/
|   |-- janela1.ui
|-- copernicus_downloader.py
|-- main.py
|-- pixi.toml
|-- pixi.lock
|-- README.md
|-- LICENSE
```

## Requisitos

- Windows 64-bit
- [Pixi](https://pixi.sh/latest/) instalado
- conta ativa no Copernicus Data Space Ecosystem
- arquivo `.netrc` configurado no diretorio do usuario

Dependencias declaradas no projeto:

- Python `>=3.14.3,<3.15`
- `requests`
- `qgis`

## Configuracao de credenciais

As credenciais nao ficam no codigo. O acesso ao CDSE e feito a partir do arquivo `.netrc` do proprio usuario.

Exemplo:

```text
machine https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token
login SEU_LOGIN
password SUA_SENHA
```

Observacoes importantes:

- nao publique o arquivo `.netrc`
- cada pessoa que usar o projeto deve configurar o seu proprio `.netrc`
- mantenha usuario, senha e tokens fora do repositorio
- se o repositorio for publico, as credenciais devem existir somente no ambiente local de quem executa o projeto

## Instalacao

Clone o repositorio e entre na pasta:

```powershell
git clone <URL_DO_REPOSITORIO>
cd downloadercopernicus
```

Instale o ambiente:

```powershell
pixi install
```

## Como executar

### Interface grafica

Para abrir a janela do downloader:

```powershell
pixi run python .\main.py
```

Se o comando `pixi` nao estiver disponivel no terminal, voce tambem pode usar diretamente o Python do ambiente local:

```powershell
& ".\.pixi\envs\default\python.exe" ".\main.py"
```

Na interface, basta:

1. informar o nome da imagem Sentinel
2. clicar em `Download`
3. acompanhar o status e as mensagens na propria janela

### Uso direto pela classe

Tambem e possivel usar a classe [`CopernicusDownloader`](./copernicus_downloader.py) em outros scripts Python.

Exemplo:

```python
from copernicus_downloader import CopernicusDownloader, PASTA_IMAGENS, ARQUIVO_NETRC

downloader = CopernicusDownloader(
    pasta_destino=str(PASTA_IMAGENS),
    netrc_path=str(ARQUIVO_NETRC),
)

caminho = downloader.download("S2A_MSIL2A_20220503T130251_N0510_R095_T23KPS_20241129T025850")
print(caminho)
```

## Interface

O arquivo [`ui/janela1.ui`](./ui/janela1.ui) define a janela principal da aplicacao. Ele foi pensado para funcionar como base da interface e pode ser evoluido com novos recursos, como:

- barra de progresso
- selecao de pasta de destino
- fila de downloads
- leitura de lista de produtos

O arquivo [`main.py`](./main.py) faz a integracao entre essa interface e a classe de download.

## Saida esperada

Os arquivos baixados sao salvos automaticamente em:

```text
imagens/<NOME_DO_PRODUTO>.zip
```

Exemplo:

```text
imagens/S2A_MSIL2A_20220503T130251_N0510_R095_T23KPS_20241129T025850.SAFE.zip
```

## Como funciona

O fluxo atual do downloader e:

1. ler `login` e `password` do `.netrc`
2. solicitar um `access_token` ao endpoint de autenticacao do CDSE
3. consultar o catalogo OData pelo nome do produto
4. localizar o `Id` do produto encontrado
5. baixar o conteudo autenticado do produto
6. salvar o arquivo na pasta `imagens/`

Na interface grafica, o download roda em uma `QThread`, evitando travar a janela durante a operacao.

## Tratamento de erros

O projeto ja trata cenarios comuns, como:

- `.netrc` ausente
- credenciais incompletas
- produto nao encontrado
- produto offline
- falha na autenticacao
- erro HTTP durante o download

As mensagens de erro aparecem na interface e tambem podem ser tratadas no uso programatico da classe.

## Roadmap

Melhorias previstas:

- leitura de lista de imagens a partir de arquivo texto
- download em lote
- barra de progresso real
- escolha da pasta de destino pela interface
- logs mais detalhados
- testes automatizados

## Referencias

- [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/)
- [Documentacao de autenticacao](https://documentation.dataspace.copernicus.eu/APIs/Token.html)
- [Documentacao da OData API](https://documentation.dataspace.copernicus.eu/APIs/OData.html)

## Licenca

Este projeto esta licenciado sob a licenca MIT. Veja o arquivo [`LICENSE`](./LICENSE).
