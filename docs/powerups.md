# Power-Up System Plan

## Overview

Add 5 power-up types that spawn randomly on the field. Players pick them up by walking over them. Each power-up lasts 10 seconds. No stacking - picking up a new power-up replaces the current one.

## Power-Up Types

| Type | Color | Label | Effect |
|------|-------|-------|--------|
| Shield | Cyan | S | Reflects bullets back at shooter |
| Rapid Fire | Orange | R | No shooting cooldown |
| Shotgun | Purple | G | 3 bullets in spread pattern |
| Speed Boost | Yellow | B | 2x movement speed |
| Big Bullet | Pink | X | 2x bullet size |

## Implementation Details

### 1. New `PowerUp` class
- Properties: `x`, `y`, `type`, `color`, `label`
- Random spawn anywhere on screen (with margin from edges)
- Drawn as 30x30 colored square with letter
- Despawns after 10 seconds if not picked up

### 2. Update `Player` class
- Add `active_powerup = None`
- Add `powerup_end_time = 0`
- Visual: Cyan ring around player when Shield active

### 3. Spawning
- One power-up on screen at a time
- Spawns every 5-8 seconds (random interval)
- Random type each spawn

### 4. Pickup
- Player collides with power-up → replaces current power-up, resets timer
- No stacking (new power-up overwrites old)

### 5. Effect Implementations

| Power-Up | Implementation |
|----------|----------------|
| Shield | On bullet hit: reverse `vx`/`vy`, swap owner, don't damage player |
| Rapid Fire | Remove 0.3s cooldown between shots |
| Shotgun | Fire 3 bullets at -15°, 0°, +15° from mouse direction |
| Speed Boost | Temporarily set `player.speed = 10` (normally 5) |
| Big Bullet | Create bullet with `radius = 10` (normally 5) |

### 6. HUD
- Bottom of screen: `[S] Shield: 7s` (if active)

### 7. Multiplayer Sync
- Host spawns/manages power-ups
- Game state includes: `powerups` list, player `active_powerup` + `powerup_end_time`
- Client renders based on received state

## Estimated Changes

| Area | Lines |
|------|-------|
| PowerUp class | ~30 |
| Player class updates | ~15 |
| Spawning logic | ~20 |
| Effect logic (bullets, speed, etc.) | ~40 |
| HUD rendering | ~10 |
| Network sync | ~20 |
| **Total** | **~135** |
