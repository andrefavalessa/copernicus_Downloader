import sys
from pathlib import Path

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi

from copernicus_downloader import ARQUIVO_NETRC, NOME_IMAGEM, PASTA_IMAGENS, CopernicusDownloader


# Caminho do arquivo .ui criado no Qt Designer.
UI_PATH = Path(__file__).resolve().parent / "ui" / "janela1.ui"


class DownloadWorker(QObject):
    """
    Classe auxiliar responsável por executar o download em segundo plano.

    Ela herda de QObject para poder trabalhar com sinais do PyQt.
    O objetivo é tirar a tarefa pesada de download da thread principal da interface,
    evitando que a janela fique travada durante a execução.

    Sinais da classe:
    - finished: emitido quando a execução termina, com sucesso ou erro.
    - success: emitido quando o download termina corretamente.
    - error: emitido quando alguma exceção ocorre.

    Atributo de instância:
    - self.nome_imagem: nome do produto que será baixado.
    """
    finished = pyqtSignal()
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, nome_imagem: str) -> None:
        """
        Inicializa o worker com o nome da imagem a ser baixada.
        """
        super().__init__()
        self.nome_imagem = nome_imagem

    def run(self) -> None:
        """
        Método executado dentro da thread.

        Ele cria um objeto da classe CopernicusDownloader, tenta realizar
        o download e emite um sinal indicando sucesso ou erro.
        """
        try:
            downloader = CopernicusDownloader(
                pasta_destino=str(PASTA_IMAGENS),
                netrc_path=str(ARQUIVO_NETRC),
            )
            caminho = downloader.download(self.nome_imagem)
            self.success.emit(str(caminho))
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    """
    Classe principal da interface gráfica.

    Ela herda de QMainWindow e representa a janela do programa.
    Sua responsabilidade é:
    - carregar a interface do arquivo .ui;
    - ler os dados digitados pelo usuário;
    - iniciar a thread de download;
    - atualizar os elementos visuais da janela.

    Atributos principais:
    - self.thread_download: guarda a thread usada no download.
    - self.worker: guarda o objeto worker que roda dentro da thread.
    """
    def __init__(self) -> None:
        """
        Monta a janela, carrega a interface e conecta os eventos.
        """
        super().__init__()
        loadUi(str(UI_PATH), self)

        self.setWindowTitle("Downloader Copernicus")
        self.thread_download = None
        self.worker = None

        # Preenche a interface com valores iniciais.
        self.lineEditNomeImagem.setText(NOME_IMAGEM)
        self.labelPastaDestino.setText(str(PASTA_IMAGENS))
        self.labelNetrc.setText(str(ARQUIVO_NETRC))

        # Conecta o botão e a tecla Enter ao método que inicia o download.
        self.pushButtonDownload.clicked.connect(self.iniciar_download)
        self.lineEditNomeImagem.returnPressed.connect(self.iniciar_download)

    def iniciar_download(self) -> None:
        """
        Inicia o processo de download.

        Esse método:
        - lê o nome da imagem digitado;
        - valida se o campo não está vazio;
        - prepara a interface;
        - cria a thread e o worker;
        - conecta os sinais e slots;
        - inicia a thread.
        """
        nome_imagem = self.lineEditNomeImagem.text().strip()
        if not nome_imagem:
            self._mostrar_erro("Informe o nome da imagem antes de iniciar o download.")
            return

        self.pushButtonDownload.setEnabled(False)
        self.labelStatus.setText("Baixando imagem...")
        self.plainTextEditLog.clear()
        self._adicionar_log(f"Iniciando download de: {nome_imagem}")
        self._adicionar_log(f"Pasta de destino: {PASTA_IMAGENS}")

        # Cria a thread separada e o worker responsável pelo download.
        self.thread_download = QThread()
        self.worker = DownloadWorker(nome_imagem)
        self.worker.moveToThread(self.thread_download)

        # Quando a thread começar, o método run() do worker será executado.
        self.thread_download.started.connect(self.worker.run)

        # Conecta os sinais do worker aos métodos da interface.
        self.worker.success.connect(self._download_concluido)
        self.worker.error.connect(self._mostrar_erro)
        self.worker.finished.connect(self._finalizar_download)

        # Ao terminar, encerra a thread e libera os objetos.
        self.worker.finished.connect(self.thread_download.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread_download.finished.connect(self.thread_download.deleteLater)

        self.thread_download.start()

    def _download_concluido(self, caminho_arquivo: str) -> None:
        """
        Atualiza a interface quando o download termina com sucesso.

        Parâmetro:
        - caminho_arquivo: caminho do arquivo salvo no disco.
        """
        self.labelStatus.setText("Download concluido com sucesso.")
        self._adicionar_log(f"Arquivo salvo em: {caminho_arquivo}")

    def _mostrar_erro(self, mensagem: str) -> None:
        """
        Exibe na interface uma mensagem de erro.

        Parâmetro:
        - mensagem: texto explicando o erro ocorrido.
        """
        self.labelStatus.setText("Ocorreu um erro durante o download.")
        self._adicionar_log(f"Erro: {mensagem}")

    def _finalizar_download(self) -> None:
        """
        Faz a limpeza final após o término do processo.

        Reabilita o botão e remove as referências para worker e thread.
        """
        self.pushButtonDownload.setEnabled(True)
        self.worker = None
        self.thread_download = None

    def _adicionar_log(self, mensagem: str) -> None:
        """
        Adiciona uma linha ao campo de log da interface.
        """
        self.plainTextEditLog.appendPlainText(mensagem)


def main() -> None:
    """
    Função principal da aplicação.

    Cria a aplicação Qt, instancia a janela principal, exibe a interface
    e inicia o loop de eventos.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()