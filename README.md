# IDP - Interpretador de Gestos Web (WGI)
1.2026 - Trabalho da Disciplina de Oficina em Soluções Web

WGI: Web Gesture Interpreter

O Web Gesture Interpreter (WGI) é uma extensão inovadora projetada para transformar a maneira como interagimos com o navegador. Ao converter movimentos manuais capturados via webcam em comandos de navegação, o projeto elimina a barreira do contato físico com periféricos, oferecendo uma experiência de usuário fluida, intuitiva e futurista.

Visão Geral do Projeto
A proposta central do WGI é democratizar o controle por gestos no ecossistema web. Seja para facilitar o consumo de conteúdo em momentos de multitarefa  como seguir uma receita na cozinha ou realizar uma apresentação  ou para servir como uma ferramenta crítica de acessibilidade, o interpretador traduz a linguagem corporal em ações digitais em tempo real.

Proposta de Valor e Diferenciais
O WGI não é apenas uma alternativa ao mouse, mas uma nova camada de interação que se destaca por:

Acessibilidade Inclusiva: Oferece autonomia para usuários com limitações motoras que possuem dificuldade no manuseio de dispositivos convencionais.

Navegação Sem Contato (Touchless): Ideal para ambientes onde a higiene ou a distância do dispositivo são prioridades.

Interatividade em Mídias Sociais: Permite o consumo de feeds verticais e mídias através de "swipes" e comandos gestuais naturais.

Expansão para Imersão: Serve como uma ponte de baixo custo para experiências de Realidade Aumentada (AR) diretamente no browser, sem a necessidade de hardware caro.

Desde o controle de câmeras em conferências remotas até a navegação em jogos baseados em web, o potencial do WGI se estende a qualquer aplicação que se beneficie de uma interface espacial. Ele transforma o navegador de uma janela estática em um ambiente responsivo ao movimento humano.

## macOS / Apple Silicon

Para compilar e executar o backend em Macs M1/M2/M3:

- Use Python arm64 nativo. Confirme com `python3 -c "import platform; print(platform.machine())"`; o resultado deve ser `arm64`.
- Use Python 3.10 ou 3.11 para manter compatibilidade com MediaPipe.
- De permissao de Camera e Accessibility ao Terminal ou ao app compilado em System Settings > Privacy & Security.
- O backend tenta abrir a webcam com AVFoundation no macOS e volta para o backend padrao do OpenCV se necessario.
- O arquivo `calibration.json` e salvo ao lado do executavel quando o backend esta compilado.

## Linux / X11 / Wayland

O backend tenta abrir a webcam no Linux usando V4L2 e volta para o backend padrao do OpenCV se necessario.

- Em sessoes X11/Xorg, o controle do cursor usa PyAutoGUI. Se o PyAutoGUI falhar, o backend tenta usar `xdotool` como fallback para movimento, clique esquerdo, clique direito, clique duplo, drag e scroll.
- Instale `xdotool` no Linux X11 quando quiser o fallback: `sudo apt install xdotool`.
- Em Wayland, a camera pode funcionar, mas muitos compositores bloqueiam controle global do cursor por seguranca. Para suporte completo de clique/movimento, use uma sessao X11/Xorg ou configure uma ferramenta de injecao permitida pelo compositor.
- O endpoint `/state` inclui `display_server` no Linux para ajudar a diagnosticar se a sessao atual e `x11`, `wayland` ou `unknown`.
