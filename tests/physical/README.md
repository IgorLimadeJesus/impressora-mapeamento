# Testes com hardware

Estes testes são manuais porque alteram o spooler, compartilhamentos e mapeamentos do usuário Windows.

1. Instale a Zebra S4M por USB e confirme que uma página RAW/ZPL direta funciona.
2. Execute o aplicativo no **mesmo usuário** do SmartClient/WebAgent.
3. Selecione a Zebra, use um nome de compartilhamento curto e crie `LPT3`.
4. Confirme com `net use LPT3:` em um terminal não elevado desse mesmo usuário.
5. Use “Testar pela porta LPT” e confirme a etiqueta impressa.
6. Reinicie o Windows, entre com o mesmo usuário e confirme o mapeamento persistente.
7. Remova `LPT3` pelo aplicativo e confirme com `net use`.

Não execute em uma máquina de produção sem janela de manutenção.
