# IGW - Inovação em Gestos

Extensão do Chrome que permite controlar o navegador usando gestos manuais detectados pela webcam.

## Como instalar a extensão

### Para desenvolvimento/teste:

1. **Abra o Chrome** e digite na barra de endereços: `chrome://extensions/`

2. **Ative o Modo Desenvolvedor** (canto superior direito)

3. **Clique em "Carregar sem compactação"**

4. **Selecione a pasta** `frontend/extension/` do seu projeto

5. **A extensão será carregada** e aparecerá na lista

### Para distribuição:

1. **Compacte a pasta** `extension/` em um arquivo ZIP

2. **Faça upload** no Chrome Web Store

3. **Publique** após revisão

## Arquivos necessários

- `manifest.json` - Configuração da extensão
- `popup.html` - Interface do popup
- `popup.js` - Lógica do popup
- `background.js` - Script em segundo plano
- `content-script.js` - Script injetado nas páginas
- `icons/icon.png` - Ícone da extensão (128x128px recomendado)

## Permissões necessárias

- `activeTab` - Acesso à aba atual
- `storage` - Armazenamento local
- `scripting` - Execução de scripts
- `<all_urls>` - Acesso a todas as páginas web

## Como usar

1. **Clique no ícone** da extensão na barra de ferramentas
2. **Clique em "Testar Câmera"** para abrir a página de demonstração
3. **Permita o acesso** à câmera quando solicitado
4. **Faça gestos** com a mão para controlar o navegador

## Desenvolvimento

Para modificar a extensão:

1. Edite os arquivos na pasta `extension/`
2. Recarregue a extensão em `chrome://extensions/`
3. Teste as mudanças

## Suporte

Para dúvidas ou problemas, consulte a documentação do Chrome Extensions:
https://developer.chrome.com/docs/extensions/