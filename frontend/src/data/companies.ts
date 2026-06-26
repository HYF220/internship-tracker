export interface Company {
  name: string;
  category: string;
  url: string;
  description: string;
}

export const COMPANIES: Company[] = [
  // 互联网大厂
  {
    name: "字节跳动",
    category: "互联网",
    url: "https://jobs.bytedance.com/campus/",
    description: "抖音、TikTok 母公司，技术氛围浓厚，薪资竞争力强",
  },
  {
    name: "阿里巴巴",
    category: "互联网",
    url: "https://talent.alibaba.com/campus/",
    description: "电商、云计算、AI 多业务线，技术栈丰富",
  },
  {
    name: "腾讯",
    category: "互联网",
    url: "https://join.qq.com/",
    description: "微信、QQ、游戏，产品+技术双驱动",
  },
  {
    name: "百度",
    category: "互联网",
    url: "https://talent.baidu.com/",
    description: "AI 和自动驾驶领先，技术底蕴深厚",
  },
  {
    name: "美团",
    category: "互联网",
    url: "https://zhaopin.meituan.com/campus",
    description: "本地生活赛道龙头，业务增长快",
  },
  {
    name: "京东",
    category: "互联网",
    url: "https://campus.jd.com/",
    description: "电商+物流+科技，供应链技术强",
  },
  {
    name: "拼多多",
    category: "互联网",
    url: "https://careers.pinduoduo.com/campus",
    description: "电商新贵，薪资在行业中极具竞争力",
  },
  {
    name: "小红书",
    category: "互联网",
    url: "https://job.xiaohongshu.com/campus",
    description: "内容社区，技术+产品驱动型公司",
  },
  {
    name: "哔哩哔哩",
    category: "互联网",
    url: "https://jobs.bilibili.com/campus/",
    description: "年轻人社区，视频技术栈有特色",
  },
  {
    name: "网易",
    category: "互联网",
    url: "https://campus.163.com/",
    description: "游戏+音乐+教育，技术业务双修",
  },
  {
    name: "快手",
    category: "互联网",
    url: "https://zhaopin.kuaishou.cn/",
    description: "短视频赛道，AI 推荐系统技术强",
  },
  {
    name: "滴滴",
    category: "互联网",
    url: "https://talent.didiglobal.com/campus",
    description: "出行平台，算法+工程能力要求高",
  },

  // 硬件/半导体
  {
    name: "华为",
    category: "硬件/通信",
    url: "https://career.huawei.com/",
    description: "通信+终端+芯片，技术硬核，薪资顶级",
  },
  {
    name: "小米",
    category: "硬件/通信",
    url: "https://hr.xiaomi.com/campus",
    description: "手机+IoT+汽车，硬件软件全覆盖",
  },
  {
    name: "大疆",
    category: "硬件/通信",
    url: "https://we.dji.com/cn/",
    description: "无人机全球第一，机器人+AI 方向",
  },
  {
    name: "海康威视",
    category: "硬件/通信",
    url: "https://campushr.hikvision.com/",
    description: "安防 AI 视觉领域龙头",
  },
  {
    name: "英伟达",
    category: "硬件/通信",
    url: "https://www.nvidia.com/zh-cn/about-nvidia/careers/university-recruiting/",
    description: "GPU 和 AI 芯片巨头，薪资优厚",
  },

  // 外企
  {
    name: "微软",
    category: "外企",
    url: "https://careers.microsoft.com/students/",
    description: "WLB 好，技术氛围佳，国际化平台",
  },
  {
    name: "Google",
    category: "外企",
    url: "https://careers.google.com/students/",
    description: "全球顶级技术公司，工程文化卓越",
  },
  {
    name: "Apple",
    category: "外企",
    url: "https://www.apple.com/careers/cn/",
    description: "硬件+软件+芯片，供应链全球化",
  },
  {
    name: "Amazon",
    category: "外企",
    url: "https://www.amazon.jobs/zh/teams/student-programs",
    description: "电商+云计算（AWS），全球业务",
  },

  // 金融科技
  {
    name: "蚂蚁集团",
    category: "金融科技",
    url: "https://talent.antgroup.com/campus",
    description: "支付宝母公司，金融科技全球领先",
  },
  {
    name: "微众银行",
    category: "金融科技",
    url: "https://hr.webank.com/",
    description: "互联网银行先驱，技术驱动金融",
  },

  // AI/新锐
  {
    name: "商汤科技",
    category: "AI/新锐",
    url: "https://www.sensetime.com/cn/careers/",
    description: "AI 四小龙，计算机视觉方向",
  },
  {
    name: "旷视科技",
    category: "AI/新锐",
    url: "https://www.megvii.com/careers/",
    description: "AI 视觉+机器人，技术前沿",
  },
  {
    name: "DeepSeek",
    category: "AI/新锐",
    url: "https://www.deepseek.com/careers",
    description: "大模型新锐，AGI 方向研发",
  },
  {
    name: "智谱 AI",
    category: "AI/新锐",
    url: "https://www.zhipuai.cn/careers",
    description: "清华系大模型公司，GLM 系列",
  },
  {
    name: "月之暗面",
    category: "AI/新锐",
    url: "https://www.moonshot.cn/join",
    description: "Kimi 母公司，大模型应用方向",
  },

  // 游戏
  {
    name: "米哈游",
    category: "游戏",
    url: "https://campus.mihoyo.com/",
    description: "原神、崩坏系列，游戏技术天花板",
  },
  {
    name: "莉莉丝",
    category: "游戏",
    url: "https://www.lilith.com/cn/careers/campus",
    description: "全球化游戏公司，技术+创意",
  },
];
