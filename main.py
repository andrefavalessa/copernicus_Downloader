import sys
from pathlib import Path

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi

from copernicus_downloader import ARQUIVO_NETRC, NOME_IMAGEM, PASTA_IMAGENS, CopernicusDownloader


UI_PATH = Path(__file__).resolve().parent / "ui" / "janela1.ui"


class DownloadWorker(QObject):
    finished = pyqtSignal()
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, nome_imagem: str) -> None:
        super().__init__()
        self.nome_imagem = nome_imagem

    def run(self) -> None:
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
    def __init__(self) -> None:
        super().__init__()
        loadUi(str(UI_PATH), self)

        self.setWindowTitle("Downloader Copernicus")
        self.thread_download = None
        self.worker = None

        self.lineEditNomeImagem.setText(NOME_IMAGEM)
        self.labelPastaDestino.setText(str(PASTA_IMAGENS))
        self.labelNetrc.setText(str(ARQUIVO_NETRC))

        self.pushButtonDownload.clicked.connect(self.iniciar_download)
        self.lineEditNomeImagem.returnPressed.connect(self.iniciar_download)

    def iniciar_download(self) -> None:
        nome_imagem = self.lineEditNomeImagem.text().strip()
        if not nome_imagem:
            self._mostrar_erro("Informe o nome da imagem antes de iniciar o download.")
            return

        self.pushButtonDownload.setEnabled(False)
        self.labelStatus.setText("Baixando imagem...")
        self.plainTextEditLog.clear()
        self._adicionar_log(f"Iniciando download de: {nome_imagem}")
        self._adicionar_log(f"Pasta de destino: {PASTA_IMAGENS}")

        self.thread_download = QThread()
        self.worker = DownloadWorker(nome_imagem)
        self.worker.moveToThread(self.thread_download)

        self.thread_download.started.connect(self.worker.run)
        self.worker.success.connect(self._download_concluido)
        self.worker.error.connect(self._mostrar_erro)
        self.worker.finished.connect(self._finalizar_download)
        self.worker.finished.connect(self.thread_download.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread_download.finished.connect(self.thread_download.deleteLater)

        self.thread_download.start()

    def _download_concluido(self, caminho_arquivo: str) -> None:
        self.labelStatus.setText("Download concluido com sucesso.")
        self._adicionar_log(f"Arquivo salvo em: {caminho_arquivo}")

    def _mostrar_erro(self, mensagem: str) -> None:
        self.labelStatus.setText("Ocorreu um erro durante o download.")
        self._adicionar_log(f"Erro: {mensagem}")

    def _finalizar_download(self) -> None:
        self.pushButtonDownload.setEnabled(True)
        self.worker = None
        self.thread_download = None

    def _adicionar_log(self, mensagem: str) -> None:
        self.plainTextEditLog.appendPlainText(mensagem)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
