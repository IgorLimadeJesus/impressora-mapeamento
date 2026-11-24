# USB to LPT Mapper

Aplicativo Windows em Python para associar uma fila de impressão instalada (inclusive USB) a `LPT1`–`LPT9`, preservando os bytes RAW enviados por sistemas legados. O caso principal é uma Zebra S4M usada pelo TOTVS Protheus em `LPT3`.

## O que ele faz

- enumera impressoras locais e de rede usando a API do spooler do Windows;
- identifica porta, driver, estado, compartilhamento e indícios de conexão USB;
- preserva um compartilhamento existente ou cria um novo com `SetPrinter`;
- cria e verifica o redirecionamento com `net use LPTx: \\COMPUTADOR\FILA`;
- mostra os mapeamentos reais do usuário por `WNetGetConnection`;
- envia testes por `\\.\LPTx`, sem passar diretamente pela fila selecionada;
- oferece comparação por impressão Win32 `RAW` direta;
- importa/edita ZPL, EPL, CPCL, ESC/POS textual e outros comandos;
- guarda configurações em `%LOCALAPPDATA%\USB-LPT-Mapper`;
- oferece reconexão, diagnóstico, logs, inicialização com o Windows e bandeja do sistema.

## Limitação técnica importante

`NET USE` cria um **redirecionamento lógico de dispositivo DOS para uma fila compartilhada**. Ele não cria uma porta paralela física, não emula registradores de hardware e não instala um driver virtual em nível de kernel.

Este aplicativo atende programas que abrem `LPT3` como arquivo/dispositivo e escrevem um fluxo de bytes. Ele não atende software que acessa diretamente endereços de E/S da porta paralela, exige interrupções/DMA, chama um driver proprietário ou roda em outro computador/usuário sem acesso ao mesmo mapeamento. Para esses casos, use uma destas arquiteturas:

- alterar a rotina para imprimir RAW pelo spooler/UNC;
- executar um agente de impressão na estação e enviar o trabalho por uma API autenticada;
- usar hardware USB–paralelo compatível com o protocolo requerido;
- contratar um driver de porta virtual assinado para Windows x64.

O aplicativo não afirma sucesso apenas porque `net use` retornou zero: ele consulta novamente o Windows. Ainda assim, a aceitação final exige a Zebra física e a rotina real do Protheus.

## Instalação para desenvolvimento

Requisitos: Windows 10/11 x64, Python 3.12+ e uma impressora instalada.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Compartilhar uma impressora normalmente requer elevação. Execute o aplicativo como administrador apenas para essa configuração se o Windows negar acesso. Crie/valide o mapeamento no contexto não elevado e no mesmo usuário do sistema legado; sessões elevadas podem ter associações de dispositivos diferentes por causa do UAC.

## Uso

1. Abra **Mapeamentos** e atualize as impressoras.
2. Selecione a impressora, confirme `LPT3`, informe um nome de compartilhamento e crie.
3. O aplicativo preservará um compartilhamento já existente.
4. Abra **Teste de impressão**, mantenha o ZPL padrão e clique em **Testar pela porta LPT**.
5. Use **Teste direto** somente como diagnóstico comparativo.
6. Consulte **Diagnóstico** e **Logs** em caso de erro.

Arquivos importados permanecem guardados como bytes e são enviados sem alteração enquanto o editor não for modificado. O editor usa UTF-8 para texto comum e Latin-1 como representação reversível de arquivos binários; depois de uma edição, a tela informa qual codificação será usada. O núcleo `RawPrinter` recebe `bytes` e não os altera.

## TOTVS Protheus: onde o mapeamento deve existir

- **SmartClient imprimindo na estação:** crie `LPT3` no usuário Windows que executa o SmartClient. É o cenário mais direto.
- **WebAgent imprimindo na estação:** crie o mapeamento no usuário que executa o WebAgent e confirme que o processo realmente abre a LPT local.
- **AppServer/serviço imprimindo no servidor:** uma LPT criada na estação não existe no servidor. O redirecionamento precisa estar na conta do serviço do AppServer, com acesso à UNC, ou a rotina deve encaminhar a impressão à estação.
- **Remote Desktop/Citrix:** dispositivos e mapeamentos variam por sessão. Valide na mesma sessão do processo de impressão.

Mapeamentos persistentes são registrados para o usuário, mas só se reconectam quando servidor, compartilhamento, spooler e credenciais/contexto estiverem disponíveis. O aplicativo não armazena credenciais.

## Segurança e rollback

- argumentos são validados e executados sem `shell=True`;
- nenhuma credencial é salva;
- impressoras e portas físicas não são removidas ou alteradas;
- compartilhamentos preexistentes são preservados;
- se um compartilhamento novo for criado e o mapeamento falhar, a aplicação tenta revertê-lo;
- a substituição de uma LPT exige confirmação;
- operações demoradas rodam fora da thread da interface;
- firewall e políticas de segurança não são desativados.

## Testes

```powershell
python -m pytest -q
```

Os testes automatizados não alteram o Windows. O roteiro que exige impressora está em `tests/physical/README.md`.

## Compilação

Execute:

```bat
build.bat
```

O script cria o ícone, executa os testes e gera `dist\USB-LPT-Mapper.exe` com PyInstaller em modo janela e arquivo único. Python não é necessário na máquina de destino. O executável não possui manifesto de elevação permanente: isso evita criar a LPT apenas na sessão administrativa. Se o spooler devolver “acesso negado”, um helper solicita UAC somente para compartilhar a impressora; o `NET USE` continua sendo executado pelo processo original no contexto do usuário do TOTVS.

## Estrutura

- `app/core`: spooler, compartilhamento, redirecionamento, RAW, permissões e diagnóstico;
- `app/services`: configuração, logs, inicialização e orquestração/rollback;
- `app/ui`: interface CustomTkinter, páginas e bandeja;
- `app/models`: modelos de impressora e mapeamento;
- `tests`: testes unitários e roteiro físico.
