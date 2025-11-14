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

    def is_special_call(self,user_id:int,waterlist:list)  :
        for special_user in waterlist['special_call_list'] :
            if user_id == special_user['call_id'] :
                return special_user
        return None


    def is_float(self,target) ->bool :
        try :
            float(target)
            return True
        except ValueError :
            return False

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
        random.seed(time.time())
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

        if group_id != "1012575925" :
            return

        waterlist['message_session'] = event.unified_msg_origin

        # 修正条件判断
        if message_str == '打水' :  
            try:
                
                sender_count = 0
                today_count = 0
                flag = 0
                for user in waterlist['today_water_list'] :
                    if user['id'] == int(event.get_sender_id()) :
                        #'''
                        if user['count'] >= 3 :
                            yield event.plain_result(f"@{sender} 你今天已经打水过3次了，不要再打水了！")
                            return
                        #'''
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
                chian = [
                    Comp.At(qq=event.get_sender_id()),
                    Comp.Plain(f"\u200b\n打水成功！你今日打水{today_count}次。\n你总计打水{sender_count}次。")
                ]
                yield event.chain_result(chian)
            except Exception as e:
                logger.error(f"打水操作出错: {e}")
                yield event.plain_result("打水失败，请稍后重试")
        elif message_str == '打水水' :
            if waterlist['water_boss']['now_hp'] != 0:
                for user in waterlist['water_boss']['kill_list'] :
                    if user['id'] == int(event.get_sender_id()) :
                        yield event.plain_result("你今天已经打过水水了，不要再打了喵！")
                        return
                kill_hp = math.ceil(random.random()*10)
                kill_more = round(random.uniform(1.1 , 10.0 ) , 1) if random.randint(0,3) else 1
                fin_kill_hp = round( kill_hp*kill_more , 1 )

                flag = 0
                for user_info in waterlist['water_boss']['total_list'] :
                    if user_info['id'] == sender_id :
                        user_info['hp'] = round(fin_kill_hp/10+user_info['hp'] , 1)
                        flag = 1
                        break
                if flag == 0:
                    waterlist['water_boss']['total_list'].append({"id":sender_id,"hp":round(fin_kill_hp/10 , 1)})

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
        elif message_str.startswith("灌水") :
            flag = 0
            for add_user in waterlist['water_boss']['total_list'] :
                if sender_id == add_user['id'] :
                    flag = 1
                    user_info = add_user
                    break
            if flag == 0 :
                yield event.plain_result(f"你还不能灌水，需要先去打水水！")
                return
            if message_str == "灌水" :
                yield event.plain_result(f"你现在的灌水可用值：{user_info['hp']}（输入“灌水 具体数值”以增加水水血量，打水伤害与灌水可用值换算比为10:1）")
            elif (not self.is_float(message_str[ 3 : ]) ) or round(float( message_str[3 : ]) , 1) <= 0 :
                yield event.plain_result(f"参数错误！（请输入正浮点数）")
            else :
                add_hp = round(float( message_str[3 : ]) , 1)
                if user_info['hp'] < add_hp or (waterlist['water_boss']['now_hp'] == 0 and user_info['hp'] -1 < add_hp):
                    yield event.plain_result(f"你现在无法增加这么多的血量，你现在的血量可用值为{user_info['hp']}（复活水水需要额外1点血量）")
                    return
                extra_reborn = 0
                if waterlist['water_boss']['now_hp'] == 0:
                    extra_reborn = 1
                waterlist['water_boss']['now_hp'] = round(waterlist['water_boss']['now_hp']+add_hp , 1 )
                user_info['hp'] = round(user_info['hp'] - add_hp -extra_reborn, 1 )
                chain = [
                    Comp.At(qq = event.get_sender_id()),
                    Comp.Plain(f"\n灌水成功。你给水水增加的血量是{add_hp},水水目前血量{waterlist['water_boss']['now_hp']}")
                ]
                yield event.chain_result(chain)
        elif self.is_special_call(sender_id,waterlist) is not None :
            logger.info(f"确认为特殊用户")
            target = self.is_special_call(sender_id,waterlist)
            randoms = random.randint(1,target['call_random'])
            if randoms == 1:
                yield event.plain_result(f"{target['call_str']}")
            else :
                logger.info(f"call_random not worked,now random int:{randoms}")
                
        self.write_water(waterlist)
            
    async def terminate(self):
        """插件销毁方法"""