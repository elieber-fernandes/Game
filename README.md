Brincando com Python e Pygame.


# Space Journey

Um jogo de nave espacial feito em Python com Pygame, onde você controla uma nave, desvia de meteoros, enfrenta inimigos e compete por pontuações no ranking online.

## Tecnologias Utilizadas

- **Python 3.8+**
- **[Pygame](https://www.pygame.org/):** Biblioteca para desenvolvimento de jogos 2D em Python.
- **[Asyncio](https://docs.python.org/3/library/asyncio.html):** Para controle de fluxos assíncronos, especialmente para integração com Firebase e telas.
- **[httpx](https://www.python-httpx.org/):** Cliente HTTP assíncrono para comunicação com o Firebase (usado fora do navegador).
- **Firebase Realtime Database:** Armazenamento e consulta de pontuações online.
- **PyGBag:** Suporte experimental para rodar o jogo no navegador (WebAssembly).

## Recursos do Projeto

- **Movimentação suave da nave** com física de aceleração, rotação e drift.
- **Tiro e colisão:** Atire em inimigos e meteoros, com detecção de colisão precisa.
- **Inimigos normais e atiradores:** Inimigos com IA simples e inimigos que atiram no jogador.
- **Meteoros:** Obstáculos aleatórios que cruzam a tela.
- **Explosões animadas** ao destruir inimigos ou meteoros.
- **Barra de vida e placar** na tela.
- **Ranking online:** Top 10 pontuações salvas e exibidas via integração com Firebase.
- **Tela de Game Over** com opção de reiniciar ou ver o ranking.
- **Recursos gráficos e sonoros:** Imagens e sons customizados para nave, inimigos, meteoros, tiros e explosões.
- **Compatível com Web (PyGBag):** Pode ser exportado para rodar no navegador.

## Estrutura de Pastas

```
.
├── main.py
├── assets/
│   ├── back.png
│   ├── Ship_2.png
│   ├── polvo.png
│   ├── polvo2.png
│   ├── shooter_1.png
│   ├── shooter_2.png
│   ├── meteor_img1.png
│   ├── meteor_img2.png
│   ├── meteor_img3.png
│   ├── shoot.ogg
│   ├── explosion.ogg
│   └── ship_moving.ogg
```

## Como Rodar

1. **Instale as dependências:**
   ```bash
   pip install pygame httpx
   ```

2. **Execute o jogo:**
   ```bash
   python main.py
   ```

3. **Controles:**
   - **Setas ou WASD:** Movimentar a nave
   - **Espaço:** Atirar
   - **ESC:** Sair
   - **ENTER:** Reiniciar após Game Over
   - **R:** Reiniciar a qualquer momento

## Ranking Online

- O jogo salva e busca as pontuações no Firebase.
- Ao atingir o Game Over, digite suas iniciais para registrar sua pontuação.
- Veja o Top 10 acessando o ranking na tela de Game Over.

## Créditos

- **Desenvolvimento:** [Elieber Fernandes Martins]
- **Imagens e sons:** Recursos próprios ou de domínio público.
- **Ranking:** Firebase Realtime Database

---

Sinta-se à vontade para contribuir, sugerir melhorias ou reportar bugs!




https://elieber.itch.io/spacejourney
