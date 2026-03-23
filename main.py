import json
import math
import os
import random
import re
import time

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import ComponentType
from astrbot.api.star import Context, Star, register
from astrbot.core.message.message_event_result import MessageChain


@register("可爱の水水の可爱のbot", "Waterwzy", "一个简单的 Hello World 插件", "1.2.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 获取插件目录的路径
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))

    def create_user_data(self):
        user = {
            "today_water": 0,
            "total_water": 0,
            "today_hp": 0,
            "total_hp": 0,
            "favorite": 0,
            "buff": [0, 0],
            "has_special_call": False,
            "special_call_type": "",
            "special_call_random": 0,
            "special_call_content": "",
            "currency": 0,
        }
        return user

    def generate_buff_description(self, buff, waterlist):
        name, level = buff
        des_str = "你今日获得的buff是："
        des_str += waterlist["buff_text_list"][name]["name"]
        des_str += "\n该buff的效果是:"
        des_str += waterlist["buff_text_list"][name]["content"][level]
        des_str += f"\n该buff消耗货币{waterlist['buff_text_list'][name]['count'][level]}，可以通过指令“买水水”获得货币详情。"
        return des_str

    def random_buff(self, user_currency, waterlist):
        buff_list = []
        for i in range(1, waterlist["buff_num"] + 1):
            for level in range(1, 4):
                buff_list.append({"buff": (i, level), "chance": 0})
                if user_currency >= 2 * waterlist["buff_text_list"][i]["count"][level]:
                    buff_list[-1]["chance"] = 3
                elif (
                    user_currency
                    >= 1.5 * waterlist["buff_text_list"][i]["count"][level]
                ):
                    buff_list[-1]["chance"] = 2
                elif user_currency >= waterlist["buff_text_list"][i]["count"][level]:
                    buff_list[-1]["chance"] = 1
        chance_list = [item["chance"] for item in buff_list]
        buff_object = random.choices(buff_list, weights=chance_list, k=1)[0]["buff"]

        return buff_object

    def get_buff(self, user: int, waterlist: dict):
        user_s = str(user)
        res = waterlist["user_data"].get(user_s, {}).get("buff", False)
        if res == [0, 0]:
            res = False
        return res

    def is_legal_songs(self, name: str):
        target_path = "data/plugins/astrbot_plugin_test/AI"
        for item in os.listdir(target_path):
            root, _ = os.path.splitext(item)
            if root == name:
                return item
        return None

    def get_all_songs(self):
        target_path = "data/plugins/astrbot_plugin_test/AI"
        target_str = ""
        for i, item in enumerate(os.listdir(target_path)):
            name, _ = os.path.splitext(item)
            target_str += str(i + 1) + "." + name + "\n"
        target_str += '（输入 "翻唱 具体歌名"以点歌）'
        return target_str

    def is_special_call(self, user_id: int, waterlist):
        user_s = str(user_id)
        if waterlist["user_data"].get(user_s, {}).get("has_special_call", None):
            return waterlist["user_data"][user_s]
        return None

    def add_favorite(self, favorite_num: int, favorite_user: int, waterlist) -> None:

        more = 1.0
        buff = self.get_buff(favorite_user, waterlist)
        if buff:
            name, level = buff
            if name != 2:
                pass
            elif level == 1:
                more = 1.5
            elif level == 2:
                more = 2.0
            elif level == 3:
                more = 3.0

        favorite_num *= more
        favorite_num = int(favorite_num)

        user_s = str(favorite_user)
        if user_s not in waterlist["user_data"]:
            waterlist["user_data"][user_s] = self.create_user_data()
        if waterlist["user_data"][user_s]["favorite"] + favorite_num > 2000:
            waterlist["user_data"][user_s]["currency"] += (
                waterlist["user_data"][user_s]["favorite"] + favorite_num - 2000
            )
            waterlist["user_data"][user_s]["favorite"] = 2000
        else:
            waterlist["user_data"][user_s]["favorite"] += favorite_num

        self.write_water(waterlist)
        return

    def is_at(self, msg_chain: list[Comp.BaseMessageComponent], bot_id: int) -> bool:
        for msg in msg_chain:
            if not isinstance(msg, Comp.BaseMessageComponent):
                continue
            if msg.type is ComponentType.At:
                qq = getattr(msg, "qq", None)
                logger.info(f"检测到含有@消息的消息，消息qq：{qq}")
                if int(qq) == bot_id:  # 3. 统一转字符串
                    return True
        return False

    def is_float(self, target) -> bool:
        try:
            float(target)
            return True
        except ValueError:
            return False

    def is_int(self, target) -> bool:
        try:
            int(target)
            return True
        except ValueError:
            return False

    def add_water(self, count: int, waterlist, user_id: int):
        user_s = str(user_id)
        if user_s not in waterlist["user_data"]:
            waterlist["user_data"][user_s] = self.create_user_data()
        if waterlist["user_data"][user_s]["today_water"] == 3:
            return None
        count = min(count, 3 - waterlist["user_data"][user_s]["today_water"])
        waterlist["user_data"][user_s]["today_water"] += count
        today = waterlist["user_data"][user_s]["today_water"]
        waterlist["user_data"][user_s]["total_water"] += count
        total = waterlist["user_data"][user_s]["total_water"]
        return (today, total)

    def get_favorite(self, id: int, waterlist):
        user_s = str(id)
        if user_s in waterlist["user_data"]:
            return waterlist["user_data"][user_s]["favorite"]
        return 0

    def get_m_kill(self, waterlist):
        max = -math.inf
        max_id = None
        min = math.inf
        min_id = None
        for id, user in waterlist["user_data"].items():
            if user["today_hp"] != 0 and user["today_hp"] > max:
                max = user["today_hp"]
                max_id = int(id)
            if user["today_hp"] != 0 and user["today_hp"] < min:
                min = user["today_hp"]
                min_id = int(id)
        return (max, max_id, min, min_id)

    def clear_user_data(self, waterlist):
        for user in waterlist["user_data"].values():
            user["today_water"] = 0
            user["today_hp"] = 0
            user["buff"] = [0, 0]
        return waterlist

    async def check_date_update(self):
        waterlist = self.create_waterlist()
        if (
            waterlist["date_mon"] != time.localtime(time.time()).tm_mon
            or waterlist["date_day"] != time.localtime(time.time()).tm_mday
        ):
            try:
                import random

                yesterday_water_hp = waterlist["water_boss"]["today_hp"]
                (
                    yesterday_max_hp,
                    yesterday_max_id,
                    yesterday_min_hp,
                    yesterday_min_id,
                ) = self.get_m_kill(waterlist)
                waterlist["date_mon"] = time.localtime(time.time()).tm_mon
                waterlist["date_day"] = time.localtime(time.time()).tm_mday
                waterlist["water_boss"]["now_hp"] = (
                    waterlist["water_boss"]["today_hp"]
                    + waterlist["water_boss"]["hp_add_of_yesterday"]
                )
                waterlist["water_boss"]["today_hp"] = waterlist["water_boss"]["now_hp"]
                waterlist["water_boss"]["hp_add_of_yesterday"] = -5
                waterlist = self.clear_user_data(waterlist)
                chain = [
                    Comp.Plain(
                        f"=====昨日打水总计=====\n昨日血量:{yesterday_water_hp}\n昨日打水最多: "
                    ),
                    Comp.At(qq=yesterday_max_id),
                    Comp.Plain(f"({yesterday_max_hp})\u200b\n昨日打水最少:"),
                    Comp.At(qq=yesterday_min_id),
                    Comp.Plain(
                        f"({yesterday_min_hp})\u200b\n今日更新血量:{waterlist['water_boss']['today_hp']}"
                    ),
                ]
                random.seed(time.time())
                await self.context.send_message(
                    waterlist["message_session"], MessageChain(chain)
                )
                self.write_water(waterlist)
            except Exception as e:
                logger.error(f"catch error in checking update:{e}")
                logger.exception(e)

    def create_waterlist(self):

        try:
            # 使用绝对路径
            file_path = os.path.join(self.plugin_dir, "newlist.json")

            logger.info(f"尝试读取文件: {file_path}")

            with open(file_path, encoding="utf-8") as f:
                bot_data = json.load(f)

            logger.info("成功加载数据")
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {e}")
            # 可以在这里创建默认文件或返回空列表
            return {}
        except Exception as e:
            logger.error(f"读取水井数据出错: {e}")
            return {}

        return bot_data

    def write_water(self, waterlist):

        # 使用绝对路径
        file_path = os.path.join(self.plugin_dir, "newlist.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(waterlist, f, indent=4)

        logger.info("成功写入水井数据")

    async def initialize(self):
        """插件初始化时检查文件是否存在"""
        file_path = os.path.join(self.plugin_dir, "newlist.json")

        if not os.path.exists(file_path):
            logger.warning(f"bot文件不存在: {file_path}")

    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令"""
        user_name = event.get_sender_name()
        message_str = event.message_str
        message_chain = event.get_messages()
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!")

    """
    @filter.on_waiting_llm_request()
    async def stop_group(self, event: AstrMessageEvent):
        if event.message_obj.group == None :
            return
        if event.message_obj.group.group_id == "1012575925" :
            event.stop_event()
    """

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def water_in_group(self, event: AstrMessageEvent):
        group_id = event.get_group_id()
        if group_id != "1012575925":
            return

        """打水功能"""
        await self.check_date_update()
        message_str = event.message_str.strip()

        event.get_sender_name()
        waterlist = self.create_waterlist()
        sender_id = int(event.get_sender_id())  # int
        user_s = event.get_sender_id()  # str

        waterlist["message_session"] = event.unified_msg_origin

        # 修正条件判断
        if message_str == "打水" or message_str == "打淼" or message_str == "打沝":
            if message_str == "打水":
                count = 1
            elif message_str == "打沝":
                count = 2
            elif message_str == "打淼":
                count = 3
            result = self.add_water(count, waterlist, sender_id)
            if result is None:
                chain = [
                    Comp.At(qq=sender_id),
                    Comp.Plain("\u200b 打水失败，每日打水上限是三次喵！"),
                ]
                yield event.chain_result(chain)
            else:
                today, total = result
                chain = [
                    Comp.At(qq=sender_id),
                    Comp.Plain(
                        f"\u200b 打水成功！\n你今日打水{today}次，总计打水{total}次。"
                    ),
                ]
                if message_str == "打水":
                    self.add_favorite(3, sender_id, waterlist)
                else:
                    self.add_favorite(9, sender_id, waterlist)
                yield event.chain_result(chain)
        elif message_str == "打水水":
            if waterlist["water_boss"]["now_hp"] != 0:
                if (
                    user_s in waterlist["user_data"]
                    and waterlist["user_data"][user_s]["today_hp"] != 0
                ):
                    yield event.plain_result("你今天已经打过水水了，不要再打了喵！")
                    return
                kill_hp = math.ceil(random.random() * 10)
                kill_more = (
                    round(
                        random.uniform(1.1, 10.0)
                        + max(
                            0, min(self.get_favorite(sender_id, waterlist) / 100, 10)
                        ),
                        1,
                    )
                    if random.randint(0, 19)
                    else 1
                )

                buff = self.get_buff(sender_id, waterlist)
                if buff:
                    name, level = buff
                    if name != 1:
                        pass
                    elif level == 1:
                        kill_more += 0.5
                    elif level == 2:
                        kill_more += 1.3
                    elif level == 3:
                        kill_more += 2.4

                kill_more = min(kill_more, 15.0)

                fin_kill_hp = round(kill_hp * kill_more, 1)

                if user_s not in waterlist["user_data"]:
                    waterlist["user_data"][user_s] = self.create_user_data()
                waterlist["user_data"][user_s]["total_hp"] += round(fin_kill_hp / 10, 1)

                if kill_hp * kill_more > waterlist["water_boss"]["now_hp"]:
                    add_out_str = f"\n(伤害溢出，原始伤害{fin_kill_hp})"
                    fin_kill_hp = waterlist["water_boss"]["now_hp"]
                else:
                    add_out_str = ""
                waterlist["water_boss"]["now_hp"] = round(
                    waterlist["water_boss"]["now_hp"] - fin_kill_hp, 1
                )
                if waterlist["water_boss"]["now_hp"] == 0:
                    waterlist["water_boss"]["hp_add_of_yesterday"] = 10
                add_str = "" if kill_more == 1 else "（暴击）"
                add_str_after = (
                    ""
                    if waterlist["water_boss"]["now_hp"] != 0
                    else "(今天的水水被打死了！)"
                )

                waterlist["user_data"][user_s]["today_hp"] = fin_kill_hp

                self.add_favorite(int(-fin_kill_hp * 0.1), sender_id, waterlist)

                chain = [
                    Comp.At(qq=event.get_sender_id()),
                    Comp.Plain(
                        f"\u200b\n 打水水成功，你今天给水水造成的伤害值是{fin_kill_hp}{add_str}（{waterlist['water_boss']['now_hp']}/{waterlist['water_boss']['today_hp']}）。{add_str_after}{add_out_str}"
                    ),
                ]
                yield event.chain_result(chain)
            else:
                yield event.plain_result("今天的水水已经被打死了！明天再来吧。")
        elif message_str.startswith("灌水"):
            if user_s not in waterlist["user_data"]:
                yield event.plain_result("你还不能灌水，需要先去打水水！")
                return
            user_info = waterlist["user_data"][user_s]
            if message_str == "灌水":
                yield event.plain_result(
                    f"你现在的灌水可用值：{user_info['total_hp']}（输入“灌水 具体数值”以增加水水血量，打水伤害与灌水可用值换算比为10:1）"
                )
            elif (not self.is_float(message_str[3:])) or round(
                float(message_str[3:]), 1
            ) <= 0:
                yield event.plain_result(
                    "参数错误！（请输入正浮点数，灌水后需要有空格）"
                )
            else:
                add_hp = round(float(message_str[3:]), 1)
                if user_info["total_hp"] < add_hp or (
                    waterlist["water_boss"]["now_hp"] == 0
                    and user_info["total_hp"] - 1 < add_hp
                ):
                    yield event.plain_result(
                        f"你现在无法增加这么多的血量，你现在的血量可用值为{user_info['total_hp']}（复活水水需要额外1点血量）"
                    )
                    return
                extra_reborn = 0
                if waterlist["water_boss"]["now_hp"] == 0:
                    extra_reborn = 1
                waterlist["water_boss"]["now_hp"] = round(
                    waterlist["water_boss"]["now_hp"] + add_hp, 1
                )
                user_info["total_hp"] = round(
                    user_info["total_hp"] - add_hp - extra_reborn, 1
                )

                self.add_favorite(int(add_hp * 1.5), sender_id, waterlist)

                chain = [
                    Comp.At(qq=event.get_sender_id()),
                    Comp.Plain(
                        f"\u200b\n灌水成功。你给水水增加的血量是{add_hp},水水目前血量{waterlist['water_boss']['now_hp']}"
                    ),
                ]
                yield event.chain_result(chain)
        elif re.search("好感", message_str) is not None and self.is_at(
            event.message_obj.message, 3516791958
        ):
            logger.info("触发好感度提示")
            if user_s in waterlist["user_data"]:
                chain = [
                    Comp.At(qq=sender_id),
                    Comp.Plain(
                        f"\u200b 你的好感度是{waterlist['user_data'][user_s]['favorite']}喵"
                    ),
                ]
                if 0 < waterlist["user_data"][user_s]["favorite"] <= 30:
                    chain.append(
                        Comp.Image.fromFileSystem(
                            "data/plugins/astrbot_plugin_test/images/low-favorite.jpg"
                        )
                    )
                elif -200 <= waterlist["user_data"][user_s]["favorite"] <= 0:
                    chain.append(Comp.Plain("\u200b 杂鱼杂鱼~"))
                    chain.append(
                        Comp.Image.fromFileSystem(
                            "data/plugins/astrbot_plugin_test/images/low-low-favorite.jpg"
                        )
                    )
                elif waterlist["user_data"][user_s]["favorite"] >= 300:
                    chain.append(
                        Comp.Image.fromFileSystem(
                            "data/plugins/astrbot_plugin_test/images/high-favorite.jpg"
                        )
                    )
                elif waterlist["user_data"][user_s]["favorite"] < -200:
                    chain = [
                        Comp.At(qq=sender_id),
                        Comp.Plain(
                            f"诶……你的好感度是{waterlist['user_data'][user_s]['favorite']}喵？不会是水水吃水煮黑背鲈吃中毒看错了吧……"
                        ),
                        Comp.Image.fromFileSystem(
                            "data/plugins/astrbot_plugin_test/images/low-low-low-favorite.jpg"
                        ),
                    ]
                yield event.chain_result(chain)
                return
            chain = [
                Comp.Image.fromFileSystem(
                    "data/plugins/astrbot_plugin_test/images/low-favorite.jpg"
                )
            ]
            yield event.chain_result(chain)

        elif message_str == "翻唱列表":
            yield event.plain_result(self.get_all_songs())
        elif message_str.startswith("翻唱"):
            tragets = message_str[2:].strip()
            if self.is_legal_songs(tragets) is None:
                yield event.plain_result(
                    "列表里没有这首歌，你可以通过 翻唱列表 查询可以翻唱的曲目"
                )
                return
            full_name = self.is_legal_songs(tragets)
            chain = [
                Comp.Record(file="data/plugins/astrbot_plugin_test/AI/" + full_name)
            ]
            yield event.chain_result(chain)

        elif message_str == "今日水水":
            chain = [
                Comp.At(qq=sender_id),
                Comp.Plain(
                    f"\u200b  bot还活着喵！\n水水目前状态：{waterlist['water_boss']['now_hp']}/{waterlist['water_boss']['today_hp']}.预计明日血量为：{waterlist['water_boss']['today_hp'] + waterlist['water_boss']['hp_add_of_yesterday']}."
                ),
            ]
            yield event.chain_result(chain)

        elif message_str == "buff":  # 获取buff
            logger.debug("进入buff区间")
            if self.get_buff(sender_id, waterlist):
                return
            logger.debug(f"确认用户{sender_id}今日无buff，正在获取buff")
            if user_s not in waterlist["user_data"]:
                waterlist["user_data"][user_s] = self.create_user_data()
            currency = waterlist["user_data"][user_s]["currency"]
            buff = self.random_buff(currency, waterlist)
            waterlist["user_data"][user_s]["buff"] = buff
            obc, level = buff
            waterlist["user_data"][user_s]["currency"] -= waterlist["buff_text_list"][
                obc
            ]["count"][level]
            chain = [
                Comp.At(qq=sender_id),
                Comp.Plain(self.generate_buff_description(buff, waterlist)),
            ]
            yield event.chain_result(chain)
            #'''
        elif message_str == "水水启动":
            TMPL = """
                    <div style="font-size: 32px;">
                    <h1 style="color: black">水水bot功能列表（v1.2.0）</h1>

                    <ul>
                    {% for item in items %}
                        <li>{{ item }}</li>
                    {% endfor %}
                    </div>
                    """
            func_text = [
                "打水（每日打卡功能，每日最多三次）\n",
                "打沝（同上，可以一次性打水两次）\n",
                "打淼（同上，可以一次性打水三次）",
                "打水水（攻击水水boss（每日刷新），随机造成伤害，每日一次）\n",
                "灌水（增加水水boss的血量）\n",
                "好感（需要@水井，展示你当前的好感度）\n",
                "翻唱列表（获取流萤翻唱曲目）\n",
                "翻唱（获取特定歌曲翻唱音频）\n",
                "今日水水（检查bot运行状态以及水水状态）\n",
                "buff（获取今日buff，可以带来打水水或者好感增加的收益，部分buff需要货币购买）\n",
                "水水启动（你现在看的就是~）\n",
                "买水水（将好感度转换为货币）\n？？（猜猜看是什么？）",
            ]
            img = await self.html_render(
                TMPL, {"items": func_text}
            )  # 第二个参数是 Jinja2 的渲染数据
            yield event.image_result(img)
        elif message_str.startswith("买水水"):
            if user_s not in waterlist["user_data"]:
                yield event.plain_result(
                    "用户不存在，请与bot有效互动后创建用户信息（输入“水水启动”以查看bot功能）"
                )
                return
            if message_str == "买水水":
                rep_str = f"你现在的货币是{waterlist['user_data'][user_s]['currency']}，输入“买水水 数值”利用好感度兑换一定量的货币"
                yield event.plain_result(rep_str)
                return
            if (
                message_str[3] != " "
                or not self.is_int(message_str[4:])
                or int(message_str[4:]) < 0
            ):
                rep_str = "参数错误！（买水水需要增加空格，请确认输入的数值是正整数）"
                yield event.plain_result(rep_str)
                return
            get_currency = int(message_str[4:])
            if waterlist["user_data"][user_s]["favorite"] - get_currency < 0:
                rep_str = "你不能兑换这么多货币，不然好感度就要为负数了！"
                yield event.plain_result(rep_str)
                return
            waterlist["user_data"][user_s]["favorite"] -= get_currency
            waterlist["user_data"][user_s]["currency"] += get_currency
            rep_str = f"兑换成功。你目前的好感度为{waterlist['user_data'][user_s]['favorite']}，货币数量为{waterlist['user_data'][user_s]['currency']}"
            yield event.plain_result(rep_str)

        # 注意：这里的逻辑只能放在最后，新增功能都上去！！！

        elif self.is_special_call(sender_id, waterlist) is not None:
            logger.info("确认为特殊用户")
            target = self.is_special_call(sender_id, waterlist)
            randoms = random.randint(1, target["special_call_random"])
            if randoms == 1:
                self.add_favorite(1, sender_id, waterlist)
                if target["special_call_type"] == "text":
                    yield event.plain_result(f"{target['special_call_content']}")
                elif target["special_call_type"] == "image":
                    yield event.image_result(target["special_call_content"])
                """
                elif target['special_call_type'] == "poke" :
                    poke = Comp.Poke(
                        qq = sender_id
                    )
                    chain = [poke]
                    yield event.chain_result(chain)
                """
            else:
                logger.info(f"call_random not worked,now random int:{randoms}")

        self.write_water(waterlist)

    async def terminate(self):
        """插件销毁方法"""
