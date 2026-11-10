const startButton = document.querySelector('#start-scanner');
const stopButton = document.querySelector('#stop-scanner');
const video = document.querySelector('#qr-video');
const placeholder = document.querySelector('#scanner-placeholder');
const status = document.querySelector('#scanner-status');
const form = document.querySelector('#scan-form');
const codeInput = document.querySelector('#credential-code');

if (startButton && stopButton && video && placeholder && status && form && codeInput) {
  let reader = null;
  let controls = null;
  let completed = false;

  const stopScanner = () => {
    controls?.stop();
    controls = null;
    video.srcObject?.getTracks().forEach((track) => track.stop());
    video.srcObject = null;
    video.pause();
    video.classList.add('hidden');
    placeholder.classList.remove('hidden');
    startButton.classList.remove('hidden');
    startButton.disabled = false;
    stopButton.classList.add('hidden');
  };

  startButton.addEventListener('click', async () => {
    if (!window.isSecureContext) {
      status.textContent = 'A câmera exige HTTPS ou localhost. Use a pesquisa manual nesta conexão.';
      return;
    }

    completed = false;
    startButton.disabled = true;
    status.textContent = 'Solicitando acesso à câmera…';

    try {
      const { BrowserQRCodeReader } = await import('@zxing/browser');
      reader = new BrowserQRCodeReader();
      controls = await reader.decodeFromVideoDevice(undefined, video, (result) => {
        if (result && !completed) {
          completed = true;
          controls?.stop();
          controls = null;
          codeInput.value = result.getText();
          status.textContent = 'QR Code lido. Validando a credencial…';
          form.requestSubmit();
        }
      });
      video.classList.remove('hidden');
      placeholder.classList.add('hidden');
      startButton.classList.add('hidden');
      stopButton.classList.remove('hidden');
      status.textContent = 'Aponte a câmera para o QR Code da pulseira.';
    } catch (error) {
      stopScanner();
      status.textContent = error?.name === 'NotAllowedError'
        ? 'Acesso à câmera negado. Autorize a câmera no navegador ou use a pesquisa manual.'
        : error?.name === 'NotFoundError'
          ? 'Nenhuma câmera foi encontrada neste dispositivo. Use a pesquisa manual.'
          : 'Câmera indisponível ou ocupada neste dispositivo. Feche outros aplicativos que a usam ou pesquise manualmente.';
    }
  });

  stopButton.addEventListener('click', () => {
    stopScanner();
    status.textContent = 'Leitura pausada.';
  });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden && controls) {
      stopScanner();
      status.textContent = 'Câmera pausada ao sair da tela.';
    }
  });

  window.addEventListener('pagehide', stopScanner, { once: true });
}
