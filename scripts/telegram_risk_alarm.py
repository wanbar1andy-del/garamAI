import os
import sys
import json
import requests
import logging
from pathlib import Path

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelegramRiskAlarm")

class TelegramRiskAlarm:
    def __init__(self, token=None, chat_id=None):
        self.token = token or os.environ.get("GARAM_TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("GARAM_TELEGRAM_CHAT_ID")
        
        # Fallback to config file if env vars missing
        if not self.token or not self.chat_id:
            config_path = Path("config/telegram_secrets.json")
            if config_path.exists():
                try:
                    cfg = json.loads(config_path.read_text(encoding='utf-8'))
                    self.token = self.token or cfg.get("bot_token")
                    self.chat_id = self.chat_id or cfg.get("chat_id")
                except Exception as e:
                    logger.warning(f"Failed to load secrets: {e}")

        if not self.token or not self.chat_id:
            logger.error("Telegram Token/ChatID missing!")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Telegram Risk Alarm Enabled.")

    def send_message(self, text, parse_mode="Markdown"):
        if not self.enabled: return False
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            resp = requests.post(url, json={"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode}, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Send Msg Error: {e}")
            return False

    def send_photo(self, photo_path, caption=None):
        if not self.enabled: return False
        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        try:
            with open(photo_path, "rb") as f:
                resp = requests.post(
                    url, 
                    data={"chat_id": self.chat_id, "caption": caption, "parse_mode": "Markdown"},
                    files={"photo": f},
                    timeout=20
                )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Send Photo Error: {e}")
            return False

    def broadcast_risk_report(self):
        """
        Sends EdgeMap Summary and Guard Params
        """
        # 1. Load Guard Params
        guard_path = Path("guard_param_recommended.json")
        if guard_path.exists():
            guard = json.loads(guard_path.read_text(encoding='utf-8'))
            msg = (
                "🛡 *GARAM 가드(Guard) 업데이트*\n\n"
                f"• 최소 기대값(Edge): `{guard.get('guard_min_threshold',0):.6f}`\n"
                f"• 크래시 방어(MDD): `{guard.get('crash_mdd',0):.2f}`\n"
                f"• 최대 매매횟수(TPD): `{guard.get('overtrade_trades_per_day',0):.1f}`\n"
                f"• 레짐 변동성(Spread): `{guard.get('regime_spread_exp_net',0):.5f}`\n\n"
                "ℹ️ 400종목 EdgeMap 분석 기반 갱신됨."
            )
            self.send_message(msg)
        else:
            self.send_message("⚠️ *가드 파라미터 누락!* 파이프라인을 점검하세요.")

        # 2. Send Visualizations
        viz_map = {
            "results/viz_regime/net_expectancy_dist.png": "📊 *레짐별 기대값 분포*",
            "results/viz_regime/cost_vs_net_by_regime.png": "📉 *비용 대 기대값 (Cost vs Edge)*",
            "results/edge_map_expectancy_dist.png": "🌍 *전체 엣지 분포 (Overall)*"
        }

        for path_str, caption in viz_map.items():
            p = Path(path_str)
            if p.exists():
                self.send_photo(p, caption)
            else:
                logger.warning(f"Image not found: {p}")

        logger.info("Risk Report Broadcast Complete.")

if __name__ == "__main__":
    alarm = TelegramRiskAlarm()
    if alarm.enabled:
        alarm.broadcast_risk_report()
    else:
        print("Telegram not configured. Set ENV vars or config/telegram_secrets.json")
