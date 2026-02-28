# python 库
import os, math, logging, random, json
from datetime import datetime
from pathlib import Path
from threading import Lock
from enum import Enum

# endstone 库
from endstone import Player, GameMode
from endstone.level import Location
from endstone.plugin import Plugin
from endstone.command import Command, CommandSender
from endstone.form import ActionForm
from endstone.boss import BarColor, BarStyle
from endstone.event import event_handler, PlayerDeathEvent, PlayerQuitEvent
from endstone.inventory import ItemStack
from endstone.scoreboard import Criteria, DisplaySlot

# Easy系列插件的 BStats 遥测模块
from .bstats import BStats

# 游戏状态枚举
class GameState(Enum):
    IDLE = "idle"  # 空闲状态
    WAITING = "waiting"  # 等待玩家加入
    READY = "ready"  # 人数已满，等待管理员开始
    COUNTDOWN = "countdown"  # 传送后倒计时中
    RUNNING = "running"  # 游戏进行中
    ENDED = "ended"  # 游戏已结束

# 插件全局常量
plugin_name = "EasyLuckyPillar"
plugin_name_smallest = "easyluckypillar"
plugin_description = "一个基于 EndStone 的幸运之柱小游戏插件 / A Lucky Pillar mini-game plugin based on EndStone."
plugin_version = "0.1.1"
plugin_author = ["梦涵LOVE"]
plugin_license = "AGPL-3.0"
plugin_github_link = "https://github.com/MengHanLOVE1027/endstone-easyluckypillar"
plugin_minebbs_link = "https://www.minebbs.com/resources/easyluckypillar-elp-endstone.15496/"

plugin_path = Path(f"./plugins/{plugin_name}")
plugin_config_path = plugin_path / "config" / "EasyLuckyPillar.json"

print_lock = Lock()  # 用于线程安全的日志输出

# --- 随机颜色系统 ---
GLOBAL_C1 = None
GLOBAL_C2 = None

def randomVividColor():
    """生成一个鲜艳的随机颜色"""
    rand = random.random() * 260
    if rand < 90:
        h = rand
    elif rand < 200:
        h = rand + 60
    else:
        h = rand + 100
    s = 0.90 + random.random() * 0.10
    l = 0.65 + random.random() * 0.15
    a = s * min(l, 1 - l)
    def f(n):
        k = (n + h / 30) % 12
        return round((l - a * max(-1, min(k - 3, 9 - k, 1))) * 255)
    return [f(0), f(8), f(4)]

def generateColorPair():
    """生成一对颜色"""
    c1 = randomVividColor()
    c2, attempts = 0, 0
    while True:
        c2 = randomVividColor()
        diff = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1]) + abs(c1[2] - c2[2])
        if diff > 150 or attempts > 20:
            break
        attempts += 1
    return [c1, c2]

GLOBAL_C1, GLOBAL_C2 = generateColorPair()

def globalLerpColor(t):
    """在全局颜色对之间进行线性插值"""
    return [
        round(GLOBAL_C1[0] + (GLOBAL_C2[0] - GLOBAL_C1[0]) * t),
        round(GLOBAL_C1[1] + (GLOBAL_C2[1] - GLOBAL_C1[1]) * t),
        round(GLOBAL_C1[2] + (GLOBAL_C2[2] - GLOBAL_C1[2]) * t)
    ]

def randomGradientColor(text):
    """生成随机渐变色文本"""
    lenth = len(text)
    out = ''
    for i in range(lenth):
        t = 0 if lenth <= 1 else i / (lenth - 1)
        r, g, b = globalLerpColor(t)
        out += f"\x1b[38;2;{r};{g};{b}m{text[i]}"
    return out + "\x1b[0m"

class RandomColor:
    """随机颜色类，用于生成随机渐变色文本"""
    def __init__(self, text):
        self.text = text
    def __str__(self):
        return randomGradientColor(self.text)

# TAG: 日志系统设置
log_dir = Path(f"./logs/{plugin_name_smallest}")
if not log_dir.exists():
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[{plugin_name}] 创建日志目录失败: {e}")

log_file = log_dir / f"{plugin_name_smallest}_{datetime.now().strftime('%Y%m%d')}.log"
logger = logging.getLogger(plugin_name)
logger.setLevel(logging.DEBUG)

try:
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"[{plugin_name}] 配置日志文件处理器失败: {e}")

def plugin_print(text, level="INFO") -> bool:
    level_colors = {
        "DEBUG": "\x1b[36m", "INFO": "\x1b[37m", "WARNING": "\x1b[33m",
        "ERROR": "\x1b[31m", "SUCCESS": "\x1b[32m"
    }
    level_color = level_colors.get(level, "\x1b[37m")
    logger_head = f"[\x1b[96m{plugin_name}\x1b[0m] [{level_color}{level}\x1b[0m] "
    with print_lock:
        print(logger_head + str(RandomColor(text)))
    log_level_map = {
        "DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING,
        "ERROR": logging.ERROR, "SUCCESS": logging.INFO
    }
    log_level = log_level_map.get(level, logging.INFO)
    logger.log(log_level, str(text))
    return True

# TAG: 插件入口点
class EasyLuckyPillarPlugin(Plugin):
    api_version = "0.5"
    name = plugin_name_smallest
    description = plugin_description
    version = plugin_version
    authors = plugin_author

    commands = {
        "lp": {
            "description": "幸运之柱",
            "usages": ["/lp", "/lp menu", "/lp leave"],
            "permissions": ["easyluckypillar.command.use"],
        },
        "lpadmin": {
            "description": "幸运之柱管理",
            "usages": [
                "/lpadmin reload", "/lpadmin init", "/lpadmin add <name: str>", "/lpadmin remove <SessionID: int>",
                "/lpadmin setcenter <SessionID: int>", "/lpadmin addpillar <SessionID: int>",
                "/lpadmin removepillar <SessionID: int> <PillarID: int>",
                "/lpadmin setpillar <SessionID: int> <PillarID: int>",
                "/lpadmin setwaitarea <SessionID: int>",
                "/lpadmin start <SessionID: int>", "/lpadmin stop <SessionID: int>"
            ],
            "permissions": ["easyluckypillar.opcommand.use"],
        }
    }

    permissions = {
        "easyluckypillar.command.use": {"description": "允许使用幸运之柱命令", "default": True},
        "easyluckypillar.opcommand.use": {"description": "允许使用幸运之柱管理命令", "default": "op"}
    }

    def __init__(self):
        super().__init__()
        self.plugin_config = {"sessions": {}}
        self.game_sessions = {}  # 运行时场次数据
        self.player_session = {} # 玩家当前所在场次
        
        # 加权物品池 (物品名: 权重)
        self.weighted_item_pool = {
            # 原列表中的物品
            "cobblestone": 100, "dirt": 100, "sand": 80, "gravel": 80, "planks": 100, "log": 80,
            "glass": 60, "wool": 60, "stone": 80, "andesite": 70, "diorite": 70, "granite": 70,
            "deepslate": 70, "tuff": 60, "moss_block": 50, "mud": 60,
            "iron_ingot": 50, "gold_ingot": 40, "coal": 60, "copper_ingot": 50, "redstone": 40,
            "lapis_lazuli": 30, "emerald": 20, "diamond": 10, "netherite_ingot": 2,
            "bread": 60, "cooked_beef": 50, "apple": 60, "carrot": 60, "potato": 60,
            "golden_apple": 10, "enchanted_golden_apple": 1,
            "bow": 30, "arrow": 50, "crossbow": 20, "iron_sword": 30, "diamond_sword": 5,
            "iron_pickaxe": 30, "diamond_pickaxe": 5, "shield": 20, "totem_of_undying": 2,
            "trident": 3, "spyglass": 10, "fishing_rod": 20, "snowball": 40, "egg": 40,
            "iron_helmet": 15, "iron_chestplate": 10, "iron_leggings": 15, "iron_boots": 15,
            "diamond_helmet": 3, "diamond_chestplate": 2, "diamond_leggings": 3, "diamond_boots": 3,
            "tnt": 25, "ender_pearl": 15, "bucket": 30, "water_bucket": 20, "lava_bucket": 15,
            "firework_rocket": 20, "slime_ball": 20, "magma_cream": 15, "obsidian": 10,

            # 补充：各色羊毛（类似 wool 权重60）
            "white_wool": 60, "orange_wool": 60, "magenta_wool": 60, "light_blue_wool": 60,
            "yellow_wool": 60, "lime_wool": 60, "pink_wool": 60, "gray_wool": 60,
            "light_gray_wool": 60, "cyan_wool": 60, "purple_wool": 60, "blue_wool": 60,
            "brown_wool": 60, "green_wool": 60, "red_wool": 60, "black_wool": 60,

            # 补充：各色混凝土（权重70）
            "white_concrete": 70, "orange_concrete": 70, "magenta_concrete": 70, "light_blue_concrete": 70,
            "yellow_concrete": 70, "lime_concrete": 70, "pink_concrete": 70, "gray_concrete": 70,
            "light_gray_concrete": 70, "cyan_concrete": 70, "purple_concrete": 70, "blue_concrete": 70,
            "brown_concrete": 70, "green_concrete": 70, "red_concrete": 70, "black_concrete": 70,

            # 补充：各色玻璃（类似 glass 权重60）
            "white_stained_glass": 60, "orange_stained_glass": 60, "magenta_stained_glass": 60,
            "light_blue_stained_glass": 60, "yellow_stained_glass": 60, "lime_stained_glass": 60,
            "pink_stained_glass": 60, "gray_stained_glass": 60, "light_gray_stained_glass": 60,
            "cyan_stained_glass": 60, "purple_stained_glass": 60, "blue_stained_glass": 60,
            "brown_stained_glass": 60, "green_stained_glass": 60, "red_stained_glass": 60,
            "black_stained_glass": 60,

            # 补充：其他木头种类（类似 log 权重80）
            "spruce_log": 80, "birch_log": 80, "jungle_log": 80, "acacia_log": 80,
            "dark_oak_log": 80, "mangrove_log": 80, "cherry_log": 80,

            # 补充：石质建材
            "end_stone": 60, "prismarine": 60, "purpur_block": 60,
            "bookshelf": 50, "clay": 60, "honeycomb_block": 40, "hay_block": 50,

            # 补充：更多工具/武器/盔甲（按材质分级）
            "wooden_sword": 20, "stone_sword": 30, "golden_sword": 25,
            "wooden_pickaxe": 20, "stone_pickaxe": 30, "golden_pickaxe": 25,
            "wooden_axe": 20, "stone_axe": 30, "golden_axe": 25,
            "wooden_shovel": 20, "stone_shovel": 30, "golden_shovel": 25,
            "wooden_hoe": 20, "stone_hoe": 30, "golden_hoe": 25,
            "leather_helmet": 15, "leather_chestplate": 10, "leather_leggings": 15, "leather_boots": 15,
            "golden_helmet": 12, "golden_chestplate": 8, "golden_leggings": 12, "golden_boots": 12,
            "chainmail_helmet": 10, "chainmail_chestplate": 8, "chainmail_leggings": 10, "chainmail_boots": 10,

            # 补充：特殊工具与杂项
            "flint_and_steel": 25, "compass": 20, "clock": 20, "map": 15,
            "shears": 25, "lead": 15, "name_tag": 10,
            "splash_potion": 15, "lingering_potion": 10,

            # 补充：更多食物
            "cake": 30, "cookie": 40, "pumpkin_pie": 40, "cooked_cod": 50,
            "cooked_salmon": 50, "golden_carrot": 15,

            # 补充：稀有掉落与材料
            "blaze_rod": 15, "ghast_tear": 8, "turtle_helmet": 5,
            "netherite_upgrade_smithing_template": 1,
            "music_disc_13": 2, "music_disc_cat": 2
        }

    def on_load(self):
        print(RandomColor("███████╗ █████╗ ███████╗██╗   ██╗██╗     ██╗   ██╗ ██████╗██╗  ██╗██╗   ██╗██████╗ ██╗██╗     ██╗      █████╗ ██████╗ "))
        print(RandomColor("██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝██║     ██║   ██║██╔════╝██║ ██╔╝╚██╗ ██╔╝██╔══██╗██║██║     ██║     ██╔══██╗██╔══██╗"))
        print(RandomColor("█████╗  ███████║███████╗ ╚████╔╝ ██║     ██║   ██║██║     █████╔╝  ╚████╔╝ ██████╔╝██║██║     ██║     ███████║██████╔╝"))
        print(RandomColor("██╔══╝  ██╔══██║╚════██║  ╚██╔╝  ██║     ██║   ██║██║     ██╔═██╗   ╚██╔╝  ██╔═══╝ ██║██║     ██║     ██╔══██║██╔══██╗"))
        print(RandomColor("███████╗██║  ██║███████║   ██║   ███████╗╚██████╔╝╚██████╗██║  ██╗   ██║   ██║     ██║███████╗███████╗██║  ██║██║  ██║"))
        print(RandomColor("╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝"))
        print(RandomColor(f"""                                       作者：{plugin_author[0]}               版本：{plugin_version}"""))
        plugin_print(f"="*80, "INFO")
        plugin_print(f"{plugin_name} - {plugin_description}")
        plugin_print(f"感谢您使用Easy系列插件！")
        plugin_print(f"本插件使用 {plugin_license} 许可证协议进行发布")
        plugin_print(f"插件GitHub项目仓库地址：{plugin_github_link}")
        plugin_print(f"插件MineBBS资源帖：{plugin_minebbs_link}")
        plugin_print(f"Easy系列插件交流群：1083195477")
        plugin_print(f"作者：{plugin_author[0]} | 版本：{plugin_version}")
        plugin_print(f"="*80, "INFO")
        
        plugin_print(f"{plugin_name} 已加载", "INFO")

    def on_enable(self):
        # bStats统计功能
        plugin_id = 29829
        self._metrics = BStats(self, plugin_id)
        self._metrics.start()  # 启动定时提交任务
        
        self.load_config()
        self.register_events(self)
        # 确保 sessions 键存在
        if "sessions" not in self.plugin_config:
            self.plugin_config["sessions"] = {}
            self.save_config()
            
        for sid in self.plugin_config.get("sessions", {}):
            self.init_session_runtime(sid)
            
        # 自动设置游戏规则：立即重生
        self.server.dispatch_command(self.server.command_sender, "gamerule doimmediaterespawn true")
        
        # 启动定时任务，每秒检查一次玩家位置
        self.server.scheduler.run_task(self, self.check_players_position, delay=20, period=20)

        plugin_print(f"{plugin_name} 已启用", "INFO")
        
    def on_disable(self) -> None: 
        self._metrics.shutdown() # 关闭bStats统计
        plugin_print(f"{plugin_name} 已禁用", "INFO")

    def check_players_position(self):
        """定期检查所有在线玩家的位置，自动加入或离开场次"""
        for player in self.server.online_players:
            # 检查玩家是否已经在某个场次中
            if player.name in self.player_session:
                current_session = self.player_session[player.name]
                runtime = self.game_sessions.get(current_session, {"state": GameState.IDLE})

                # 如果游戏正在进行中、倒计时中，不检查玩家位置
                if runtime["state"] in [GameState.RUNNING, GameState.COUNTDOWN]:
                    continue

                # 检查玩家是否还在当前场次的准备区域内
                in_wait_area = self.is_player_in_wait_area(player, current_session)
                if not in_wait_area:
                    # 玩家离开了准备区域，自动离开游戏
                    player.send_message("§c你离开了准备区域，已自动退出游戏！")
                    self.leave_game(player, silent=True)
            else:
                # 玩家不在任何场次中，检查是否进入了某个场次的准备区域
                for sid in self.plugin_config.get("sessions", {}):
                    runtime = self.game_sessions.get(sid, {"state": GameState.IDLE})
                    # 在空闲状态、等待状态或准备就绪状态下允许玩家自动加入
                    if runtime["state"] in [GameState.IDLE, GameState.WAITING, GameState.READY] and self.is_player_in_wait_area(player, sid):
                        # 玩家进入了准备区域，自动加入游戏
                        self.join_game(player, sid)
                        break

        # 检查是否有场次的所有玩家都在准备区域内，如果是，则播放胜利音效
        self.check_all_players_in_wait_area()

        # 检查是否有离线玩家还在场次中，如果有则移除
        self.remove_offline_players()

    def remove_offline_players(self):
        """检查是否有离线玩家还在场次中，如果有则移除"""
        for session_id, runtime in self.game_sessions.items():
            players_to_remove = []

            for player in runtime["players"]:
                # 检查玩家是否在线
                if player not in self.server.online_players:
                    # 玩家离线，记录需要移除的玩家
                    if player.name in self.player_session and self.player_session[player.name] == session_id:
                        players_to_remove.append(player)

            # 移除离线玩家
            for player in players_to_remove:
                if player in runtime["players"]:
                    runtime["players"].remove(player)
                if player.name in runtime["alive_players"]:
                    runtime["alive_players"].remove(player.name)
                if player.name in self.player_session:
                    del self.player_session[player.name]

            # 如果有玩家被移除，更新bossbar和scoreboard
            if players_to_remove:
                self.update_bossbar(session_id)
                self.update_scoreboard(session_id)

    def check_all_players_in_wait_area(self):
        """检查是否有场次的所有玩家都在准备区域内，如果是，则播放胜利音效"""
        for sid, runtime in self.game_sessions.items():
            # 只检查空闲状态、等待状态和准备就绪状态的场次
            if runtime["state"] not in [GameState.IDLE, GameState.WAITING, GameState.READY]:
                continue

            # 检查是否有玩家在该场次中
            if not runtime["players"]:
                continue

            # 检查所有玩家是否都在准备区域内
            all_in_wait_area = True
            online_players = 0
            players_to_remove = []

            for player in runtime["players"]:
                # 检查玩家是否在线
                if player not in self.server.online_players:
                    # 玩家离线，记录需要移除的玩家
                    if player.name in self.player_session and self.player_session[player.name] == sid:
                        players_to_remove.append(player)
                    continue

                online_players += 1
                if not self.is_player_in_wait_area(player, sid):
                    all_in_wait_area = False
                    break

            # 移除离线玩家
            for player in players_to_remove:
                if player in runtime["players"]:
                    runtime["players"].remove(player)
                if player.name in runtime["alive_players"]:
                    runtime["alive_players"].remove(player.name)
                if player.name in self.player_session:
                    del self.player_session[player.name]

            # 如果所有玩家都在准备区域内，播放胜利音效
            if all_in_wait_area and online_players > 0:
                # 检查是否已经播放过音效，避免重复播放
                if "_victory_sound_played" not in runtime:
                    runtime["_victory_sound_played"] = False

                if not runtime["_victory_sound_played"] and runtime["state"] not in [GameState.IDLE, GameState.WAITING, GameState.READY]:
                    for player in runtime["players"]:
                        # 在玩家位置播放胜利音效
                        loc = player.location
                        self.server.dispatch_command(self.server.command_sender, f"playsound mob.enderdragon.death \"{player.name}\" {loc.x} {loc.y} {loc.z} 10")
                        player.send_message("§a所有玩家已回到准备区域，准备开始下一局游戏！")
                    runtime["_victory_sound_played"] = True
            else:
                # 如果有玩家不在准备区域内，重置音效播放标志
                if "_victory_sound_played" in runtime:
                    runtime["_victory_sound_played"] = False

    def init_session_runtime(self, session_id):
        if session_id not in self.game_sessions:
            # 从配置文件中读取边界相关的参数
            session_data = self.plugin_config.get("sessions", {}).get(session_id, {})
            border_config = session_data.get("border", {})

            self.game_sessions[session_id] = {
                "players": [],
                "state": GameState.IDLE,
                "bossbar": None,
                "scoreboard": None,
                "tasks": [],
                "countdown": 0,
                "game_time": 0,
                "alive_players": [],
                "border_radius": border_config.get("initial_radius", 20),  # 初始边界半径
                "min_border_radius": border_config.get("min_radius", 4),  # 最小边界半径
                "border_shrink_interval": border_config.get("shrink_interval", 300),  # 边界缩小间隔（秒）
                "border_shrink_amount": border_config.get("shrink_amount", 4),  # 每次缩小的格数
                "border_damage_per_second": border_config.get("damage_per_second", 5),  # 每秒扣血量
                "last_shrink_time": 0  # 上次缩小边界的时间
            }

    def load_config(self):
        if plugin_config_path.exists():
            try:
                with open(plugin_config_path, "r", encoding="utf-8") as f:
                    self.plugin_config = json.load(f)
                # 再次确保 sessions 键存在
                if "sessions" not in self.plugin_config:
                    self.plugin_config["sessions"] = {}
                # 加载物品池
                if "item_pool" in self.plugin_config:
                    self.weighted_item_pool = self.plugin_config["item_pool"]
            except Exception as e:
                plugin_print(f"加载配置文件失败: {e}", "ERROR")
                self.init_default_config()
        else:
            self.init_default_config()

    def init_default_config(self):
        """初始化默认配置文件"""
        self.plugin_config = {
            "sessions": {
                "1": {
                    "name": "默认场次",
                    "center_pos": {"x": 0, "y": 100, "z": 0},
                    "pillars": {
                        "1": {"x": 0, "y": 99, "z": 0},
                        "2": {"x": 0, "y": 99, "z": -16},
                        "3": {"x": 16, "y": 99, "z": 0},
                        "4": {"x": 0, "y": 99, "z": 16},
                        "5": {"x": -16, "y": 99, "z": 0},
                        "6": {"x": -11, "y": 99, "z": -11},
                        "7": {"x": 11, "y": 99, "z": -11},
                        "8": {"x": -11, "y": 99, "z": 11},
                        "9": {"x": 11, "y": 99, "z": 11}
                    },
                    "min_players": 2,
                    "wait_area": {
                        "pos1": {"x": -20, "y": 100, "z": -20},
                        "pos2": {"x": 20, "y": 100, "z": 20}
                    },
                    "border": {
                        "initial_radius": 20,
                        "min_radius": 4,
                        "shrink_interval": 300,
                        "shrink_amount": 4,
                        "damage_per_second": 5
                    },
                    "particles": {
                        "enabled": True,
                        "particle_type": "minecraft:falling_border_dust_particle",
                        "particle_height": 10,
                        "particle_y_offset": -48,
                        "horizontal_step": 2,
                        "vertical_step": 1,
                        "view_distance": 4
                    },
                    "sounds": {
                        "enabled": True,
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
                        "item_interval": 100,
                        "event_interval": 1200,
                        "border_check_interval": 20,
                        "particle_interval": 20,
                        "scoreboard_update_interval": 20
                    }
                }
            },
            "item_pool": {
                "cobblestone": 100, "dirt": 100, "sand": 80, "gravel": 80, "planks": 100, "log": 80,
                "glass": 60, "wool": 60, "stone": 80, "andesite": 70, "diorite": 70, "granite": 70,
                "deepslate": 70, "tuff": 60, "moss_block": 50, "mud": 60,
                "iron_ingot": 50, "gold_ingot": 40, "coal": 60, "copper_ingot": 50, "redstone": 40,
                "lapis_lazuli": 30, "emerald": 20, "diamond": 10, "netherite_ingot": 2,
                "bread": 60, "cooked_beef": 50, "apple": 60, "carrot": 60, "potato": 60,
                "golden_apple": 10, "enchanted_golden_apple": 1,
                "bow": 30, "arrow": 50, "crossbow": 20, "iron_sword": 30, "diamond_sword": 5,
                "iron_pickaxe": 30, "diamond_pickaxe": 5, "shield": 20, "totem_of_undying": 2,
                "trident": 3, "spyglass": 10, "fishing_rod": 20, "snowball": 40, "egg": 40,
                "iron_helmet": 15, "iron_chestplate": 10, "iron_leggings": 15, "iron_boots": 15,
                "diamond_helmet": 3, "diamond_chestplate": 2, "diamond_leggings": 3, "diamond_boots": 3,
                "tnt": 25, "ender_pearl": 15, "bucket": 30, "water_bucket": 20, "lava_bucket": 15,
                "firework_rocket": 20, "slime_ball": 20, "magma_cream": 15, "obsidian": 10,
                "white_wool": 60, "orange_wool": 60, "magenta_wool": 60, "light_blue_wool": 60,
                "yellow_wool": 60, "lime_wool": 60, "pink_wool": 60, "gray_wool": 60,
                "light_gray_wool": 60, "cyan_wool": 60, "purple_wool": 60, "blue_wool": 60,
                "brown_wool": 60, "green_wool": 60, "red_wool": 60, "black_wool": 60,
                "white_concrete": 70, "orange_concrete": 70, "magenta_concrete": 70, "light_blue_concrete": 70,
                "yellow_concrete": 70, "lime_concrete": 70, "pink_concrete": 70, "gray_concrete": 70,
                "light_gray_concrete": 70, "cyan_concrete": 70, "purple_concrete": 70, "blue_concrete": 70,
                "brown_concrete": 70, "green_concrete": 70, "red_concrete": 70, "black_concrete": 70
            }
        }
        self.save_config()
        plugin_print("已初始化默认配置文件", "SUCCESS")

    def save_config(self):
        plugin_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(plugin_config_path, "w", encoding="utf-8") as f:
            json.dump(self.plugin_config, f, indent=4, ensure_ascii=False)

    # --- 命令处理 ---
    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if command.name == "lp":
            if not args:
                # 显示当前场次情况
                self.show_session_info(sender)
            elif args[0] == "menu":
                # 显示菜单
                self.show_player_menu(sender)
            elif args[0] == "leave":
                self.leave_game(sender)
            return True
        
        if command.name == "lpadmin":
            if not args: return False
            if args[0] == "reload":
                self.load_config()
                sender.send_message("§a配置已重载")
            elif args[0] == "init" and len(args) > 1:
                self.init_default_config()
            elif args[0] == "add" and len(args) > 1:
                self.add_session(sender, args[1])
            elif args[0] == "remove" and len(args) > 1:
                self.remove_session(sender, args[1])
            elif args[0] == "setcenter" and len(args) > 1:
                self.set_center(sender, args[1])
            elif args[0] == "addpillar" and len(args) > 1:
                self.add_pillar(sender, args[1])
            elif args[0] == "setwaitarea" and len(args) > 1:
                self.set_wait_area(sender, args[1])
            elif args[0] == "start" and len(args) > 1:
                self.start_game_process(sender, args[1])
            elif args[0] == "stop" and len(args) > 1:
                self.stop_game(args[1], "管理员停止了游戏")
            return True
        return False

    # --- 菜单系统 ---
    def show_player_menu(self, sender: CommandSender):
        if not isinstance(sender, Player): return
        form = ActionForm(title="§l幸运之柱 - 场次列表")
        sessions = self.plugin_config.get("sessions", {})
        
        if not sessions:
            form.content = "§c当前没有可用的场次。"
        else:
            for sid, data in sessions.items():
                runtime = self.game_sessions.get(sid, {"state": GameState.IDLE, "players": []})
                state_text = {
                    GameState.IDLE: "§7空闲", GameState.WAITING: "§a等待中",
                    GameState.READY: "§b准备就绪", GameState.COUNTDOWN: "§e倒计时", 
                    GameState.RUNNING: "§c进行中", GameState.ENDED: "§8已结束"
                }.get(runtime["state"], "§7未知")
                
                btn_text = f"{data['name']}\n{state_text} §r| §b{len(runtime['players'])}人"
                form.add_button(btn_text, on_click=lambda p, s=sid: self.teleport_to_center(p, s))
        
        sender.send_form(form)

    def show_session_info(self, sender: CommandSender):
        """显示当前场次情况"""
        sessions = self.plugin_config.get("sessions", {})

        if not sessions:
            sender.send_message("§c当前没有可用的场次。")
            return

        sender.send_message("§e===== 幸运之柱 - 场次列表 =====")
        for sid, data in sessions.items():
            runtime = self.game_sessions.get(sid, {"state": GameState.IDLE, "players": []})
            state_text = {
                GameState.IDLE: "§7空闲", GameState.WAITING: "§a等待中",
                GameState.READY: "§b准备就绪", GameState.COUNTDOWN: "§e倒计时",
                GameState.RUNNING: "§c进行中", GameState.ENDED: "§8已结束"
            }.get(runtime["state"], "§7未知")

            center = data.get("center_pos", {"x": 0, "y": 100, "z": 0})
            wait_area = data.get("wait_area", None)

            sender.send_message(f"§6场次 {sid}: §f{data['name']}")
            sender.send_message(f"  状态: {state_text} §r| §b{len(runtime['players'])}人")
            sender.send_message(f"  中心位置: §e({center['x']}, {center['y']}, {center['z']})")
            if wait_area:
                pos1 = wait_area.get("pos1", {"x": 0, "y": 100, "z": 0})
                pos2 = wait_area.get("pos2", {"x": 0, "y": 100, "z": 0})
                sender.send_message(f"  准备区域: §e({pos1['x']}, {pos1['y']}, {pos1['z']}) 到 ({pos2['x']}, {pos2['y']}, {pos2['z']})")
            else:
                sender.send_message(f"  准备区域: §c未设置")

        sender.send_message("§e================================")

    def teleport_to_center(self, player: Player, session_id: str):
        """传送玩家到指定场次的中心点"""
        if session_id not in self.plugin_config.get("sessions", {}):
            player.send_message("§c场次不存在！")
            return

        session_data = self.plugin_config["sessions"][session_id]
        center = session_data.get("center_pos", {"x": 0, "y": 100, "z": 0})

        player.teleport(Location(player.dimension, center["x"] - 0.5, center["y"] + 1, center["z"] + 0.5))
        player.send_message(f"§a已传送到场次 {session_id} 的中心位置！")

    def is_player_in_wait_area(self, player: Player, session_id: str) -> bool:
        """检查玩家是否在指定场次的准备区域内"""
        if session_id not in self.plugin_config.get("sessions", {}):
            return False

        session_data = self.plugin_config["sessions"][session_id]
        wait_area = session_data.get("wait_area", None)
        if not wait_area:
            return False

        pos1 = wait_area.get("pos1", {"x": 0, "y": 100, "z": 0})
        pos2 = wait_area.get("pos2", {"x": 0, "y": 100, "z": 0})

        # 获取准备区域的边界
        min_x = min(pos1["x"], pos2["x"])
        max_x = max(pos1["x"], pos2["x"])
        min_y = min(pos1["y"], pos2["y"])
        max_y = max(pos1["y"], pos2["y"])
        min_z = min(pos1["z"], pos2["z"])
        max_z = max(pos1["z"], pos2["z"])

        # 检查玩家位置是否在准备区域内
        player_x = player.location.x
        player_y = player.location.y
        player_z = player.location.z
        in_area = (min_x <= player_x <= max_x and
                min_y <= player_y <= max_y and
                min_z <= player_z <= max_z)

        return in_area

    # --- 游戏逻辑 ---
    def join_game(self, player: Player, session_id: str):
        if player.name in self.player_session:
            # 玩家已经在游戏中，检查是否还在准备区域内
            current_session = self.player_session[player.name]
            if current_session == session_id:
                # 还在同一个场次，不需要做任何操作
                return
            else:
                # 玩家移动到了另一个场次的准备区域，先退出当前场次
                self.leave_game(player)

        if session_id not in self.plugin_config.get("sessions", {}):
            return

        session_data = self.plugin_config["sessions"][session_id]
        self.init_session_runtime(session_id)
        runtime = self.game_sessions[session_id]

        if runtime["state"] not in [GameState.IDLE, GameState.WAITING, GameState.READY]:
            return

        runtime["players"].append(player)
        self.player_session[player.name] = session_id
        player.send_message(f"§a你已进入场次 {session_data['name']} 的准备区域！")
        
        self.update_bossbar(session_id)
        self.update_scoreboard(session_id)

    def leave_game(self, player: Player, silent=False):
        if player.name not in self.player_session:
            if not silent:
                player.send_message("§c你不在任何场次中！")
            return
        
        session_id = self.player_session[player.name]
        runtime = self.game_sessions[session_id]
        
        if player in runtime["players"]:
            runtime["players"].remove(player)
        
        if player.name in runtime["alive_players"]:
            runtime["alive_players"].remove(player.name)
        
        if runtime["bossbar"]:
            runtime["bossbar"].remove_player(player)
            
        del self.player_session[player.name]
        if not silent:
            player.send_message("§e你离开了游戏。")
        
        if runtime["state"] == GameState.RUNNING:
            self.check_winner(session_id)
        else:
            self.update_bossbar(session_id)
            self.update_scoreboard(session_id)

    def update_bossbar(self, session_id):
        runtime = self.game_sessions[session_id]
        session_data = self.plugin_config.get("sessions", {}).get(session_id, {})
        if not session_data: return
        
        min_players = session_data.get("min_players", 2)
        pillars = session_data.get("pillars", {})
        max_players = len(pillars)
        # 只计算在线玩家
        current_players = len([p for p in runtime["players"] if p in self.server.online_players])
        
        if not runtime["bossbar"]:
            runtime["bossbar"] = self.server.create_boss_bar(
                "幸运之柱", BarColor.YELLOW, BarStyle.SOLID
            )
        
        if runtime["state"] == GameState.RUNNING:
            m, s = divmod(runtime["game_time"], 60)
            runtime["bossbar"].title = f"§c游戏进行中 §f| §e时间: {m:02d}:{s:02d} §f| §e存活: {len(runtime['alive_players'])}/{max_players}"
            runtime["bossbar"].color = BarColor.RED
            runtime["bossbar"].progress = 1.0
        elif runtime["state"] == GameState.COUNTDOWN:
            # 倒计时状态，进度条从少到多
            countdown = runtime.get("countdown", 10)
            # 进度条从 0（倒计时开始）到 1（倒计时结束）
            progress = 1.0 - (countdown / 10.0)
            # 确保进度在 0-1 之间
            progress = max(0.0, min(1.0, progress))
            runtime["bossbar"].title = f"§e游戏即将开始 §f| §e倒计时: §c{countdown} §e秒"
            runtime["bossbar"].color = BarColor.YELLOW
            runtime["bossbar"].progress = progress
        elif current_players < min_players:
            runtime["bossbar"].title = f"§e等待玩家: §f{current_players}/{min_players} §7(还需{min_players - current_players}人) §f| §e最大: {max_players}人"
            runtime["bossbar"].progress = min(1.0, current_players / min_players)
            runtime["bossbar"].color = BarColor.YELLOW
            runtime["state"] = GameState.WAITING
        elif current_players == min_players:
            runtime["bossbar"].title = f"§a可以开始游戏了 §f{current_players}/{min_players} §f| §e最少: {min_players}人 最多: {max_players}人"
            runtime["bossbar"].progress = 1.0
            runtime["bossbar"].color = BarColor.GREEN
            if runtime["state"] == GameState.WAITING:
                runtime["state"] = GameState.READY
        elif current_players > min_players:
            runtime["bossbar"].title = f"§a可以开始游戏了 §f{current_players}/{max_players} §f| §e最少: {min_players}人 最多: {max_players}人"
            runtime["bossbar"].progress = min(1.0, current_players / max_players)
            runtime["bossbar"].color = BarColor.WHITE
            if runtime["state"] == GameState.WAITING:
                runtime["state"] = GameState.READY
        
        # 只为准备区域和参与游戏的玩家显示bossbar
        # 遍历所有在线玩家，检查是否应该显示bossbar
        all_online_players = self.server.online_players
        for player in all_online_players:
            # 检查玩家是否在游戏中或在准备区域内
            if player.name in self.player_session and self.player_session[player.name] == session_id:
                # 玩家在游戏中，显示bossbar
                runtime["bossbar"].add_player(player)
            elif self.is_player_in_wait_area(player, session_id):
                # 玩家在准备区域内，显示bossbar
                runtime["bossbar"].add_player(player)
            else:
                # 玩家不在准备区域内也不在游戏中，隐藏bossbar
                runtime["bossbar"].remove_player(player)

    def update_scoreboard(self, session_id):
        """更新侧边栏显示游戏信息"""
        runtime = self.game_sessions[session_id]
        session_data = self.plugin_config.get("sessions", {}).get(session_id, {})
        if not session_data: return

        # 创建或获取侧边栏
        if not runtime["scoreboard"]:
            scoreboard = self.server.scoreboard
            objective_name = f"lucky_pillar_{session_id}"

            # 检查 objective 是否已存在
            existing_objective = scoreboard.get_objective(objective_name)
            if existing_objective:
                objective = existing_objective
            else:
                objective = scoreboard.add_objective(
                    name=objective_name,
                    criteria=Criteria.DUMMY,
                    display_name="§e§l幸运之柱"
                )

            objective.set_display(DisplaySlot.SIDE_BAR)
            runtime["scoreboard"] = objective

        objective = runtime["scoreboard"]

        # 清空旧的分数 - 使用更可靠的方式
        try:
            for entry in list(objective.scoreboard.entries):
                objective.scoreboard.reset_scores(entry)
        except Exception as e:
            plugin_print(f"[DEBUG] 清空分数时出错: {e}", "WARNING")

        # 只为准备区域和参与游戏的玩家显示侧边栏
        # 获取所有在线玩家
        all_online_players = self.server.online_players
        # 遍历所有在线玩家，检查是否应该显示侧边栏
        for player in all_online_players:
            # 如果玩家在准备区域内或参与游戏中，则显示侧边栏
            if player.name in self.player_session and self.player_session[player.name] == session_id:
                # 玩家在游戏中，确保显示侧边栏
                continue
            else:
                # 玩家不在游戏中，检查是否在准备区域内
                if self.is_player_in_wait_area(player, session_id):
                    # 玩家在准备区域内，确保显示侧边栏
                    continue
                else:
                    # 玩家不在准备区域内也不在游戏中，隐藏侧边栏
                    # 通过清空该玩家的分数来隐藏侧边栏
                    try:
                        # 重置该玩家在侧边栏中的所有分数
                        for entry in list(objective.scoreboard.entries):
                            if entry == player.name:
                                objective.scoreboard.reset_scores(entry)
                    except Exception as e:
                        plugin_print(f"[DEBUG] 隐藏侧边栏时出错: {e}", "WARNING")

        # 获取游戏信息
        pillars = session_data.get("pillars", {})
        max_players = len(pillars)
        # 只计算在线玩家
        current_players = len([p for p in runtime["players"] if p in self.server.online_players])
        alive_players = len(runtime["alive_players"])

        # 根据游戏状态显示不同信息
        if runtime["state"] == GameState.RUNNING:
            # 游戏进行中
            m, s = divmod(runtime["game_time"], 60)

            # 计算下一事件时间
            tasks_config = session_data.get("tasks", {})
            event_interval = tasks_config.get("event_interval", 1200)  # 获取事件间隔（tick）
            event_period_seconds = event_interval / 20  # 转换为秒
            # 事件从游戏开始后event_interval秒开始触发
            if runtime["game_time"] < event_period_seconds:
                time_until_event = event_period_seconds - runtime["game_time"]
            else:
                # 计算当前周期内已经过去的时间
                time_in_current_period = runtime["game_time"] % event_period_seconds
                time_until_event = event_period_seconds - time_in_current_period
            # 转换为分秒
            event_minutes = int(time_until_event // 60)
            event_seconds = int(time_until_event % 60)

            # 获取下一事件名称
            next_event_name = self.get_next_event_name(runtime["game_time"], session_id)

            # 计算下一边界缩小时间
            border_interval = runtime["border_shrink_interval"]  # 秒
            time_since_last_shrink = runtime["game_time"] - runtime["last_shrink_time"]
            time_until_shrink = border_interval - time_since_last_shrink
            # 转换为分秒
            shrink_minutes = int(time_until_shrink // 60)
            shrink_seconds = int(time_until_shrink % 60)

            # 设置侧边栏内容
            try:
                # 获取或创建 objective
                scoreboard = self.server.scoreboard
                objective_name = f"lucky_pillar_{session_id}"

                # 检查 objective 是否已存在
                existing_objective = scoreboard.get_objective(objective_name)
                if existing_objective:
                    objective = existing_objective
                else:
                    objective = scoreboard.add_objective(
                        objective_name,
                        Criteria.DUMMY,
                        "§e§l幸运之柱"
                    )
                    objective.set_display(DisplaySlot.SIDE_BAR)
                    runtime["scoreboard"] = objective

                # 清空旧的分数
                for entry in list(objective.scoreboard.entries):
                    objective.scoreboard.reset_scores(entry)

                # 设置新的分数
                objective.get_score("§a§l游戏信息").value = 10
                objective.get_score(f"§e游戏时间: §f{m:02d}:{s:02d}").value = 9
                objective.get_score(f"§e存活玩家: §f{alive_players}/{max_players}").value = 8
                objective.get_score(f"§e当前半径: §f{runtime['border_radius']}").value = 7
                objective.get_score("§r").value = 6
                objective.get_score("§c§l下一事件").value = 5
                objective.get_score(f"§f{next_event_name}").value = 4
                objective.get_score(f"§e距离触发: §f{event_minutes:02d}:{event_seconds:02d}").value = 3
                objective.get_score("§r ").value = 2
                objective.get_score("§c§l边界缩小").value = 1
                objective.get_score(f"§e距离缩小: §f{shrink_minutes:02d}:{shrink_seconds:02d}").value = 0
                next_radius = max(runtime["min_border_radius"], runtime["border_radius"] - runtime["border_shrink_amount"])
                objective.get_score(f"§e缩小到: §f{next_radius}").value = -1
            except Exception as e:
                plugin_print(f"设置分数时出错: {e}", "ERROR")

        elif runtime["state"] == GameState.COUNTDOWN:
            # 倒计时状态
            countdown = runtime.get("countdown", 10)

            # 设置倒计时状态的分数
            objective.get_score("§a§l游戏即将开始").value = 10
            objective.get_score("§e倒计时: §c" + f"{countdown}秒").value = 9
            objective.get_score("").value = 8
            objective.get_score("§e当前玩家: §f" + f"{current_players}/{max_players}").value = 7
            objective.get_score("§e最少需要: §f" + str(session_data.get("min_players", 2)) + "人").value = 6
            objective.get_score("").value = 5
            objective.get_score("§e最大人数: §f" + f"{max_players}人").value = 4

        elif runtime["state"] == GameState.WAITING or runtime["state"] == GameState.READY:
            # 等待玩家状态
            min_players = session_data.get("min_players", 2)

            # 设置等待状态的分数
            objective.get_score("§a§l等待玩家").value = 10
            objective.get_score("§e当前玩家: §f" + f"{current_players}/{max_players}").value = 9
            objective.get_score("§e最少需要: §f" + f"{min_players}人").value = 8
            objective.get_score("§e最大人数: §f" + f"{max_players}人").value = 7
            objective.get_score("").value = 6

            if current_players >= min_players:
                objective.get_score("§a可以开始游戏！").value = 5
            else:
                objective.get_score("§c还需 " + str(min_players - current_players) + " 人").value = 5

    def start_game_process(self, sender: CommandSender, session_id: str):
        if session_id not in self.plugin_config.get("sessions", {}):
            sender.send_message("§c场次不存在！")
            return
            
        self.init_session_runtime(session_id)
        runtime = self.game_sessions[session_id]
        session_data = self.plugin_config["sessions"][session_id]
        min_players = session_data.get("min_players", 2)
        
        if len(runtime["players"]) < min_players:
            sender.send_message(f"§c人数不足，无法开始游戏！(当前: {len(runtime['players'])}, 需要: {min_players})")
            return
            
        if runtime["state"] not in [GameState.READY, GameState.WAITING]:
            sender.send_message("§c该场次已在进行中！")
            return

        # 1. 确保游戏规则：立即重生
        self.server.dispatch_command(self.server.command_sender, "gamerule doimmediaterespawn true")
            
        # 先设置为等待状态，确保玩家不会被自动移出游戏
        runtime["state"] = GameState.WAITING
        runtime["countdown"] = 10
        runtime["game_time"] = 0
        runtime["alive_players"] = [p.name for p in runtime["players"]]
        
        # 2. 传送玩家并立即清理背包
        pillars = list(session_data.get("pillars", {}).values())
        random.shuffle(pillars)
        for i, player in enumerate(runtime["players"]):
            if i < len(pillars):
                pos = pillars[i]
                player.teleport(Location(player.dimension, pos["x"] - 0.5, pos["y"] + 1, pos["z"] + 0.5))
            
            # 优化: 使用 /clear 清理背包
            self.server.dispatch_command(self.server.command_sender, f"clear \"{player.name}\"")
            
            self.server.dispatch_command(self.server.command_sender, f"inputpermission set \"{player.name}\" movement disabled")
            player.game_mode = GameMode.SURVIVAL
            
        task = self.server.scheduler.run_task(
            self, lambda: self.countdown_tick(session_id), delay=0, period=20
        )
        runtime["tasks"].append(task)
        sender.send_message(f"§a场次 {session_id} 已重置场地并开启传送。")

    def countdown_tick(self, session_id):
        runtime = self.game_sessions[session_id]

        # 如果当前状态是 WAITING，设置为 COUNTDOWN
        if runtime["state"] == GameState.WAITING:
            runtime["state"] = GameState.COUNTDOWN

        # 获取声音配置
        session_data = self.plugin_config.get("sessions", {}).get(session_id, {})
        sound_config = session_data.get("sounds", {})

        if runtime["countdown"] > 0:
            self.update_scoreboard(session_id)
            self.update_bossbar(session_id)
            msg = f"§e游戏将在 §c{runtime['countdown']} §e秒后开始！"
            for p in runtime["players"]:
                p.send_title("§l§e倒计时", msg, 0, 25, 5)
                # 剩余 5 秒时播放经验粒子音效，音调由低到高
                if runtime["countdown"] <= 5:
                    # 音调计算: 5秒->0.6, 4秒->0.8, 3秒->1.0, 2秒->1.2, 1秒->1.4
                    pitch = 0.6 + (5 - runtime["countdown"]) * 0.2
                    # 使用配置文件中的声音参数
                    if sound_config.get("enabled", True):
                        sound_name = sound_config.get("countdown_sound", "random.orb")
                        volume = sound_config.get("countdown_volume", 10.0)
                        p.play_sound(p.location, sound_name, volume=volume, pitch=pitch)

            runtime["countdown"] -= 1
        else:
            self.start_game_final(session_id)

    def start_game_final(self, session_id):
        runtime = self.game_sessions[session_id]
        for task in runtime["tasks"]:
            task.cancel()
        runtime["tasks"] = []
        
        # 获取场次配置
        session_data = self.plugin_config.get("sessions", {}).get(session_id, {})
        pillars = session_data.get("pillars", {})
        max_players = len(pillars)

        # 获取任务间隔配置
        tasks_config = session_data.get("tasks", {})

        # 检查玩家数量是否超过最大人数
        if len(runtime["players"]) > max_players:
            # 随机移除多余的玩家
            players_to_remove = len(runtime["players"]) - max_players
            removed_players = random.sample(runtime["players"], players_to_remove)

            # 从玩家列表中移除
            for p in removed_players:
                runtime["players"].remove(p)
                runtime["alive_players"].remove(p.name)
                # 传送回等待区域
                wait_area = session_data.get("wait_area", {})
                pos1 = wait_area.get("pos1", {"x": 0, "y": 100, "z": 0})
                p.teleport(Location(p.dimension, pos1["x"] - 0.5, pos1["y"], pos1["z"] + 0.5))
                p.send_message("§c很遗憾，人数已满，您已被移出游戏！")
                p.game_mode = GameMode.ADVENTURE

            # 通知所有玩家
            for p in runtime["players"]:
                p.send_message(f"§e由于人数超过最大人数（{max_players}人），已随机移除了 {players_to_remove} 名玩家！")

        runtime["state"] = GameState.RUNNING
        
        for p in runtime["players"]:
            self.server.dispatch_command(self.server.command_sender, f"inputpermission set \"{p.name}\" movement enabled")
            p.send_title("§a游戏开始！", "§7祝你好运", 10, 40, 10)

        time_task = self.server.scheduler.run_task(
            self, lambda: self.game_timer_tick(session_id), delay=0, period=20
        )
        item_task = self.server.scheduler.run_task(
            self, lambda: self.give_random_items(session_id), delay=tasks_config.get("item_interval", 100), period=tasks_config.get("item_interval", 100)
        )
        event_task = self.server.scheduler.run_task(
            self, lambda: self.trigger_random_event(session_id), delay=tasks_config.get("event_interval", 1200), period=tasks_config.get("event_interval", 1200)
        )
        border_task = self.server.scheduler.run_task(
            self, lambda: self.check_border_shrink(session_id), delay=tasks_config.get("border_check_interval", 20), period=tasks_config.get("border_check_interval", 20)
        )
        
        self.show_border_particles(session_id)
        
        particle_task = self.server.scheduler.run_task(
            self, lambda: self.show_border_particles(session_id), delay=100, period=tasks_config.get("particle_interval", 20)
        )
        # 独立的侧边栏更新任务
        scoreboard_task = self.server.scheduler.run_task(
            self, lambda: self.scoreboard_update_tick(session_id), delay=0, period=tasks_config.get("scoreboard_update_interval", 20)
        )

        runtime["tasks"].extend([time_task, item_task, event_task, border_task, scoreboard_task, particle_task])
        self.update_bossbar(session_id)
        self.update_scoreboard(session_id)

    def game_timer_tick(self, session_id):
        runtime = self.game_sessions[session_id]
        if runtime["state"] == GameState.RUNNING:
            runtime["game_time"] += 1
            self.update_bossbar(session_id)

    def scoreboard_update_tick(self, session_id):
        """独立的侧边栏更新函数"""
        runtime = self.game_sessions[session_id]
        if runtime["state"] == GameState.RUNNING:
            self.update_scoreboard(session_id)

    def get_weighted_random_item(self):
        items = list(self.weighted_item_pool.keys())
        weights = list(self.weighted_item_pool.values())
        return random.choices(items, weights=weights, k=1)[0]

    def give_random_items(self, session_id):
        runtime = self.game_sessions[session_id]
        if runtime["state"] != GameState.RUNNING: return
        for p in runtime["players"]:
            # 检查玩家是否在线
            if p not in self.server.online_players:
                continue

            if p.name in runtime["alive_players"]:
                item_type = self.get_weighted_random_item()
                # 优化: 使用 inventory API 发放物品
                try:
                    item_stack = ItemStack(item_type, 1)
                    p.inventory.add_item(item_stack)
                    p.send_tip(f"§a获得随机物品: §f{item_type}")
                except Exception as e:
                    plugin_print(f"无法发放物品 {item_type}: {e}", "ERROR")

    def get_next_event_name(self, game_time, session_id=None):
        """根据游戏时间获取下一事件的名称"""
        events = ["darkness", "tnt", "ghast", "lightning", "blindness", "slowness", "levitation"]
        event_names = {
            "darkness": "黑暗降临",
            "tnt": "TNT雨",
            "ghast": "恶魂袭击",
            "lightning": "雷击警告",
            "blindness": "视野受阻",
            "slowness": "行动迟缓",
            "levitation": "漂浮之力"
        }

        # 获取事件间隔
        event_interval = 1200  # 默认1200 tick（60秒）
        if session_id and session_id in self.game_sessions:
            session_data = self.plugin_config.get("sessions", {}).get(session_id, {})
            tasks_config = session_data.get("tasks", {})
            event_interval = tasks_config.get("event_interval", 1200)

        event_period_seconds = event_interval / 20  # 转换为秒

        # 计算当前是第几个事件周期
        # 如果游戏时间正好是事件周期的整数倍，则触发该事件
        # 否则，计算下一个事件周期
        event_cycle = int(game_time / event_period_seconds)

        # 检查是否正好在事件触发时间点
        time_in_current_period = game_time % event_period_seconds
        if time_in_current_period == 0:
            # 正好在事件触发时间点，显示当前事件
            current_event_cycle = event_cycle
        else:
            # 不在事件触发时间点，显示下一个事件
            current_event_cycle = event_cycle + 1

        # 使用哈希函数生成确定性的随机选择
        # 为了增加随机性，使用多个哈希值组合
        hash_value = hash((current_event_cycle, 123456789))
        event_index = abs(hash_value) % len(events)
        event = events[event_index]

        return event_names.get(event, "未知事件")

    def spawn_tnt_in_border(self, session_id, center_pos, border_radius):
        """在边界内随机位置生成TNT"""
        runtime = self.game_sessions[session_id]
        if runtime["state"] != GameState.RUNNING: return

        # 随机选择一个玩家作为基准
        alive_players = [p for p in runtime["players"] if p in self.server.online_players and p.name in runtime["alive_players"]]
        if not alive_players:
            return

        target_player = random.choice(alive_players)

        # 在边界内随机位置生成TNT
        x_min = center_pos["x"] - border_radius
        x_max = center_pos["x"] + border_radius
        z_min = center_pos["z"] - border_radius
        z_max = center_pos["z"] + border_radius

        # 随机生成TNT位置
        tnt_x = random.uniform(x_min, x_max)
        tnt_y = target_player.location.y + random.randint(10, 20)  # 玩家上方10-20格
        tnt_z = random.uniform(z_min, z_max)

        # 生成TNT
        self.server.dispatch_command(self.server.command_sender, f"summon tnt {tnt_x} {tnt_y} {tnt_z}")

    def trigger_random_event(self, session_id):
        runtime = self.game_sessions[session_id]
        if runtime["state"] != GameState.RUNNING: return
        events = ["darkness", "tnt", "ghast", "lightning", "blindness", "slowness", "levitation"]
        
        # 获取事件间隔
        session_data = self.plugin_config.get("sessions", {}).get(session_id, {})
        tasks_config = session_data.get("tasks", {})
        event_interval = tasks_config.get("event_interval", 1200)
        event_period_seconds = event_interval / 20  # 转换为秒

        # 使用游戏时间作为随机种子，确保触发的事件与显示的事件名称一致
        event_cycle = int(runtime["game_time"] / event_period_seconds)
        # 为了增加随机性，使用多个哈希值组合
        hash_value = hash((event_cycle, 123456789))
        event_index = abs(hash_value) % len(events)
        event = events[event_index]
        for p in runtime["players"]:
            # 检查玩家是否在线
            if p not in self.server.online_players:
                continue

            if p.name in runtime["alive_players"]:
                if event == "darkness":
                    self.server.dispatch_command(self.server.command_sender, f"effect \"{p.name}\" darkness 10 1 true")
                    p.send_message("§8[事件] §7黑暗降临...")
                elif event == "tnt":
                    # 获取边界和中心点信息
                    session_data = self.plugin_config.get("sessions", {}).get(session_id, {})
                    center_pos = session_data.get("center_pos", {"x": 0, "y": 100, "z": 0})
                    border_radius = runtime["border_radius"]

                    # 随机持续时间 3-5 秒
                    duration = random.randint(3, 5)

                    # 发送消息
                    p.send_message("§4[事件] §cTNT雨来袭！")

                    # 在边界内平面随机生成TNT，持续几秒
                    # 使用调度器延迟执行，避免阻塞主线程
                    for i in range(duration * 4):  # 每0.25秒生成一次
                        self.server.scheduler.run_task(
                            self, 
                            lambda: self.spawn_tnt_in_border(session_id, center_pos, border_radius),
                            delay=i * 5  # 5 tick = 0.25秒
                        )
                elif event == "ghast":
                    # 获取所有存活的玩家
                    alive_players = [p for p in runtime["players"] if p in self.server.online_players and p.name in runtime["alive_players"]]

                    if alive_players:
                        # 计算所有存活玩家的中心点
                        center_x = sum(p.location.x for p in alive_players) / len(alive_players)
                        center_y = sum(p.location.y for p in alive_players) / len(alive_players)
                        center_z = sum(p.location.z for p in alive_players) / len(alive_players)

                        # 在玩家中心点上方生成恶魂
                        ghast_count = min(len(alive_players), 5)  # 最多生成5只恶魂
                        for i in range(ghast_count):
                            # 在中心点周围随机偏移
                            offset_x = random.uniform(-5, 5)
                            offset_z = random.uniform(-5, 5)
                            spawn_x = center_x + offset_x
                            spawn_y = center_y + 10 + i * 3  # 每只恶魂高度相差3格
                            spawn_z = center_z + offset_z
                            self.server.dispatch_command(self.server.command_sender, f"summon ghast {spawn_x} {spawn_y} {spawn_z}")
                    p.send_message("§d[事件] §5恶魂来袭！")
                elif event == "lightning":
                    loc = p.location
                    self.server.dispatch_command(self.server.command_sender, f"summon lightning_bolt {loc.x} {loc.y} {loc.z}")
                    p.send_message("§e[事件] §6雷击警告！")
                elif event == "blindness":
                    self.server.dispatch_command(self.server.command_sender, f"effect \"{p.name}\" blindness 10 1 true")
                    p.send_message("§8[事件] §7视野受阻...")
                elif event == "slowness":
                    self.server.dispatch_command(self.server.command_sender, f"effect \"{p.name}\" slowness 10 2 true")
                    p.send_message("§7[事件] §8行动迟缓...")
                elif event == "levitation":
                    self.server.dispatch_command(self.server.command_sender, f"effect \"{p.name}\" levitation 5 1 true")
                    p.send_message("§b[事件] §3漂浮之力！")

    def check_winner(self, session_id):
        runtime = self.game_sessions[session_id]
        if runtime["state"] != GameState.RUNNING: return

        # 添加额外检查，防止在游戏已经结束后再次调用
        if session_id not in self.game_sessions or self.game_sessions[session_id]["state"] != GameState.RUNNING:
            return

        alive_count = len(runtime["alive_players"])
        if alive_count == 0:
            self.stop_game(session_id, "§c无人生还")
        elif alive_count == 1:
            winner_name = runtime["alive_players"][0]
            self.stop_game(session_id, f"§6游戏结束！胜利者是: §l{winner_name}")

    def stop_game(self, session_id, message):
        if session_id not in self.game_sessions: return
        runtime = self.game_sessions[session_id]
        session_data = self.plugin_config.get("sessions", {}).get(session_id, {})
        if not session_data: return
        
        center = session_data.get("center_pos", {"x": 0, "y": 100, "z": 0})
        
        for p in runtime["players"]:
            # 检查玩家是否在线
            if p not in self.server.online_players:
                continue

            p.send_title("§6游戏结束", message, 10, 60, 10)
            p.game_mode = GameMode.ADVENTURE
            self.server.dispatch_command(self.server.command_sender, f"inputpermission set \"{p.name}\" movement enabled")
            
            # 优化: 使用 /clear 结束后清理背包
            self.server.dispatch_command(self.server.command_sender, f"clear \"{p.name}\"")
            
            p.teleport(Location(p.dimension, center["x"] - 0.5, center["y"] + 1, center["z"] + 0.5))
            # 优化: 在玩家位置播放胜利音效，并增加音量
            loc = p.location
            self.server.dispatch_command(self.server.command_sender, f"playsound mob.wither.death \"{p.name}\" {loc.x} {loc.y} {loc.z} 10")
            if p.name in self.player_session:
                del self.player_session[p.name]
                
        # 清理恶魂
        self.server.dispatch_command(self.server.command_sender, f"kill @e[type=ghast]")

        if runtime["bossbar"]:
            runtime["bossbar"].remove_all()
            runtime["bossbar"] = None
        for task in runtime["tasks"]:
            task.cancel()
        runtime["players"] = []
        runtime["alive_players"] = []
        runtime["state"] = GameState.IDLE
        runtime["tasks"] = []
        runtime["game_time"] = 0
        plugin_print(f"场次 {session_id} 游戏已停止: {message}")

    # --- 事件监听 ---
    @event_handler
    def on_player_death(self, event: PlayerDeathEvent):
        player = event.player
        if player.name in self.player_session:
            session_id = self.player_session[player.name]
            runtime = self.game_sessions[session_id]
            if runtime["state"] == GameState.RUNNING:
                if player.name in runtime["alive_players"]:
                    runtime["alive_players"].remove(player.name)
                self.server.scheduler.run_task(self, lambda: self.handle_death_post(player, session_id), delay=1)

    def handle_death_post(self, player: Player, session_id: str):
        # 检查玩家是否在线
        if player not in self.server.online_players:
            return

        runtime = self.game_sessions[session_id]
        if runtime["state"] != GameState.RUNNING: return
        if len(runtime["alive_players"]) <= 1:
            self.check_winner(session_id)
        else:
            player.game_mode = GameMode.SPECTATOR
            player.send_message("§c你已被淘汰，进入旁观模式。")
            self.update_scoreboard(session_id)

    @event_handler
    def on_player_quit(self, event: PlayerQuitEvent):
        self.leave_game(event.player)

    # --- 管理功能 ---
    def add_session(self, sender: Player, name: str):
        # 确保 sessions 键存在
        if "sessions" not in self.plugin_config:
            self.plugin_config["sessions"] = {}
            
        sid = str(len(self.plugin_config["sessions"]) + 1)
        self.plugin_config["sessions"][sid] = {
            "name": name,
            "center_pos": {"x": int(sender.location.x), "y": int(sender.location.y), "z": int(sender.location.z)},
            "pillars": {},
            "min_players": 2
        }
        self.save_config()
        self.init_session_runtime(sid)
        sender.send_message(f"§a场次 {name} (ID: {sid}) 已创建。")

    def set_center(self, sender: Player, sid: str):
        if "sessions" in self.plugin_config and sid in self.plugin_config["sessions"]:
            self.plugin_config["sessions"][sid]["center_pos"] = {
                "x": int(sender.location.x), "y": int(sender.location.y), "z": int(sender.location.z)
            }
            self.save_config()
            sender.send_message(f"§a场次 {sid} 中心位置已更新。")
        else:
            sender.send_message(f"§c场次 {sid} 不存在！")

    def add_pillar(self, sender: Player, sid: str):
        if "sessions" in self.plugin_config and sid in self.plugin_config["sessions"]:
            pillars = self.plugin_config["sessions"][sid]["pillars"]
            pid = str(len(pillars) + 1)
            pillars[pid] = {"x": int(sender.location.x), "y": int(sender.location.y), "z": int(sender.location.z)}
            self.save_config()
            sender.send_message(f"§a场次 {sid} 已添加柱子 {pid}。")
        else:
            sender.send_message(f"§c场次 {sid} 不存在！")

    def set_wait_area(self, sender: Player, sid: str):
        """设置准备区域的两个点坐标"""
        if "sessions" not in self.plugin_config or sid not in self.plugin_config["sessions"]:
            sender.send_message(f"§c场次 {sid} 不存在！")
            return

        # 检查是否已经设置了第一个点
        if not hasattr(self, "_temp_wait_area"):
            self._temp_wait_area = {}

        if sid not in self._temp_wait_area:
            # 设置第一个点
            self._temp_wait_area[sid] = {
                "pos1": {"x": int(sender.location.x), "y": int(sender.location.y), "z": int(sender.location.z)}
            }
            sender.send_message(f"§a已设置场次 {sid} 准备区域的第一个点，请移动到第二个点并再次执行该命令。")
        else:
            # 设置第二个点
            self._temp_wait_area[sid]["pos2"] = {
                "x": int(sender.location.x), "y": int(sender.location.y), "z": int(sender.location.z)
            }
            # 保存到配置
            self.plugin_config["sessions"][sid]["wait_area"] = self._temp_wait_area[sid]
            self.save_config()
            sender.send_message(f"§a场次 {sid} 准备区域已设置完成！")
            # 清除临时数据
            del self._temp_wait_area[sid]

    def remove_session(self, sender: Player, sid: str):
        """删除指定的游戏场次"""
        if "sessions" not in self.plugin_config or sid not in self.plugin_config["sessions"]:
            sender.send_message(f"§c场次 {sid} 不存在！")
            return

        # 如果游戏正在运行，先停止游戏
        if sid in self.game_sessions and self.game_sessions[sid]["state"] != GameState.IDLE:
            self.stop_game(sid, "游戏已被管理员删除")

        # 从配置中删除场次
        del self.plugin_config["sessions"][sid]

        # 从运行时数据中删除场次
        if sid in self.game_sessions:
            del self.game_sessions[sid]

        # 保存配置
        self.save_config()

        sender.send_message(f"§a场次 {sid} 已成功删除！")

    def check_border_shrink(self, session_id):
        """检查并缩小边界"""
        runtime = self.game_sessions[session_id]
        if runtime["state"] != GameState.RUNNING:
            return

        # 检查是否需要缩小边界
        if runtime["game_time"] - runtime["last_shrink_time"] >= runtime["border_shrink_interval"]:
            # 检查是否已经达到最小边界
            if runtime["border_radius"] > runtime["min_border_radius"]:
                # 缩小边界
                old_radius = runtime["border_radius"]
                new_radius = max(runtime["min_border_radius"], old_radius - runtime["border_shrink_amount"])
                runtime["border_radius"] = new_radius
                runtime["last_shrink_time"] = runtime["game_time"]

                # 获取声音配置
                session_data = self.plugin_config.get("sessions", {}).get(session_id, {})
                sound_config = session_data.get("sounds", {})

                # 通知所有玩家
                for p in runtime["players"]:
                    if p in self.server.online_players and p.name in runtime["alive_players"]:
                        p.send_message(f"§c边界正在缩小！当前半径: {new_radius} 格")
                        p.send_title("§c警告", "§e边界正在缩小！", 0, 20, 5)
                        # 播放警告音效
                        if sound_config.get("enabled", True):
                            sound_name = sound_config.get("border_shrink_sound", "mob.wither.ambient")
                            volume = sound_config.get("border_shrink_volume", 10.0)
                            pitch = sound_config.get("border_shrink_pitch", 1.0)
                            p.play_sound(p.location, sound_name, volume=volume, pitch=pitch)

                # 更新侧边栏显示
                self.update_scoreboard(session_id)


        # 检查玩家是否在边界外
        session_data = self.plugin_config.get("sessions", {}).get(session_id, {})
        if not session_data:
            return

        center_pos = session_data.get("center_pos", {"x": 0, "y": 100, "z": 0})
        border_radius = runtime["border_radius"]
        damage_per_second = runtime["border_damage_per_second"]

        for p in runtime["players"]:
            if p in self.server.online_players and p.name in runtime["alive_players"]:
                # 计算玩家到中心的距离
                dx = p.location.x - center_pos["x"]
                dz = p.location.z - center_pos["z"]
                distance = math.sqrt(dx * dx + dz * dz)

                # 如果玩家在边界外，扣血
                if distance > border_radius:
                    # 扣血（每次扣damage_per_second点血，每秒扣1次）
                    self.server.dispatch_command(self.server.command_sender, f"damage {p.name} {damage_per_second} magic")
                    if p.health <= 0:
                        p.send_message("§c你因在边界外而死亡！")

    def show_border_particles(self, session_id):
        """显示边界粒子效果"""
        runtime = self.game_sessions[session_id]
        if runtime["state"] != GameState.RUNNING:
            return

        session_data = self.plugin_config.get("sessions", {}).get(session_id, {})
        if not session_data:
            return

        # 获取粒子配置
        particle_config = session_data.get("particles", {})
        if not particle_config.get("enabled", True):
            return

        center_pos = session_data.get("center_pos", {"x": 0, "y": 100, "z": 0})
        border_radius = runtime["border_radius"]

        # 从配置文件读取粒子参数
        particle_type = particle_config.get("particle_type", "minecraft:falling_border_dust_particle")
        particle_height = particle_config.get("particle_height", 10)
        particle_y_offset = particle_config.get("particle_y_offset", -48)
        horizontal_step = particle_config.get("horizontal_step", 2)
        vertical_step = particle_config.get("vertical_step", 1)
        view_distance = particle_config.get("view_distance", 4)

        # 计算边界的四个角
        x_min = center_pos["x"] - border_radius
        x_max = center_pos["x"] + border_radius
        z_min = center_pos["z"] - border_radius
        z_max = center_pos["z"] + border_radius

        # 计算Y轴范围
        y_start = center_pos['y'] + particle_height
        y_end = center_pos['y'] + particle_y_offset

        # 获取在线玩家
        players = [p for p in runtime["players"] if p in self.server.online_players]
        if not players:
            return

        # 为每个玩家生成粒子
        for player in players:
            player_x = player.location.x
            player_z = player.location.z

            # 计算玩家视野范围内的边界范围
            x_range_start = max(int(x_min), int(player_x - view_distance))
            x_range_end = min(int(x_max), int(player_x + view_distance))
            z_range_start = max(int(z_min), int(player_z - view_distance))
            z_range_end = min(int(z_max), int(player_z + view_distance))

            # 生成上边和下边的粒子（在玩家视野范围内）
            for x in range(x_range_start, x_range_end + 1, horizontal_step):
                for y in range(y_start, y_end, -vertical_step):
                    player.spawn_particle(particle_type, x, y, z_max)
                    player.spawn_particle(particle_type, x, y, z_min)

            # 生成左边和右边的粒子（在玩家视野范围内）
            for z in range(z_range_start, z_range_end + 1, horizontal_step):
                for y in range(y_start, y_end, -vertical_step):
                    player.spawn_particle(particle_type, x_min, y, z)
                    player.spawn_particle(particle_type, x_max, y, z)
