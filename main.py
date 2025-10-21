import os
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import json
import time

@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 获取插件目录的路径
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        waterlist = self.create_waterlist()
        if waterlist['date_mon'] != time.localtime(time.time()).tm_mon or waterlist['date_day'] != time.localtime(time.time()).tm_mday :
            waterlist['today_water_list'] = []
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
        message_str = event.message_str.strip()
        group_id = event.get_group_id()
        sender = event.get_sender_name()
        
        # 修正条件判断
        if message_str == '打水' and group_id == "1012575925":  
            try:
                waterlist = self.create_waterlist()
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
                self.write_water(waterlist)
                yield event.plain_result(f"@{sender}\n打水成功！你今日打水{today_count}次。\n你总计打水{sender_count}次。")
            except Exception as e:
                logger.error(f"打水操作出错: {e}")
                yield event.plain_result("打水失败，请稍后重试")
        elif message_str == '打水水' and group_id == "1012575925" :
            yield event.plain_result(f"@{sender} 水！水！不！能！打！！！！")

    async def terminate(self):
        """插件销毁方法"""