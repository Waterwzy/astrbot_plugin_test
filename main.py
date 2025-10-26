import os
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.core.message.message_event_result import MessageChain
import json
import time
import random
import math
import re

@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 获取插件目录的路径
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        

    async def check_date_update(self) :
        waterlist = self.create_waterlist()
        if waterlist['date_mon'] != time.localtime(time.time()).tm_mon or waterlist['date_day'] != time.localtime(time.time()).tm_mday :
            waterlist['today_water_list'] = []
            waterlist['date_mon'] = time.localtime(time.time()).tm_mon
            waterlist['date_day'] = time.localtime(time.time()).tm_mday
            waterlist['water_boss']['now_hp'] = waterlist['water_boss']['today_hp'] + waterlist['water_boss']['hp_add_of_yesterday']
            waterlist['water_boss']['today_hp'] = waterlist['water_boss']['now_hp']
            waterlist['water_boss']['kill_list'] = []
            waterlist['water_boss']['hp_add_of_yesterday'] = -5
            waterlist['today_wife']['wife_id'] = 0
        random.seed(time.time())
        if not waterlist['today_wife']['wife_id'] and time.time() - waterlist['today_wife']['last_ask_time'] >= 90:
            chain = [
                Comp.Plain("今日老婆")
            ]
            if waterlist['message_session'] :
                waterlist['today_wife']['last_ask_time'] = time.time()
                await self.context.send_message(waterlist['message_session'],MessageChain(chain))
        self.write_water(waterlist)

    def create_waterlist(self):

        try:
            # 使用绝对路径
            file_path = os.path.join(self.plugin_dir, 'datalist.json')
            
            logger.info(f"尝试读取文件: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                bot_data = json.load(f)
            
            logger.info(f"成功加载数据")
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {e}")
            # 可以在这里创建默认文件或返回空列表
            return []
        except Exception as e:
            logger.error(f"读取水井数据出错: {e}")
            return []
            
        return bot_data
    
    def write_water(self,waterlist) :
        
            # 使用绝对路径
        file_path = os.path.join(self.plugin_dir, 'datalist.json')
                  
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(waterlist,f,indent=4)
            
        logger.info(f"成功写入水井数据")


    async def initialize(self):
        """插件初始化时检查文件是否存在"""
        file_path = os.path.join(self.plugin_dir, 'datalist.json')
        
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

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def water_in_group(self, event: AstrMessageEvent):
        
        """打水功能"""
        await self.check_date_update()
        message_str = event.message_str.strip()
        group_id = event.get_group_id()
        sender = event.get_sender_name()
        waterlist = self.create_waterlist()
        sender_id = int(event.get_sender_id()) #int

        waterlist['message_session'] = event.unified_msg_origin

        qq_match = re.search(r'【[^】]+】\((\d+)\)', message_str.strip())
        if qq_match:
            logger.info("匹配到 QQ 号码，可以设置")
            target_qq = int(qq_match.group(1))

        

        # 修正条件判断
        if message_str == '打水' and group_id == "1012575925":  
            try:
                
                sender_count = 0
                today_count = 0
                flag = 0
                for user in waterlist['today_water_list'] :
                    if user['id'] == int(event.get_sender_id()) :
                        if user['count'] >= 3 :
                            yield event.plain_result(f"@{sender} 你今天已经打水过3次了，不要再打水了！")
                            return
                        user['count']+=1
                        today_count = user['count']
                        flag =1 
                        break
                if flag == 0 :
                    waterlist['today_water_list'].append({"id":int(event.get_sender_id()),"count":1})
                    today_count = 1
                flag = 0
                for user in waterlist['waterlist'] :
                    if user['id'] == int(event.get_sender_id()) :
                        user['count']+=1
                        sender_count = user['count']
                        flag = 1
                        break

                if flag == 0:
                    waterlist['waterlist'].append({"id":int(event.get_sender_id()),"count":1})
                    sender_count = 1
     
                logger.info(f"打水成功，群组: {group_id}")
                #self.write_water(waterlist)
                yield event.plain_result(f"@{sender}\n打水成功！你今日打水{today_count}次。\n你总计打水{sender_count}次。")
            except Exception as e:
                logger.error(f"打水操作出错: {e}")
                yield event.plain_result("打水失败，请稍后重试")
        elif message_str == '打水水' and group_id == "1012575925" :
            if waterlist['water_boss']['now_hp'] != 0:
                for user in waterlist['water_boss']['kill_list'] :
                    if user['id'] == int(event.get_sender_id()) :
                        yield event.plain_result("你今天已经打过水水了，不要再打了喵！")
                        return
                kill_hp = math.ceil(random.random()*10)
                kill_more = round(random.uniform(1.1 , 10.0 ) , 1) if random.randint(0,1) else 1
                fin_kill_hp = round( kill_hp*kill_more , 1 )
                if kill_hp*kill_more > waterlist['water_boss']['now_hp'] :
                    add_out_str = f'\n(伤害溢出，原始伤害{fin_kill_hp})'
                    fin_kill_hp = waterlist['water_boss']['now_hp']
                else :
                    add_out_str = ''
                waterlist['water_boss']['now_hp'] = round (waterlist['water_boss']['now_hp'] - fin_kill_hp ,1)
                if waterlist['water_boss']['now_hp'] == 0:
                        waterlist['water_boss']['hp_add_of_yesterday'] = 10
                add_str = '' if kill_more == 1 else '（暴击）'
                add_str_after = '' if waterlist['water_boss']['now_hp'] != 0 else '(今天的水水被打死了！)'
                waterlist['water_boss']['kill_list'].append({"id":int(event.get_sender_id()),"hp":fin_kill_hp})
                chain = [
                    Comp.At(qq=event.get_sender_id()),
                    Comp.Plain(f" 打水水成功，你今天给水水造成的伤害值是{fin_kill_hp}{add_str}（{waterlist['water_boss']['now_hp']}/{waterlist['water_boss']['today_hp']}）。{add_str_after}{add_out_str}")
                ]
                yield event.chain_result(chain)
                #self.write_water(waterlist)
            else :
                yield event.plain_result("今天的水水已经被打死了！明天再来吧。")
        elif sender_id == waterlist['today_wife']['bot_id'] and event.is_at_or_wake_command and qq_match:
            waterlist['today_wife']['wife_id'] = target_qq
            waterlist['today_wife']['call_name'] = "老婆"
            logger.info("载入老婆信息成功")
            #self.write_water(waterlist)
        elif sender_id == waterlist['today_wife']['bot_id'] and event.is_at_or_wake_command and qq_match:
            waterlist['today_wife']['wife_id'] = target_qq
            waterlist['today_wife']['call_name'] = "老公"
            logger.info("载入老公信息成功")
            #self.write_water(waterlist)
        elif waterlist['today_wife']['wife_id'] and sender_id == waterlist['today_wife']['wife_id'] :
            if random.randint(1,waterlist['today_wife']['call_wife_random']) == 1 :
                yield event.plain_result(f"{waterlist['today_wife']['call_name']}~")
        self.write_water(waterlist)
            
    async def terminate(self):
        """插件销毁方法"""