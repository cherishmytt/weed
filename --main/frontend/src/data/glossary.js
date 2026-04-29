export const GLOSSARY_GROUPS = [
  {
    id: 'data',
    title: '数据术语',
    description: '用于解释数据来源、字段含义和监测记录的基础结构。',
    items: [
      {
        term: 'FIRMS',
        aliases: ['NASA FIRMS'],
        keywords: ['火点数据', '数据源', '监测'],
        summary:
          'FIRMS 是 NASA 提供的火点与热异常监测服务，本系统的火点记录主要来源于这一类标准化遥感产品。',
        details: [
          '在本系统里，FIRMS 数据经过字段整理、时间补全、区域标注和多源合并后，再进入数据库。',
          '用户看到的火点点位、趋势图和热点区域，都是围绕这套火点记录展开统计和展示。',
        ],
      },
      {
        term: 'Active Fire / Hotspot',
        aliases: ['火点', '热异常'],
        keywords: ['火点', '热点', '点位'],
        summary:
          'Active Fire 或 Hotspot 指遥感卫星识别出的高温异常像元，通常代表野火、秸秆焚烧或其他热源活动。',
        details: [
          '本系统中的火点并不等同于已经核实的火灾灾情，它更接近遥感监测发现的疑似热异常位置。',
          '在地图页中，每个火点都有时间、位置、FRP、昼夜属性和来源信息。',
        ],
      },
      {
        term: 'NRT',
        aliases: ['Near Real Time'],
        keywords: ['近实时', '时效'],
        summary:
          'NRT 表示近实时数据，强调尽快提供监测结果，适合做动态监控、趋势观察和快速展示。',
        details: [
          '近实时数据更新快，但在后续版本中可能还会有补充和校正，因此更适合监测和研判，不完全等同于最终定稿数据。',
        ],
      },
      {
        term: 'VIIRS',
        aliases: ['Visible Infrared Imaging Radiometer Suite'],
        keywords: ['传感器', '卫星载荷'],
        summary:
          'VIIRS 是常见的热异常监测传感器，具备较好的空间分辨率和全球覆盖能力，是当前系统的主要火点来源。',
        details: [
          '系统里的 NOAA-20 和 S-NPP 数据，都属于 VIIRS 系列产品，只是搭载平台不同。',
        ],
      },
      {
        term: 'MODIS',
        aliases: [],
        keywords: ['未来扩展', '传感器'],
        summary:
          'MODIS 也是常见的火点监测来源，目前本系统尚未作为主数据源接入，但后续扩展时会和 VIIRS 一样纳入统一筛选框架。',
        details: [
          '页面里的数据源切换和术语设计已经为后续增加 MODIS 预留了扩展空间。',
        ],
      },
      {
        term: 'NOAA-20',
        aliases: ['JPSS-1'],
        keywords: ['数据源', '卫星平台'],
        summary:
          'NOAA-20 是当前系统支持的一套主要火点来源平台，对应的数据源标识通常为 VIIRS_NOAA20_NRT。',
        details: [
          '在本系统里，它可以单独筛选，也可以与 S-NPP 合并查看，用于对比不同来源下的火点分布和趋势。',
        ],
      },
      {
        term: 'S-NPP',
        aliases: ['Suomi NPP'],
        keywords: ['数据源', '卫星平台'],
        summary:
          'S-NPP 是另一套常用的 VIIRS 火点来源平台，在系统中通常以 VIIRS_SNPP_NRT 表示。',
        details: [
          '与 NOAA-20 一样，S-NPP 可以独立查询，也可以参与联合统计。',
        ],
      },
      {
        term: 'FRP',
        aliases: ['Fire Radiative Power'],
        keywords: ['辐射功率', '火强度'],
        summary:
          'FRP 表示火辐射功率，通常可用来反映火点热释放强度，是系统中衡量活跃程度的重要字段。',
        details: [
          'FRP 数值越高，往往意味着热异常更强。地图上的点位样式和图表中的分布统计，都可以基于 FRP 做映射。',
          '它适合用于强弱对比，但不应直接等同为实际过火面积或灾损等级。',
        ],
      },
      {
        term: 'confidence',
        aliases: ['置信度'],
        keywords: ['可信度', '高低置信度'],
        summary:
          'confidence 表示火点记录的置信程度，用于区分高、中、低不同可信等级。',
        details: [
          '在系统里，高置信度火点通常会被单独统计，也常作为筛选条件帮助用户快速聚焦更可靠的火点记录。',
        ],
      },
      {
        term: 'daynight',
        aliases: ['昼夜属性'],
        keywords: ['白天', '夜间'],
        summary:
          'daynight 用于表示火点记录是在白天还是夜间被观测到，通常使用 D 和 N 这样的简写值。',
        details: [
          '昼夜属性会直接影响图表结构分析，也常用于观察夜间活跃区域和持续燃烧特征。',
        ],
      },
      {
        term: 'acq_date',
        aliases: [],
        keywords: ['采集日期', '日期'],
        summary:
          'acq_date 表示火点记录对应的采集日期，是进行按天统计和日期范围查询的基础字段。',
        details: [
          '系统的趋势图、快捷时间筛选和分析页日期联动，都会用到这个字段。',
        ],
      },
      {
        term: 'acq_time',
        aliases: [],
        keywords: ['采集时间', '原始时间'],
        summary:
          'acq_time 表示原始记录中的采集时间，通常以数值形式存储，需要补零和拼接后才能更稳定地参与时间分析。',
        details: [
          '系统在导入阶段会把它标准化，并进一步生成可直接查询的完整时间字段。',
        ],
      },
      {
        term: 'acq_datetime',
        aliases: ['采集时间戳'],
        keywords: ['时间主字段', '时间轴'],
        summary:
          'acq_datetime 是本系统统一使用的时间主字段，便于多天回放、趋势统计、时间范围筛选和自动播放。',
        details: [
          '相比单独使用日期和时间，本字段更适合做多天数据查询和时间轴联动，是当前系统最核心的时间条件。',
        ],
      },
      {
        term: 'source_product',
        aliases: ['数据源标识'],
        keywords: ['NOAA-20', 'S-NPP', '数据源切换'],
        summary:
          'source_product 用于区分火点数据来自哪一套产品，例如 VIIRS_NOAA20_NRT 或 VIIRS_SNPP_NRT。',
        details: [
          '在系统中，数据源筛选、数据源占比饼图以及联合统计，都是围绕这个字段展开的。',
        ],
      },
      {
        term: 'area_label',
        aliases: ['区域标签'],
        keywords: ['world', 'seasia', 'australia', 'south_america'],
        summary:
          'area_label 是本系统自定义补充的区域标签，用来标记一条火点记录属于哪个数据范围或展示区域。',
        details: [
          '它不是 FIRMS 原始字段，而是为了支持区域切换、分区分析和多套 merged CSV 联动而加入的。',
          '目前系统已支持 world、seasia、australia、south_america，后续也可以继续扩展新的区域标签。',
        ],
      },
    ],
  },
  {
    id: 'mapping',
    title: '地图与分析术语',
    description: '用于解释地图展示、空间筛选和分析交互里常见的概念。',
    items: [
      {
        term: 'bbox',
        aliases: ['Bounding Box', '范围框'],
        keywords: ['空间范围', '经纬度框'],
        summary:
          'bbox 表示经纬度矩形范围，通常用最小经度、最小纬度、最大经度、最大纬度来描述一个空间查询框。',
        details: [
          '在地图场景中，bbox 适合用于快速截取某个区域的火点记录或做局部分析。',
        ],
      },
      {
        term: '时间轴回放',
        aliases: ['时间播放', '回放'],
        keywords: ['按天播放', '变化过程'],
        summary:
          '时间轴回放是指按时间顺序逐步展示火点变化过程，让用户观察不同日期或时段的火点分布变化。',
        details: [
          '在本系统里，它主要基于 acq_datetime 做按天播放，适合用于展示区域活跃过程和多天变化趋势。',
        ],
      },
      {
        term: '热点区域',
        aliases: ['Hotspot Cluster'],
        keywords: ['聚合', '高密度区域'],
        summary:
          '热点区域是系统根据火点密度自动聚合出来的高活跃区域，用于从离散点位中识别更具代表性的空间热点。',
        details: [
          '热点区域通常会给出中心点、火点数量、平均 FRP、最大 FRP、主要国家和时间范围等信息。',
        ],
      },
      {
        term: '国家着色图',
        aliases: ['专题图', 'Choropleth'],
        keywords: ['国家统计', '颜色分级'],
        summary:
          '国家着色图是按国家统计结果进行颜色分级展示的地图形式，便于快速识别火点密集国家。',
        details: [
          '在本系统里，国家着色图通常基于火点总数或平均 FRP 做分级，是时空分析页的重要概览视图。',
        ],
      },
      {
        term: '数据源切换',
        aliases: [],
        keywords: ['NOAA-20', 'S-NPP', '联合分析'],
        summary:
          '数据源切换是指在不同卫星来源之间进行筛选和对比，用于区分某一套来源的数据表现。',
        details: [
          '用户可以只看 NOAA-20、只看 S-NPP，也可以选择全部做联合统计。',
        ],
      },
      {
        term: '区域筛选',
        aliases: [],
        keywords: ['区域切换', 'world', 'seasia'],
        summary:
          '区域筛选用于在全球、东南亚、澳大利亚、南美等不同数据范围之间切换，帮助用户聚焦特定区域。',
        details: [
          '切换区域后，地图视角、分析图表和热点列表都应随之联动刷新。',
        ],
      },
    ],
  },
  {
    id: 'system',
    title: '系统功能术语',
    description: '用于解释系统页面、功能模块和展示方式的含义。',
    items: [
      {
        term: '数据同步',
        aliases: ['数据导入'],
        keywords: ['CSV 导入', '批次记录'],
        summary:
          '数据同步是指把新的 CSV 文件导入系统数据库，并写入批次记录、来源信息和查询字段的过程。',
        details: [
          '同步完成后，新数据会参与地图展示、图表统计和热点计算。',
        ],
      },
      {
        term: '自动巡航',
        aliases: [],
        keywords: ['相机飞行', '热点切换'],
        summary:
          '自动巡航是大屏中的自动展示能力，系统会在多个热点区域之间平滑飞行切换，用于无人值守或录屏演示。',
        details: [
          '它通常会结合热点排行、区域信息和趋势内容，让展示更有节奏。',
        ],
      },
      {
        term: '演示模式',
        aliases: [],
        keywords: ['自动播放', '录屏展示'],
        summary:
          '演示模式是更偏展示导向的自动播放方案，会结合时间轴、热点切换和大屏内容轮播，让系统更适合现场演示或录屏。',
        details: [
          '它强调的是观感和节奏，不完全等同于日常分析操作界面。',
        ],
      },
      {
        term: '数据大屏',
        aliases: ['驾驶舱', 'Screen'],
        keywords: ['展示', '总览'],
        summary:
          '数据大屏是偏展示和总览的全屏页面，强调沉浸感、节奏感和核心信息快速识别。',
        details: [
          '它通常聚焦地图、核心指标、热点排行和趋势图，不适合承载过多细碎操作。',
        ],
      },
      {
        term: '时空分析',
        aliases: [],
        keywords: ['统计分析', '空间分析'],
        summary:
          '时空分析是系统中用来做时间趋势、区域统计和国家专题分析的页面，偏分析和研判使用。',
        details: [
          '相比大屏，它更强调筛选联动和图表阅读；相比后台表格，它又更重视可视化表达。',
        ],
      },
    ],
  },
]

export const flattenGlossaryTerms = () =>
  GLOSSARY_GROUPS.flatMap((group) =>
    group.items.map((item) => ({
      ...item,
      groupId: group.id,
      groupTitle: group.title,
      searchText: [
        group.title,
        item.term,
        ...(item.aliases || []),
        ...(item.keywords || []),
        item.summary,
        ...(item.details || []),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase(),
    })),
  )
