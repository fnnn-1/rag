import json
from pathlib import Path

items = [
  {"id":"handbook-01","category":"员工手册","question":"新员工的标准试用期是多久？","answerable":True,"expected_documents":["01_employee_handbook.md"],"expected_terms":["3个月"]},
  {"id":"handbook-02","category":"员工手册","question":"转正总结最晚应在试用期结束前多久提交？","answerable":True,"expected_documents":["01_employee_handbook.md"],"expected_terms":["10个工作日"]},
  {"id":"handbook-03","category":"员工手册","question":"发现疑似数据泄露后需要多长时间内报告？","answerable":True,"expected_documents":["01_employee_handbook.md"],"expected_terms":["30分钟"]},
  {"id":"handbook-04","category":"员工手册","question":"公司电脑和门禁卡最晚什么时候归还？","answerable":True,"expected_documents":["01_employee_handbook.md"],"expected_terms":["最后工作日","18:00"]},
  {"id":"attendance-01","category":"考勤","question":"公司的标准工作时间是什么？","answerable":True,"expected_documents":["02_attendance_policy.md"],"expected_terms":["09:00","18:00"]},
  {"id":"attendance-02","category":"考勤","question":"几点以后打卡会被记为迟到？","answerable":True,"expected_documents":["02_attendance_policy.md"],"expected_terms":["09:10"]},
  {"id":"attendance-03","category":"考勤","question":"每月迟到多少次需要主管进行考勤沟通？","answerable":True,"expected_documents":["02_attendance_policy.md"],"expected_terms":["3次"]},
  {"id":"attendance-04","category":"考勤","question":"漏打卡后应在几个工作日内提交补卡申请？","answerable":True,"expected_documents":["02_attendance_policy.md"],"expected_terms":["2个工作日"]},
  {"id":"leave-01","category":"休假","question":"工作满1年但不满10年的员工有多少天年假？","answerable":True,"expected_documents":["03_leave_policy.md"],"expected_terms":["5天"]},
  {"id":"leave-02","category":"休假","question":"连续休假超过3个工作日需要提前多久申请？","answerable":True,"expected_documents":["03_leave_policy.md"],"expected_terms":["7个工作日"]},
  {"id":"leave-03","category":"休假","question":"病假超过多久需要提供医疗机构证明？","answerable":True,"expected_documents":["03_leave_policy.md"],"expected_terms":["1个工作日"]},
  {"id":"leave-04","category":"休假","question":"突发病假无法提前申请时，当天几点前要通知主管？","answerable":True,"expected_documents":["03_leave_policy.md"],"expected_terms":["10:00"]},
  {"id":"expense-01","category":"报销","question":"费用发生后多少天内应提交报销？","answerable":True,"expected_documents":["04_expense_policy.md"],"expected_terms":["30个自然日"]},
  {"id":"expense-02","category":"报销","question":"上月费用集中报销的截止时间是什么？","answerable":True,"expected_documents":["04_expense_policy.md"],"expected_terms":["第5个工作日"]},
  {"id":"expense-03","category":"报销","question":"单笔费用超过2000元时还需要提供哪些材料？","answerable":True,"expected_documents":["04_expense_policy.md"],"expected_terms":["合同","订单","事前审批"]},
  {"id":"expense-04","category":"报销","question":"哪些费用明确不予报销？","answerable":True,"expected_documents":["04_expense_policy.md"],"expected_terms":["个人消费","交通违章罚款"]},
  {"id":"travel-01","category":"差旅","question":"国内出差乘高铁原则上可以买什么座位？","answerable":True,"expected_documents":["05_travel_policy.md"],"expected_terms":["二等座"]},
  {"id":"travel-02","category":"差旅","question":"上海出差的住宿标准上限是多少？","answerable":True,"expected_documents":["05_travel_policy.md"],"expected_terms":["600元"]},
  {"id":"travel-03","category":"差旅","question":"其他省会城市每晚住宿上限是多少？","answerable":True,"expected_documents":["05_travel_policy.md"],"expected_terms":["450元"]},
  {"id":"travel-04","category":"差旅","question":"国内出差每天的餐费补助是多少？","answerable":True,"expected_documents":["05_travel_policy.md"],"expected_terms":["100元"]},
  {"id":"procurement-01","category":"采购","question":"采购金额不超过5000元由谁审批？","answerable":True,"expected_documents":["06_procurement_policy.md"],"expected_terms":["部门负责人"]},
  {"id":"procurement-02","category":"采购","question":"采购金额在5000元到50000元之间需要几家供应商报价？","answerable":True,"expected_documents":["06_procurement_policy.md"],"expected_terms":["3家供应商"]},
  {"id":"procurement-03","category":"采购","question":"超过50000元的采购需要履行什么程序？","answerable":True,"expected_documents":["06_procurement_policy.md"],"expected_terms":["正式招标","财务负责人","总经理"]},
  {"id":"procurement-04","category":"采购","question":"紧急采购应在多久内补齐申请和审批记录？","answerable":True,"expected_documents":["06_procurement_policy.md"],"expected_terms":["2个工作日"]},
  {"id":"unknown-01","category":"知识库外","question":"公司2026年的股票价格是多少？","answerable":False,"expected_documents":[],"expected_terms":[]},
  {"id":"unknown-02","category":"知识库外","question":"公司创始人的出生日期是什么？","answerable":False,"expected_documents":[],"expected_terms":[]},
  {"id":"unknown-03","category":"知识库外","question":"公司食堂今天午餐菜单是什么？","answerable":False,"expected_documents":[],"expected_terms":[]},
  {"id":"unknown-04","category":"知识库外","question":"下周上海的天气怎么样？","answerable":False,"expected_documents":[],"expected_terms":[]},
  {"id":"unknown-05","category":"知识库外","question":"公司的年度营收目标是多少亿元？","answerable":False,"expected_documents":[],"expected_terms":[]},
  {"id":"unknown-06","category":"知识库外","question":"员工可以免费领取几台手机？","answerable":False,"expected_documents":[],"expected_terms":[]}
]

payload = {
    "name": "企业制度知识库评测集",
    "version": "1.0.0",
    "created_date": "2026-08-30",
    "description": "基于虚构脱敏企业制度文档构建的检索、引用和拒答评测集。",
    "items": items,
}
workspace = Path(__file__).resolve().parents[1]
path = workspace / "data" / "evaluation" / "eval_dataset.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Created {len(items)} evaluation items at {path}")
