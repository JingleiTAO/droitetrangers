from langchain_core.tools import tool
from datetime import datetime

class LegalKnowledgeTool:
    @tool("search_legal_info")
    def search_legal_info(topic: str):
        """
        当用户询问具体的法国法律条款、签证类型要求或居留卡办理流程时，使用此工具。
        """
        # 实际开发时，这里应该对接你的数据库或 PDF 检索系统
        # 现在我们可以先做一个简单的 Mock 逻辑
        knowledge_base = {
                "passeport talent": (
                "【Passeport Talent (优秀人才居留)】\n"
                "- 有效期：最多 4 年。\n"
                "- 核心要求：针对高素质员工（Salarié qualifié）、企业创建者或投资者。\n"
                "- 薪资门槛：通常要求年薪至少达到 1.5 倍 SMIC（目前约为 32,400€+ 每年，视具体子类别而定）。\n"
                "- 优势：无需申请工作许可（Autorisation de travail），家属可随行。"
            ),
            "aps": (
                "【APS / RECE (找工作或创业居留)】\n"
                "- 对象：在法国获得硕士（Master）或以上学位的毕业生。\n"
                "- 有效期：通常为 12 个月，不可续签。\n"
                "- 权利：允许在法国全职工作或寻找工作。一旦找到符合标准的 CDD/CDI，需申请转身份。"
            ),
            "salarie": (
                "【Salarié / Travailleur temporaire (普通工签)】\n"
                "- 有效期：通常为 1 年（续签后可获得多年卡）。\n"
                "- 核心要求：需要雇主申请【工作许可 (Autorisation de travail)】。\n"
                "- 续签提醒：建议在现有居留过期前 2 个月（2 mois avant l'expiration）预约提交申请。"
            ),
            "etudiant": (
                "【Étudiant (学生居留)】\n"
                "- 权利：允许每年合法打工 964 小时（约 60% 的全职工作量）。\n"
                "- 续签：需证明学习进度（学分、出勤率）及经济来源（每月约 615€）。"
            ),
            "algerien": (
                "【Certificat de résidence pour Algérien (阿尔及利亚籍特殊规定)】\n"
                "- 依据：1968 年法阿协议（Accord franco-algérien）。\n"
                "- 类别：分为 1 年期和 10 年期证件，申请条件与常规 CESEDA 法典有所不同。"
            )
        }
        
        # 简单的模糊匹配
        for key, value in knowledge_base.items():
            if key in topic.lower():
                return value
        return "抱歉，目前数据库中未查询到该具体条文，建议咨询 service-public.fr。"

