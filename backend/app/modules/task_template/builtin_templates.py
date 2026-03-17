from .schemas import (
    TaskTemplateCreate,
    TemplateSchemaCreate,
    TemplateScriptCreate,
    TemplateCronSuggestionCreate
)


def get_builtin_templates():
    """获取所有内置模板"""
    return [
        # ========== 天气推送模板 ==========
        {
            "template": TaskTemplateCreate(
                template_id="weather-push",
                name="天气推送",
                version="1.0.0",
                author="MyTool Team",
                description="每天定时推送天气预报到指定通知渠道，支持穿衣建议和未来3天预报",
                category="个人助理类",
                tags=["天气", "提醒", "个人助理"],
                difficulty="入门",
                icon="🌤"
            ),
            "schema": TemplateSchemaCreate(
                template_id="weather-push",
                schema_json={
                    "type": "object",
                    "title": "天气推送配置",
                    "properties": {
                        "city": {
                            "type": "string",
                            "title": "城市名称",
                            "description": "请输入要查询的城市（如：北京、上海、深圳）",
                            "default": "北京",
                            "examples": ["北京", "上海", "深圳", "广州", "杭州"],
                            "required": True
                        },
                        "weather_source": {
                            "type": "string",
                            "title": "天气数据源",
                            "default": "open-meteo",
                            "enum": ["open-meteo", "wttr.in"],
                            "enum_labels": {
                                "open-meteo": "Open-Meteo（免费，无需Key）",
                                "wttr.in": "wttr.in（免费，无需Key）"
                            },
                            "required": True
                        },
                        "notification_channel": {
                            "type": "string",
                            "title": "通知渠道",
                            "default": "webhook",
                            "enum": ["webhook", "bark", "wecom", "feishu", "dingtalk"],
                            "enum_labels": {
                                "webhook": "自定义Webhook",
                                "bark": "Bark（iOS）",
                                "wecom": "企业微信",
                                "feishu": "飞书",
                                "dingtalk": "钉钉"
                            },
                            "required": True
                        },
                        "webhook_url": {
                            "type": "string",
                            "title": "Webhook地址",
                            "placeholder": "https://example.com/webhook",
                            "required": False
                        },
                        "bark_key": {
                            "type": "string",
                            "title": "Bark Key",
                            "placeholder": "xxxxxxxxxxxxxxxxxx",
                            "required": False
                        },
                        "wecom_webhook": {
                            "type": "string",
                            "title": "企业微信Webhook",
                            "placeholder": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
                            "required": False
                        },
                        "show_forecast": {
                            "type": "boolean",
                            "title": "显示未来3天预报",
                            "default": True
                        },
                        "custom_message": {
                            "type": "string",
                            "title": "自定义附加消息",
                            "placeholder": "今天是{weekday}，{city}天气不错！",
                            "default": ""
                        }
                    }
                }
            ),
            "script": TemplateScriptCreate(
                template_id="weather-push",
                script_type="python",
                script_content="""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
import sys
from datetime import datetime

class WeatherPusher:
    def __init__(self, config):
        self.config = config
        self.city = config.get("city", "北京")
        self.weather_source = config.get("weather_source", "open-meteo")
        self.notification_channel = config.get("notification_channel", "webhook")
        self.show_forecast = config.get("show_forecast", True)
        self.custom_message = config.get("custom_message", "")

    def get_weather(self):
        if self.weather_source == "open-meteo":
            return self._get_open_meteo()
        else:
            return self._get_wttr()

    def _get_open_meteo(self):
        city_coords = {
            "北京": (39.9042, 116.4074),
            "上海": (31.2304, 121.4737),
            "深圳": (22.5431, 114.0579),
            "广州": (23.1291, 113.2644),
            "杭州": (30.2741, 120.1551),
        }
        lat, lon = city_coords.get(self.city, (39.9042, 116.4074))
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia/Shanghai&forecast_days=4"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        weather_codes = {
            0: "晴", 1: "大部晴朗", 2: "局部多云", 3: "多云",
            45: "雾", 51: "小毛毛雨", 61: "小雨", 63: "中雨",
            65: "大雨", 71: "小雪", 73: "中雪", 75: "大雪",
            80: "小阵雨", 81: "阵雨", 82: "大阵雨", 95: "雷暴"
        }

        current = data["current"]
        daily = data["daily"]
        forecast = []
        for i in range(1, 4):
            forecast.append({
                "date": daily["time"][i],
                "weather": weather_codes.get(daily["weather_code"][i], "未知"),
                "temp_max": daily["temperature_2m_max"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "rain_prob": daily["precipitation_probability_max"][i]
            })

        return {
            "city": self.city,
            "current": {
                "temp": current["temperature_2m"],
                "humidity": current["relative_humidity_2m"],
                "weather": weather_codes.get(current["weather_code"], "未知"),
                "wind_speed": current["wind_speed_10m"]
            },
            "forecast": forecast
        }

    def _get_wttr(self):
        url = f"https://wttr.in/{self.city}?format=j1"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        current = data["current_condition"][0]
        forecast = []
        for i in range(1, 4):
            if i < len(data["weather"]):
                day = data["weather"][i]
                forecast.append({
                    "date": day["date"],
                    "weather": day["hourly"][0]["lang_zh"][0]["value"] if "lang_zh" in day["hourly"][0] else day["hourly"][0]["weatherDesc"][0]["value"],
                    "temp_max": int(day["maxtempC"]),
                    "temp_min": int(day["mintempC"]),
                    "rain_prob": int(day["hourly"][0]["chanceofrain"])
                })
        return {
            "city": self.city,
            "current": {
                "temp": int(current["temp_C"]),
                "humidity": int(current["humidity"]),
                "weather": current["lang_zh"][0]["value"] if "lang_zh" in current else current["weatherDesc"][0]["value"],
                "wind_speed": current["windspeedKmph"]
            },
            "forecast": forecast
        }

    def build_message(self, weather):
        now = datetime.now()
        date_str = now.strftime("%Y年%m月%d日")
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]
        current = weather["current"]

        lines = [
            f"🌤 {self.city}天气预报",
            f"📅 {date_str} {weekday}",
            "",
            f"📍 当前天气：{current['weather']}",
            f"🌡 温度：{current['temp']}°C",
            f"💧 湿度：{current['humidity']}%",
            f"🌬 风速：{current['wind_speed']} km/h"
        ]

        if current["temp"] < 10:
            lines.append("🧥 建议穿厚外套、羽绒服")
        elif current["temp"] < 20:
            lines.append("🧥 建议穿外套、卫衣")
        else:
            lines.append("👕 建议穿短袖、衬衫")

        if self.show_forecast and weather["forecast"]:
            lines.append("")
            lines.append("📆 未来3天预报：")
            for day in weather["forecast"]:
                lines.append(f"  {day['date']}：{day['weather']} {day['temp_min']}~{day['temp_max']}°C")

        if self.custom_message:
            lines.append("")
            msg = self.custom_message.format(date=date_str, weekday=weekday, city=self.city)
            lines.append(f"💬 {msg}")

        return "\\n".join(lines)

    def send(self, message):
        channel = self.notification_channel
        if channel == "webhook":
            url = self.config.get("webhook_url")
            if url:
                requests.post(url, json={"content": message}, timeout=10)
        elif channel == "bark":
            key = self.config.get("bark_key")
            if key:
                requests.get(f"https://api.day.app/{key}/{message}", timeout=10)
        elif channel == "wecom":
            url = self.config.get("wecom_webhook")
            if url:
                requests.post(url, json={"msgtype": "text", "text": {"content": message}}, timeout=10)
        print(message)

    def run(self):
        weather = self.get_weather()
        message = self.build_message(weather)
        self.send(message)
        return {"status": "success"}

if __name__ == "__main__":
    config = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    pusher = WeatherPusher(config)
    pusher.run()
"""
            ),
            "cron_suggestions": [
                TemplateCronSuggestionCreate(
                    template_id="weather-push",
                    label="每天早上8点",
                    cron_value="0 8 * * *",
                    is_default=True,
                    sort_order=1
                ),
                TemplateCronSuggestionCreate(
                    template_id="weather-push",
                    label="每天早上7点半",
                    cron_value="30 7 * * *",
                    sort_order=2
                ),
                TemplateCronSuggestionCreate(
                    template_id="weather-push",
                    label="每天晚上6点（下班提醒）",
                    cron_value="0 18 * * *",
                    sort_order=3
                )
            ]
        },

        # ========== MySQL备份模板 ==========
        {
            "template": TaskTemplateCreate(
                template_id="mysql-backup",
                name="MySQL全量备份",
                version="1.0.0",
                author="MyTool Team",
                description="MySQL数据库全量备份，自动压缩，保留最近7天",
                category="系统运维类",
                tags=["MySQL", "数据库", "备份"],
                difficulty="入门",
                icon="🗄️"
            ),
            "schema": TemplateSchemaCreate(
                template_id="mysql-backup",
                schema_json={
                    "type": "object",
                    "title": "MySQL备份配置",
                    "properties": {
                        "mysql_host": {"type": "string", "title": "MySQL地址", "default": "localhost", "required": True},
                        "mysql_port": {"type": "number", "title": "MySQL端口", "default": 3306, "required": True},
                        "mysql_user": {"type": "string", "title": "MySQL用户", "default": "root", "required": True},
                        "mysql_password": {"type": "string", "title": "MySQL密码", "required": True},
                        "backup_dir": {"type": "string", "title": "备份目录", "default": "/data/backup/mysql", "required": True},
                        "retention_days": {"type": "number", "title": "保留天数", "default": 7, "required": True}
                    }
                }
            ),
            "script": TemplateScriptCreate(
                template_id="mysql-backup",
                script_type="python",
                script_content="""#!/usr/bin/env python3
import os
import time
import subprocess
import glob
import json
import sys

config = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
backup_dir = config.get("backup_dir", "/data/backup/mysql")
os.makedirs(backup_dir, exist_ok=True)

date_str = time.strftime("%Y%m%d_%H%M%S")
filename = f"mysql_backup_{date_str}.sql.gz"
filepath = os.path.join(backup_dir, filename)

cmd = [
    "mysqldump",
    "-h", config.get("mysql_host", "localhost"),
    "-P", str(config.get("mysql_port", 3306)),
    "-u", config.get("mysql_user", "root"),
    f"-p{config.get('mysql_password', '')}",
    "--all-databases"
]

with open(filepath, "wb") as f:
    p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["gzip"], stdin=p1.stdout, stdout=f)
    p2.wait()
    p1.wait()

retention = config.get("retention_days", 7)
cutoff = time.time() - retention * 86400
for f in glob.glob(os.path.join(backup_dir, "mysql_backup_*.sql.gz")):
    if os.path.getmtime(f) < cutoff:
        os.remove(f)
        print(f"Deleted old backup: {f}")

print(f"Backup completed: {filepath}")
"""
            ),
            "cron_suggestions": [
                TemplateCronSuggestionCreate(
                    template_id="mysql-backup",
                    label="每天凌晨2点",
                    cron_value="0 2 * * *",
                    is_default=True,
                    sort_order=1
                )
            ]
        },

        # ========== Nginx日志清理模板 ==========
        {
            "template": TaskTemplateCreate(
                template_id="nginx-log-clean",
                name="Nginx日志清理",
                version="1.0.0",
                author="MyTool Team",
                description="清理30天前的Nginx访问日志和错误日志",
                category="系统运维类",
                tags=["Nginx", "日志", "清理"],
                difficulty="入门",
                icon="📝"
            ),
            "schema": TemplateSchemaCreate(
                template_id="nginx-log-clean",
                schema_json={
                    "type": "object",
                    "title": "Nginx日志清理配置",
                    "properties": {
                        "log_dir": {"type": "string", "title": "日志目录", "default": "/var/log/nginx", "required": True},
                        "retention_days": {"type": "number", "title": "保留天数", "default": 30, "required": True}
                    }
                }
            ),
            "script": TemplateScriptCreate(
                template_id="nginx-log-clean",
                script_type="python",
                script_content="""#!/usr/bin/env python3
import os
import time
import glob
import json
import sys

config = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
log_dir = config.get("log_dir", "/var/log/nginx")
retention = config.get("retention_days", 30)
cutoff = time.time() - retention * 86400

patterns = [
    "access.log*",
    "error.log*",
    "*.access.log",
    "*.error.log"
]

deleted = 0
for pattern in patterns:
    for f in glob.glob(os.path.join(log_dir, pattern)):
        if os.path.isfile(f) and os.path.getmtime(f) < cutoff:
            os.remove(f)
            print(f"Deleted: {f}")
            deleted += 1

print(f"Total deleted {deleted} files")
"""
            ),
            "cron_suggestions": [
                TemplateCronSuggestionCreate(
                    template_id="nginx-log-clean",
                    label="每周日凌晨6点",
                    cron_value="0 6 * * 0",
                    is_default=True,
                    sort_order=1
                )
            ]
        },

        # ========== 网站可用性监控模板 ==========
        {
            "template": TaskTemplateCreate(
                template_id="website-monitor",
                name="网站可用性监控",
                version="1.0.0",
                author="MyTool Team",
                description="定期检查网站HTTP状态，异常时发送通知",
                category="网络监控类",
                tags=["监控", "网站", "HTTP"],
                difficulty="入门",
                icon="🌐"
            ),
            "schema": TemplateSchemaCreate(
                template_id="website-monitor",
                schema_json={
                    "type": "object",
                    "title": "网站监控配置",
                    "properties": {
                        "url": {"type": "string", "title": "网站URL", "placeholder": "https://example.com", "required": True},
                        "timeout": {"type": "number", "title": "超时时间（秒）", "default": 10},
                        "expected_status": {"type": "number", "title": "期望状态码", "default": 200},
                        "webhook_url": {"type": "string", "title": "告警Webhook", "required": True}
                    }
                }
            ),
            "script": TemplateScriptCreate(
                template_id="website-monitor",
                script_type="python",
                script_content="""#!/usr/bin/env python3
import requests
import json
import sys
from datetime import datetime

config = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
url = config.get("url")
timeout = config.get("timeout", 10)
expected = config.get("expected_status", 200)
webhook = config.get("webhook_url")

try:
    start = datetime.now()
    r = requests.get(url, timeout=timeout, allow_redirects=True)
    elapsed = (datetime.now() - start).total_seconds() * 1000
    if r.status_code == expected:
        print(f"OK: {url} status={r.status_code} time={elapsed:.0f}ms")
    else:
        msg = f"⚠️ 网站异常: {url}\\n状态码: {r.status_code} (期望: {expected})\\n响应时间: {elapsed:.0f}ms"
        print(msg)
        if webhook:
            requests.post(webhook, json={"content": msg}, timeout=5)
except Exception as e:
    msg = f"❌ 网站不可达: {url}\\n错误: {str(e)}"
    print(msg)
    if webhook:
        requests.post(webhook, json={"content": msg}, timeout=5)
"""
            ),
            "cron_suggestions": [
                TemplateCronSuggestionCreate(
                    template_id="website-monitor",
                    label="每5分钟检查一次",
                    cron_value="*/5 * * * *",
                    is_default=True,
                    sort_order=1
                ),
                TemplateCronSuggestionCreate(
                    template_id="website-monitor",
                    label="每2分钟检查一次",
                    cron_value="*/2 * * * *",
                    sort_order=2
                )
            ]
        }
    ]
