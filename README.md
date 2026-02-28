<div align="center">

![EndStone-EasyLuckyPillar](https://socialify.git.ci/MengHanLOVE1027/endstone-easyluckypillar/image?custom_language=Python&description=1&font=Inter&forks=1&issues=1&language=1&logo=https://zh.minecraft.wiki/images/Bedrock_JE2_BE2.png?13f82&name=1&owner=1&pattern=Plus&pulls=1&stargazers=1&theme=Auto)

<h3>EndStone-EasyLuckyPillar</h3>

<p>
  <b>一个基于 EndStone 的幸运之柱小游戏插件 / A Lucky Pillar mini-game plugin based on EndStone.</b>

Powered by EndStone.<br>

</p>
</div>
<div align="center">

[![README](https://img.shields.io/badge/README-中文|Chinese-blue)](README.md) [![README_EN](https://img.shields.io/badge/README-英文|English-blue)](README_EN.md)

[![Github Version](https://img.shields.io/github/v/release/MengHanLOVE1027/endstone-easyluckypillar)](https://github.com/MengHanLOVE1027/endstone-easyluckypillar/releases) [![GitHub License](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0) [![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/) [![Platform](https://img.shields.io/badge/Platform-EndStone-9cf.svg)](https://endstone.io) [![Downloads](https://img.shields.io/github/downloads/MengHanLOVE1027/endstone-easyluckypillar/total.svg)](https://github.com/MengHanLOVE1027/endstone-easyluckypillar/releases)

</div>

---

## 📖 简介

EndStone-EasyLuckyPillar 是一个专为 Endstone 服务器设计的多人竞技类幸运之柱小游戏插件。玩家需要在不断缩小的边界中争夺资源，通过破坏幸运柱获取随机物品，同时躲避边界伤害，成为最后的幸存者。插件支持多场次管理、自定义物品池、粒子特效、音效系统等功能，为服务器管理员提供灵活的游戏配置选项。

---

## ✨ 核心特性

| 特性             | 描述                         |
| ---------------- | ---------------------------- |
| 🎮**多场次管理** | 支持创建和管理多个游戏场次   |
| 🏛️**幸运之柱** | 每场游戏不定数量的幸运之柱  |
| 🔥**边界缩放**   | 游戏区域逐渐缩小，增加紧张感 |
| ✨**粒子特效**   | 自定义粒子效果，增强视觉体验 |
| 🔊**音效系统**   | 边界缩小、胜利、倒计时等音效 |
| 🎁**物品池系统** | 丰富的随机掉落物品           |
| ⏱️**任务系统**   | 物品投放、事件触发等定时任务 |

---

## 🗂️ 目录结构

```
服务器根目录/
├── logs/
│   └── EasyLuckyPillar/                 # 日志目录
│       └── easyluckypillar_YYYYMMDD.log  # 主日志文件
├── plugins/
│   ├── endstone_easyluckypillar-x.x.x-py3-none-any.whl  # 插件主文件
│   └── EasyLuckyPillar/                 # 插件资源目录
│       └── config/
│           └── config.json              # 配置文件
```

---

## 🚀 快速开始

### 安装步骤

1. **下载插件**
   - 从 [Release页面](https://github.com/MengHanLOVE1027/endstone-easyluckypillar/releases) 下载最新版本
   - 或从 [MineBBS](https://www.minebbs.com/resources/easyluckypillar-elp-endstone.15496/) 获取

2. **安装插件**

   ```bash
   # 将插件主文件复制到服务器 plugins 目录
   cp endstone_easyluckypillar-x.x.x-py3-none-any.whl plugins/
   ```

3. **配置插件**
   - 编辑 `plugins/EasyLuckyPillar/config/config.json` 配置文件
   - 根据需要自定义游戏场次和物品池

4. **启动服务器**
   - 重启服务器或使用 `/reload` 命令
   - 插件会自动生成默认配置文件

---

## ⚙️ 配置详解

配置文件位于：`plugins/EasyLuckyPillar/config/config.json`

### 📋 主要配置项

```json
{
  // 🎮 游戏场次配置
  "sessions": {
    "1": {
      "name": "默认场次",
      "center_pos": { "x": 0, "y": 100, "z": 0 }, // 场次中心位置
      "pillars": {
        // 幸运柱位置配置
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
      "min_players": 2, // 最小玩家数
      "wait_area": {
        // 等待区域
        "pos1": { "x": -20, "y": 100, "z": -20 },
        "pos2": { "x": 20, "y": 100, "z": 20 }
      },
      "border": {
        // 边界配置
        "initial_radius": 20, // 初始半径
        "min_radius": 4, // 最小半径
        "shrink_interval": 300, // 缩小间隔（刻）
        "shrink_amount": 4, // 每次缩小量
        "damage_per_second": 5 // 每秒伤害
      },
      "particles": {
        // 粒子效果配置
        "enabled": true,
        "particle_type": "minecraft:falling_border_dust_particle",
        "particle_height": 10,
        "particle_y_offset": -48,
        "horizontal_step": 2,
        "vertical_step": 1,
        "view_distance": 4
      },
      "sounds": {
        // 音效配置
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
        // 任务配置
        "item_interval": 100, // 物品投放间隔（刻）
        "event_interval": 1200, // 事件触发间隔（刻）
        "border_check_interval": 20, // 边界检查间隔（刻）
        "particle_interval": 20, // 粒子更新间隔（刻）
        "scoreboard_update_interval": 20 // 计分板更新间隔（刻）
      }
    }
  },
  // 🎁 物品池配置（物品id+权重）
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

## 🎮 命令手册

### 玩家命令

| 命令                              | 描述               |
| --------------------------------- | ------------------ |
| `/lp` | 打开幸运之柱菜单 |
| `/lp menu` | 打开幸运之柱菜单 |
| `/lp leave` | 离开当前场次 |

### 管理员命令

| 命令                              | 描述               |
| --------------------------------- | ------------------ |
| `/lpadmin reload` | 重载配置文件 |
| `/lpadmin init` | 初始化配置文件 |
| `/lpadmin add <name>` | 添加新场次 |
| `/lpadmin remove <SessionID>` | 删除指定场次 |
| `/lpadmin setcenter <SessionID>` | 设置场次中心位置 |
| `/lpadmin addpillar <SessionID>` | 添加幸运柱 |
| `/lpadmin removepillar <SessionID> <PillarID>` | 删除幸运柱 |
| `/lpadmin setpillar <SessionID> <PillarID>` | 设置幸运柱位置 |
| `/lpadmin setwaitarea <SessionID>` | 设置等待区域 |
| `/lpadmin start <SessionID>` | 开始指定场次的游戏 |
| `/lpadmin stop <SessionID>` | 停止指定场次的游戏 |

---

## 🔧 高级功能

### 🎨 自定义粒子效果

粒子效果可以在配置文件中自定义，包括粒子类型、高度、偏移量等参数：

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

### 🔊 自定义音效

游戏中的各种音效可以在配置文件中自定义，包括音效类型、音量和音调：

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

### 🎁 自定义物品池

物品池可以在配置文件中自定义，包括各种物品及其出现概率：

```json
"item_pool": {
  "diamond": 10,
  "gold_ingot": 40,
  "iron_ingot": 50,
  "bread": 60
}
```

### 🔥 边界配置

边界可以在配置文件中自定义，包括初始半径、最小半径、缩小间隔等参数：

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

## 🛠️ 故障排除

### 常见问题

<details>
<summary><b>❓ 游戏无法开始</b></summary>

**检查步骤：**

1. 确认游戏场次配置正确
   ```bash
   /lp
   ```
2. 检查玩家数量是否达到最小要求
3. 查看日志文件
   ```bash
   cat logs/EasyLuckyPillar/easyluckypillar_*.log
   ```
   </details>

<details>
<summary><b>❓ 粒子效果不显示</b></summary>

**排查方法：**

1. 确认粒子效果已启用
   ```json
   "particles": {
     "enabled": true
   }
   ```
2. 检查粒子类型是否正确
3. 查看日志文件确认是否有错误
</details>

<details>
<summary><b>❓ 音效不播放</b></summary>

**排查方法：**

1. 确认音效已启用
   ```json
   "sounds": {
     "enabled": true
   }
   ```
2. 检查音效类型是否正确
3. 检查音量和音调设置
</details>

### 📊 日志文件说明

| 日志文件 | 位置                                                | 用途                       |
| -------- | --------------------------------------------------- | -------------------------- |
| 主日志   | `logs/EasyLuckyPillar/easyluckypillar_YYYYMMDD.log` | 记录游戏运行日志和错误信息 |

---

## 📄 许可证

本项目采用 **AGPL-3.0** 许可证开源。

```
版权所有 (c) 2023 梦涵LOVE

本程序是自由软件：您可以自由地重新发布和修改它，
但必须遵循AGPL-3.0许可证的条款。
```

完整许可证文本请参阅 [LICENSE](LICENSE) 文件。

---

## 👥 贡献指南

欢迎提交 Issue 和 Pull Request！

1. **Fork 项目仓库**
2. **创建功能分支**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **提交更改**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **推送分支**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **创建 Pull Request**

---

## 🌟 支持与反馈

- **GitHub Issues**: [提交问题](https://github.com/MengHanLOVE1027/endstone-easyluckypillar/issues)
- **MineBBS**: [讨论帖](https://www.minebbs.com/resources/easyluckypillar-elp-endstone.15496/)
- **作者**: 梦涵LOVE

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个 Star！**

[![Star History Chart](https://api.star-history.com/svg?repos=MengHanLOVE1027/endstone-easyluckypillar&type=Date)](https://star-history.com/#MengHanLOVE1027/endstone-easyluckypillar&Date)

</div>
