# Prototype history and credits

System Panic began with a functional Pak implementation in 2017 and an unfinished class-based rewrite in May 2025. The current game is a fresh implementation under `src/system_panic`, with external content under `paks/`.

The obsolete prototypes and their unused artwork, music and font were removed from the working tree on 2026-10-25. Their code, media, original documentation and license files remain in Git history under `legacy/`, including commit `fa0ba575e4ad7774a4576695ade1d91633a212d4`. To inspect the old tree without changing the checkout:

```sh
git ls-tree -r fa0ba575e4ad7774a4576695ade1d91633a212d4 legacy/
git show fa0ba575e4ad7774a4576695ade1d91633a212d4:legacy/README.md
```

The following attributions are preserved from that README. They describe historical assets; the current game uses the original generated assets recorded in [the asset manifest](../assets/manifest.json).

## May 2025 rewrite credits

### Enemies

- slime_enemy: patvanmackelberg, license: CC0, sliced from [Slime 2 Frame Animation 32x32](http://opengameart.org/content/slime-2-frame-animation-32x32).
- bat_enemy: AntumDeluge, license: CC-BY 3.0, sliced from [Bat Rework](https://opengameart.org/content/bat-rework).

### Players

- mage_player missile: Master484, license: CC0, sliced from [Bullet Collection 2](http://opengameart.org/content/bullet-collection-2-m484-games).

### Platforms

- brick_platform: Nimnon, license: CC0, sliced from [Blue Brick Tileset](https://opengameart.org/content/blue-brick-tileset).
- grass_platform: Redfill Production, license: CC-BY-SA 4.0, sliced from [Grass and Dirt Sprite Sheet](https://opengameart.org/content/grass-and-dirt-sprite-sheet).

## 2017 implementation credits

### Music

- BGM_Alpha, BGM_Delta, BGM_Omega and BGM_Menu: CodeManu, license: CC0, [The Slimeking's Tower OST](http://opengameart.org/content/the-slimekings-tower-ost-retro-like), converted to Ogg.

### Players

- ExamplePlayer1 spritesheet: pondomaniac, license: CC0, [Hero](http://opengameart.org/content/hero-0).
- ExamplePlayer2 spritesheet: eracoon, license: CC0, [Isometric Vehicles](http://opengameart.org/content/isometric-vehicles).
- ExamplePlayer3 spritesheet: Disthron, license: CC0, [Mr Knife Guy Animated](http://opengameart.org/content/mr-knife-guy-animated).

### Enemies

- ExampleEnemy1 spritesheet: patvanmackelberg, license: CC0, [Slime 2 Frame Animation 32x32](http://opengameart.org/content/slime-2-frame-animation-32x32).
- ExampleEnemy2 spritesheet: scx, license: CC0, [Monsters](http://opengameart.org/content/monsters-2).

### Missiles

- ExampleMissile 1 and ExampleMissile 2 spritesheets: Master484, license: CC0, sliced from [Bullet Collection 2](http://opengameart.org/content/bullet-collection-2-m484-games).

### Level tiles

- ExampleLevelTiles1 spritesheet: GrumpyDiamond, license: CC0, [Seamless Wall](http://opengameart.org/content/seamless-wall).

### Fonts

- Press Start 2P: Copyright 2012 The Press Start 2P Project Authors (cody@zone38.net), license: OFL. The original license file remains alongside the font in Git history.

### Sound

- Glitch: HarleyGlitch, license: CC-BY-3.0, [Freesound 332711](https://freesound.org/people/HarleyGlitch/sounds/332711/), converted to Ogg.
- Glitch-9: HarleyGlitch, license: CC-BY-3.0, [Freesound 333982](https://freesound.org/people/HarleyGlitch/sounds/333982/), converted to Ogg.
