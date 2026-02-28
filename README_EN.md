<div align="center">

![EndStone-EasyLuckyPillar](https://socialify.git.ci/MengHanLOVE1027/endstone-easyluckypillar/image?custom_language=Python&description=1&font=Inter&forks=1&issues=1&language=1&logo=https://zh.minecraft.wiki/images/Bedrock_JE2_BE2.png?13f82&name=1&owner=1&pattern=Plus&pulls=1&stargazers=1&theme=Auto)

<h3>EndStone-EasyLuckyPillar</h3>

<p>
  <b>A Lucky Pillar mini-game plugin based on EndStone.</b>

Powered by EndStone.<br>

</p>
</div>
<div align="center">

[![README](https://img.shields.io/badge/README-中文|Chinese-blue)](README.md) [![README_EN](https://img.shields.io/badge/README-英文|English-blue)](README_EN.md)

[![Github Version](https://img.shields.io/github/v/release/MengHanLOVE1027/endstone-easyluckypillar)](https://github.com/MengHanLOVE1027/endstone-easyluckypillar/releases) [![GitHub License](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0) [![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/) [![Platform](https://img.shields.io/badge/Platform-EndStone-9cf.svg)](https://endstone.io) [![Downloads](https://img.shields.io/github/downloads/MengHanLOVE1027/endstone-easyluckypillar/total.svg)](https://github.com/MengHanLOVE1027/endstone-easyluckypillar/releases)

</div>

---

## 📖 Introduction

EndStone-EasyLuckyPillar is a multiplayer competitive Lucky Pillar mini-game plugin designed for EndStone servers. Players need to compete for resources in a constantly shrinking border, obtain random items by destroying lucky pillars, and avoid border damage to become the last survivor. The plugin supports multi-session management, custom item pools, particle effects, sound systems, and other features, providing flexible game configuration options for server administrators.

---

## ✨ Core Features

| Feature              | Description                              |
| ----------------- | ---------------------------------------- |
| 🎮**Multi-Session Management** | Support creating and managing multiple game sessions |
| 🏛️**Lucky Pillar System** | Multiple lucky pillars per game |
| 🔥**Border Shrinking** | Game area gradually shrinks, increasing tension |
| ✨**Particle Effects** | Customizable particle effects to enhance visual experience |
| 🔊**Sound System** | Border shrinking, victory, countdown and other sound effects |
| 🎁**Item Pool System** | Rich random drop items |
| ⏱️**Task System** | Timed tasks for item spawning, event triggering, etc. |
| 📊**Scoreboard System** | Real-time player score updates |

---

## 🗂️ Directory Structure

```
Server Root/
├── logs/
│   └── EasyLuckyPillar/                 # Log directory
│       └── easyluckypillar_YYYYMMDD.log  # Main log file
├── plugins/
│   ├── endstone_easyluckypillar-x.x.x-py3-none-any.whl  # Plugin main file
│   └── EasyLuckyPillar/                 # Plugin resource directory
│       └── config/
│           └── config.json              # Configuration file
```

---

## 🚀 Quick Start

### Installation Steps

1. **Download Plugin**
   - Download the latest version from [Release page](https://github.com/MengHanLOVE1027/endstone-easyluckypillar/releases)
   - Or get it from [MineBBS](https://www.minebbs.com/resources/easyluckypillar-elp-endstone.15496/)

2. **Install Plugin**
   ```bash
   # Copy plugin main file to server plugins directory
   cp endstone_easyluckypillar-x.x.x-py3-none-any.whl plugins/
   ```

3. **Configure Plugin**
   - Edit `plugins/EasyLuckyPillar/config/config.json` configuration file
   - Customize game sessions and item pool as needed

4. **Start Server**
   - Restart server or use `/reload` command
   - Plugin will automatically generate default configuration file

---

## ⚙️ Configuration Details

Configuration file location: `plugins/EasyLuckyPillar/config/config.json`

### 📋 Main Configuration Items

```json
{
  // 🎮 Game Session Configuration
  "sessions": {
    "1": {
      "name": "Default Session",
      "center_pos": { "x": 0, "y": 100, "z": 0 }, // Session center position
      "pillars": {
        // Lucky pillar position configuration
        "1": { "x": 0, "y": 99, "z": 0 },
        "2": { "x": 0, "y": 99, "z": -16 },
        "3": { "x": 16, "y": 99, "z": 0 },
        "4": { "x": 0, "y": 99, "z": 16 },
        "5": { "x": -16, "y": 99, "z": 0 },
        "6": { "x": -11, "y": 99, "z": -11 },
        "7": { "x": 11, "y": 99, "z": -11 },
        "8": { "x": -11, "y": 99, "z": 11 },
        "9": { "x": 11, "y": 99, "z": 11 }
      },
      "min_players": 2, // Minimum player count
      "wait_area": {
        // Waiting area
        "pos1": { "x": -20, "y": 100, "z": -20 },
        "pos2": { "x": 20, "y": 100, "z": 20 }
      },
      "border": {
        // Border configuration
        "initial_radius": 20, // Initial radius
        "min_radius": 4, // Minimum radius
        "shrink_interval": 300, // Shrink interval (ticks)
        "shrink_amount": 4, // Shrink amount per time
        "damage_per_second": 5 // Damage per second
      },
      "particles": {
        // Particle effect configuration
        "enabled": true,
        "particle_type": "minecraft:falling_border_dust_particle",
        "particle_height": 10,
        "particle_y_offset": -48,
        "horizontal_step": 2,
        "vertical_step": 1,
        "view_distance": 4
      },
      "sounds": {
        // Sound effect configuration
        "enabled": true,
        "border_shrink_sound": "random.explode",
        "border_shrink_volume": 10.0,
        "border_shrink_pitch": 1.0,
        "victory_sound": "mob.enderdragon.death",
        "victory_volume": 10.0,
        "victory_pitch": 1.0,
        "countdown_sound": "random.orb",
        "countdown_volume": 10.0,
        "game_end_sound": "mob.wither.death",
        "game_end_volume": 10.0,
        "game_end_pitch": 1.0
      },
      "tasks": {
        // Task configuration
        "item_interval": 100, // Item spawn interval (ticks)
        "event_interval": 1200, // Event trigger interval (ticks)
        "border_check_interval": 20, // Border check interval (ticks)
        "particle_interval": 20, // Particle update interval (ticks)
        "scoreboard_update_interval": 20 // Scoreboard update interval (ticks)
      }
    }
  },
  // 🎁 Item Pool Configuration (item id + weight)
  "item_pool": {
    "cobblestone": 100,
    "dirt": 100,
    "sand": 80,
    "gravel": 80,
    "planks": 100,
    "log": 80,
    "glass": 60,
    "wool": 60,
    "stone": 80,
    "andesite": 70,
    "diorite": 70,
    "granite": 70
  }
}
```

---

## 🎮 Command Manual

### Player Commands

| Command                              | Description               |
| --------------------------------- | ------------------ |
| `/lp` | Open Lucky Pillar menu |
| `/lp menu` | Open Lucky Pillar menu |
| `/lp leave` | Leave current session |

### Admin Commands

| Command                              | Description               |
| --------------------------------- | ------------------ |
| `/lpadmin reload` | Reload configuration file |
| `/lpadmin init` | Initialize configuration file |
| `/lpadmin add <name>` | Add new session |
| `/lpadmin remove <SessionID>` | Remove specified session |
| `/lpadmin setcenter <SessionID>` | Set session center position |
| `/lpadmin addpillar <SessionID>` | Add lucky pillar |
| `/lpadmin removepillar <SessionID> <PillarID>` | Remove lucky pillar |
| `/lpadmin setpillar <SessionID> <PillarID>` | Set lucky pillar position |
| `/lpadmin setwaitarea <SessionID>` | Set waiting area |
| `/lpadmin start <SessionID>` | Start specified session game |
| `/lpadmin stop <SessionID>` | Stop specified session game |

---

## 🔧 Advanced Features

### 🎨 Custom Particle Effects

Particle effects can be customized in the configuration file, including particle type, height, offset and other parameters:

```json
"particles": {
  "enabled": true,
  "particle_type": "minecraft:falling_border_dust_particle",
  "particle_height": 10,
  "particle_y_offset": -48,
  "horizontal_step": 2,
  "vertical_step": 1,
  "view_distance": 4
}
```

### 🔊 Custom Sound Effects

Various sound effects in the game can be customized in the configuration file, including sound type, volume and pitch:

```json
"sounds": {
  "enabled": true,
  "border_shrink_sound": "random.explode",
  "border_shrink_volume": 10.0,
  "border_shrink_pitch": 1.0,
  "victory_sound": "mob.enderdragon.death",
  "victory_volume": 10.0,
  "victory_pitch": 1.0,
  "countdown_sound": "random.orb",
  "countdown_volume": 10.0,
  "game_end_sound": "mob.wither.death",
  "game_end_volume": 10.0,
  "game_end_pitch": 1.0
}
```

### 🎁 Custom Item Pool

Item pool can be customized in the configuration file, including various items and their spawn probabilities:

```json
"item_pool": {
  "diamond": 10,
  "gold_ingot": 40,
  "iron_ingot": 50,
  "bread": 60
}
```

### 🔥 Border Configuration

Border can be customized in the configuration file, including initial radius, minimum radius, shrink interval and other parameters:

```json
"border": {
  "initial_radius": 20,
  "min_radius": 4,
  "shrink_interval": 300,
  "shrink_amount": 4,
  "damage_per_second": 5
}
```

---

## 🛠️ Troubleshooting

### Common Issues

<details>
<summary><b>❓ Game cannot start</b></summary>

**Check Steps:**

1. Confirm game session configuration is correct
   ```bash
   /lp
   ```
2. Check if player count meets minimum requirement
3. View log file
   ```bash
   cat logs/EasyLuckyPillar/easyluckypillar_*.log
   ```
</details>

<details>
<summary><b>❓ Particle effects not displaying</b></summary>

**Troubleshooting:**

1. Confirm particle effects are enabled
   ```json
   "particles": {
     "enabled": true
   }
   ```
2. Check if particle type is correct
3. View log file to confirm if there are any errors
</details>

<details>
<summary><b>❓ Sound effects not playing</b></summary>

**Troubleshooting:**

1. Confirm sound effects are enabled
   ```json
   "sounds": {
     "enabled": true
   }
   ```
2. Check if sound type is correct
3. Check volume and pitch settings
</details>

### 📊 Log File Description

| Log File | Location                                                | Purpose                       |
| -------- | --------------------------------------------------- | -------------------------- |
| Main Log   | `logs/EasyLuckyPillar/easyluckypillar_YYYYMMDD.log`  | Record game running logs and error information |

---

## 📄 License

This project is open source under **AGPL-3.0** license.

```
Copyright (c) 2023 梦涵LOVE

This program is free software: you can freely redistribute and modify it,
but must follow the terms of the AGPL-3.0 license.
```

For the full license text, please refer to the [LICENSE](LICENSE) file.

---

## 👥 Contributing Guide

Issues and Pull Requests are welcome!

1. **Fork Project Repository**
2. **Create Feature Branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit Changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push Branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Create Pull Request**

---

## 🌟 Support & Feedback

- **GitHub Issues**: [Submit Issues](https://github.com/MengHanLOVE1027/endstone-easyluckypillar/issues)
- **MineBBS**: [Discussion Thread](https://www.minebbs.com/resources/easyluckypillar-elp-endstone.15496/)
- **Author**: 梦涵LOVE

---

<div align="center">

**⭐ If this project helps you, please give us a Star!**

[![Star History Chart](https://api.star-history.com/svg?repos=MengHanLOVE1027/endstone-easyluckypillar&type=Date)](https://star-history.com/#MengHanLOVE1027/endstone-easyluckypillar&Date)
