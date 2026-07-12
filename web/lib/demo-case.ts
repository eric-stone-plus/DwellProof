export type EvidenceStatus =
  | "verified"
  | "user_input"
  | "missing"
  | "stale"
  | "conflict"
  | "not_applicable";

export type WorkspaceId =
  | "overview"
  | "evidence"
  | "valuation"
  | "finance"
  | "risks"
  | "memo";

export type EvidenceGate = {
  id: string;
  code: string;
  title: string;
  shortTitle: string;
  status: EvidenceStatus;
  requirement: string;
  reason: string;
  deadline: string;
  owner: string;
  accepted: string[];
};

export type OfficialSource = {
  id: string;
  title: string;
  authority: string;
  observed: string;
  checked: string;
  boundary: string;
  url: string;
};

export const workspaces: Array<{
  id: WorkspaceId;
  label: string;
  shortLabel: string;
  description: string;
}> = [
  { id: "overview", label: "案例概览", shortLabel: "概览", description: "结论门槛与下一步" },
  { id: "evidence", label: "证据室", shortLabel: "证据", description: "七项交易准入检查" },
  { id: "valuation", label: "可比估值", shortLabel: "估值", description: "成交样本与调整" },
  { id: "finance", label: "成本与融资", shortLabel: "模型", description: "税费、贷款与现金流" },
  { id: "risks", label: "风险与交割", shortLabel: "风险", description: "按交易节点化解" },
  { id: "memo", label: "决策备忘录", shortLabel: "备忘录", description: "可审计输出与修订" },
];

export const evidenceGates: EvidenceGate[] = [
  {
    id: "title",
    code: "G01",
    title: "产权人与处分权",
    shortTitle: "产权与处分权",
    status: "missing",
    requirement: "确认登记权利人、共有人、婚姻财产关系及完整处分授权。",
    reason: "没有权利人与处分授权证据，无法判断签约主体是否有权出售。",
    deadline: "支付定金前",
    owner: "买方 / 律师",
    accepted: ["最新不动产登记信息", "身份证明与婚姻状态材料", "共有人书面同意或授权"],
  },
  {
    id: "encumbrance",
    code: "G02",
    title: "抵押、查封、异议与居住权",
    shortTitle: "权利负担",
    status: "missing",
    requirement: "取得足以覆盖抵押、查封、异议登记和居住权的当日登记状态。",
    reason: "旧查档不能证明签约或付款当日仍可安全过户。",
    deadline: "定金前首次查验，付款前复验",
    owner: "买方 / 经办机构",
    accepted: ["当日查档结果", "抵押余额及解押安排", "查封或异议解除证明"],
  },
  {
    id: "property_nature",
    code: "G03",
    title: "房屋性质与交易限制",
    shortTitle: "房屋性质",
    status: "missing",
    requirement: "核对土地用途、权利性质、使用年限及当地限售或资格限制。",
    reason: "不同性质会改变能否交易、税费、融资与退出条件。",
    deadline: "签约前",
    owner: "买方 / 登记与住建部门",
    accepted: ["不动产权证完整页", "当地交易资格结果", "限制或补缴规则的官方依据"],
  },
  {
    id: "occupancy",
    code: "G04",
    title: "租赁、户口与学位占用",
    shortTitle: "占用与交付",
    status: "missing",
    requirement: "确认租赁、实际占用、户口迁出、学位使用及交付条件。",
    reason: "占用关系可能影响交付、使用价值和交易后的实际控制。",
    deadline: "签约前写入合同",
    owner: "买方 / 卖方",
    accepted: ["租赁合同及承租人确认", "现场占用核验", "户口与学位状态材料"],
  },
  {
    id: "tax",
    code: "G05",
    title: "地方税费与计税基础",
    shortTitle: "税费口径",
    status: "missing",
    requirement: "用当地、当期、与交易双方情况匹配的规则确定全部税费和费用。",
    reason: "当前只确认全国优惠契税规则，尚不能确定本标的实际税负。",
    deadline: "签约前",
    owner: "买卖双方 / 当地税务窗口",
    accepted: ["当地税务书面或系统测算", "家庭住房套数证明", "持有年限和计税价格材料"],
  },
  {
    id: "loan",
    code: "G06",
    title: "银行书面贷款报价",
    shortTitle: "贷款执行条件",
    status: "missing",
    requirement: "取得与借款人、期限、首付和还款方式匹配的书面执行利率。",
    reason: "LPR 只是市场基准，不能代替银行对本借款人的实际报价。",
    deadline: "签约或贷款条款生效前",
    owner: "借款人 / 贷款银行",
    accepted: ["银行预审批或书面报价", "执行利率及有效期", "首付比例、期限和还款方式"],
  },
  {
    id: "comparables",
    code: "G07",
    title: "同小区可比成交",
    shortTitle: "可比成交",
    status: "missing",
    requirement: "至少取得 3 笔近期、可归属、口径清晰且可解释调整的成交样本。",
    reason: "城市指数不能替代单套房估值，挂牌价也不能视为真实成交价。",
    deadline: "形成价格意见前",
    owner: "买方 / 数据提供方",
    accepted: ["同小区近期真实成交", "面积、楼层、朝向和装修口径", "来源、日期与纳入排除理由"],
  },
];

export const officialSources: OfficialSource[] = [
  {
    id: "deed-tax",
    title: "全国住房交易契税优惠规则",
    authority: "财政部 / 税务总局 / 住建部",
    observed: "2024-12-01 起施行",
    checked: "本地快照核验 2026-07-12",
    boundary: "只证明全国优惠规则，不证明本交易适用税率或地方费用。",
    url: "https://guangdong.chinatax.gov.cn/gdsw/zjfg/2024-11/14/content_0289c52475614b0c9d89145c43310721.shtml",
  },
  {
    id: "nbs-index",
    title: "2026-04 二手住宅价格指数",
    authority: "国家统计局 · 五城选定行逐项匹配",
    observed: "观察期 2026-04",
    checked: "本地快照核验 2026-07-12",
    boundary: "只作城市市场背景，不参与单套房估值。",
    url: "https://www.stats.gov.cn/sj/zxfb/202605/t20260518_1963715.html",
  },
  {
    id: "lpr",
    title: "五年期以上 LPR",
    authority: "中国人民银行",
    observed: "2026-06-22 公告 · 3.5%",
    checked: "本地快照核验 2026-07-12",
    boundary: "仅为定价基准，不是借款人的银行执行利率。",
    url: "https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125440/3876551/2026062208495122562/index.html",
  },
];

export const caseFacts = [
  { label: "案例代号", value: "GZ-DEMO-001", status: "user_input" as const },
  { label: "城市 / 区域", value: "广州 / 天河", status: "user_input" as const },
  { label: "建筑面积", value: "89 m2", status: "user_input" as const },
  { label: "演示要约", value: "520 万元", status: "user_input" as const },
  { label: "计划持有", value: "5 年", status: "user_input" as const },
  { label: "基准日", value: "2026-07-12", status: "user_input" as const },
];

export const scenarioRows = [
  { name: "保守", price: "-5.0% / 年", vacancy: "3 个月", exit: "9 个月" },
  { name: "基准", price: "0.0% / 年", vacancy: "1 个月", exit: "6 个月" },
  { name: "乐观", price: "+3.0% / 年", vacancy: "1 个月", exit: "3 个月" },
];
